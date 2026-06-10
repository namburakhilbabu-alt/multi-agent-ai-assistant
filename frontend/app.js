// Maestro frontend: sends a message, reads the NDJSON event stream, and renders
// the orchestrator's routing + each agent's tool calls live as a trace.

const chat = document.getElementById("chat");
const form = document.getElementById("composer");
const input = document.getElementById("input");
const sendBtn = document.getElementById("send");

const EXAMPLES = [
  "What's the weather in Tokyo right now?",
  "Convert 5 miles to kilometers, then divide by 3.",
  "What agents does Maestro have?",
  "Summarize this in one sentence: <paste text>",
];

const NODE = {
  orch: { cls: "orch", icon: "◆" },
  route: { cls: "route", icon: "→" },
  tool: { cls: "tool", icon: "⚙" },
  done: { cls: "done", icon: "✓" },
};

// ---------- bootstrap: roster, examples, health ----------
async function init() {
  try {
    const { agents } = await (await fetch("/api/agents")).json();
    document.getElementById("roster").innerHTML = agents
      .map(
        (a) => `<div class="agent-chip" data-agent="${a.name}">
          <div class="name">${a.name}</div>
          <div class="desc">${a.description}</div></div>`
      )
      .join("");
  } catch (_) {}

  document.getElementById("examples").innerHTML = EXAMPLES.map(
    (e) => `<button class="example">${e}</button>`
  ).join("");
  document.querySelectorAll(".example").forEach((el) =>
    el.addEventListener("click", () => {
      input.value = el.textContent;
      input.focus();
    })
  );

  const dot = document.getElementById("status-dot");
  const txt = document.getElementById("status-text");
  try {
    const h = await (await fetch("/api/health")).json();
    dot.className = "dot " + (h.ok ? "ok" : "bad");
    txt.textContent = h.ok ? `${h.model} · online` : "model offline";
  } catch (_) {
    dot.className = "dot bad";
    txt.textContent = "backend unreachable";
  }
}

// ---------- rendering helpers ----------
function el(html) {
  const t = document.createElement("template");
  t.innerHTML = html.trim();
  return t.content.firstChild;
}

function addUser(text) {
  document.querySelector(".empty")?.remove();
  chat.appendChild(el(`<div class="msg user"><div class="bubble"></div></div>`));
  chat.lastChild.querySelector(".bubble").textContent = text;
}

function addBot() {
  const node = el(`
    <div class="msg bot">
      <div class="trace open">
        <div class="trace-head">
          <span class="label">Agent flow</span>
          <span class="chev">›</span>
        </div>
        <div class="trace-body"></div>
      </div>
      <div class="answer pending"><span class="thinking"><i></i><i></i><i></i></span></div>
    </div>`);
  node.querySelector(".trace-head").addEventListener("click", () =>
    node.querySelector(".trace").classList.toggle("open")
  );
  chat.appendChild(node);
  scroll();
  return node;
}

function addStep(body, kind, title, detail, code) {
  const n = NODE[kind];
  const step = el(`
    <div class="step">
      <div class="rail"><div class="node ${n.cls}">${n.icon}</div><div class="line"></div></div>
      <div class="body">
        <div class="t">${title}</div>
        ${detail ? `<div class="d">${detail}</div>` : ""}
        ${code ? `<div class="code"></div>` : ""}
      </div>
    </div>`);
  if (code) step.querySelector(".code").textContent = code;
  body.appendChild(step);
  scroll();
  return step;
}

function scroll() {
  chat.scrollTop = chat.scrollHeight;
}

// ---------- the conversation turn ----------
async function send(text) {
  addUser(text);
  const bot = addBot();
  const body = bot.querySelector(".trace-body");
  const answerEl = bot.querySelector(".answer");

  const res = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message: text }),
  });

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop();
    for (const line of lines) {
      if (line.trim()) handleEvent(JSON.parse(line), body, answerEl);
    }
  }
}

function handleEvent(ev, body, answerEl) {
  switch (ev.type) {
    case "orchestrator_start":
      addStep(body, "orch", "Orchestrator", "Reading the request and choosing an agent…");
      break;
    case "route":
      addStep(body, "route", `Routed to ${ev.agent}`, ev.description);
      break;
    case "tool_start":
      addStep(body, "tool", `Tool · ${ev.tool}`, "", JSON.stringify(ev.args));
      break;
    case "tool_end": {
      const step = addStep(body, "tool", `Result · ${ev.tool}`, "", ev.result);
      step.querySelector(".code").style.color = "var(--green)";
      break;
    }
    case "final":
      addStep(body, "done", "Answer ready", `${ev.agent} responded`);
      answerEl.classList.remove("pending");
      answerEl.textContent = ev.answer || "(no answer)";
      break;
    case "error":
      answerEl.classList.remove("pending");
      answerEl.style.color = "var(--rose)";
      answerEl.textContent = "Error: " + ev.message;
      break;
  }
  scroll();
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const text = input.value.trim();
  if (!text) return;
  input.value = "";
  sendBtn.disabled = true;
  input.disabled = true;
  try {
    await send(text);
  } catch (err) {
    addBot().querySelector(".answer").textContent = "Request failed: " + err.message;
  } finally {
    sendBtn.disabled = false;
    input.disabled = false;
    input.focus();
  }
});

init();
