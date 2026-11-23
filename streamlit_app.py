"""Maestro — Streamlit front end.

Runs the multi-agent orchestrator directly (no FastAPI server needed), so it
can be deployed as-is on Streamlit Community Cloud.

    streamlit run streamlit_app.py

Configuration (Streamlit secrets or environment variables):
    GROQ_API_KEY  — free key from https://console.groq.com (required on the cloud)
    GROQ_MODEL    — optional, defaults to openai/gpt-oss-20b
"""

from __future__ import annotations

import asyncio
import json
import os

import streamlit as st

st.set_page_config(page_title="Maestro · Multi-Agent Assistant", page_icon="◆", layout="centered")


def _load_secrets() -> None:
    """Copy Streamlit secrets into the environment before the backend reads them."""
    for key in ("GROQ_API_KEY", "GROQ_MODEL", "OLLAMA_HOST", "MAESTRO_MODEL"):
        try:
            value = st.secrets.get(key)
        except Exception:  # no secrets.toml at all
            value = None
        if value and not os.getenv(key):
            os.environ[key] = str(value)


_load_secrets()

from backend.llm import active_model, groq_api_key  # noqa: E402  (needs env first)
from backend.orchestrator import Orchestrator  # noqa: E402

AGENT_ICONS = {
    "Math Agent": "🧮",
    "Weather Agent": "🌦️",
    "Research Agent": "📚",
    "Writer Agent": "✍️",
}

EXAMPLES = [
    "What is (1200 * 1.18) / 12?",
    "Convert 5 miles to kilometers",
    "What's the weather in Hyderabad right now?",
    "How do I add a new agent to Maestro?",
    "Rewrite this to sound professional: hey, can u send the report asap",
]


@st.cache_resource(show_spinner="Starting the agents…")
def get_orchestrator(model: str) -> Orchestrator:
    # `model` is part of the cache key so changing GROQ_MODEL rebuilds the agents.
    return Orchestrator()


def run_query(orchestrator: Orchestrator, query: str) -> tuple[str, list[dict]]:
    """Run one request through the supervisor and collect every event."""
    events: list[dict] = []

    async def emit(event: dict) -> None:
        events.append(event)

    answer = asyncio.run(orchestrator.handle(query, emit))
    return answer, events


def render_trace(events: list[dict]) -> None:
    """Show which agent handled the request and the tools it called."""
    agent = next((e["agent"] for e in events if e["type"] == "route"), None)
    tools = [e for e in events if e["type"] in ("tool_start", "tool_end")]
    if not agent and not tools:
        return
    label = f"{AGENT_ICONS.get(agent, '◆')} Handled by **{agent}**" if agent else "◆ Agent trace"
    if tools:
        label += f" · {sum(1 for t in tools if t['type'] == 'tool_start')} tool call(s)"
    with st.expander(label, expanded=False):
        for e in events:
            if e["type"] == "route":
                st.markdown(f"**Orchestrator → {e['agent']}**  \n{e.get('description', '')}")
            elif e["type"] == "tool_start":
                st.markdown(f"🔧 `{e['tool']}` called with")
                st.code(json.dumps(e.get("args", {}), ensure_ascii=False, default=str), language="json")
            elif e["type"] == "tool_end":
                st.markdown(f"↳ `{e['tool']}` returned")
                st.code(str(e.get("result", ""))[:2000], language="text")


# ---------------------------------------------------------------- sidebar
with st.sidebar:
    st.title("◆ Maestro")
    st.caption("A supervisor agent routes each request to one specialist agent that uses real tools.")
    st.markdown(
        "\n".join(f"- {icon} **{name}**" for name, icon in AGENT_ICONS.items())
    )
    st.divider()
    backend = "Groq (cloud)" if groq_api_key() else "Ollama (local)"
    st.markdown(f"**Backend:** {backend}  \n**Model:** `{active_model()}`")
    if st.button("Clear chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# ---------------------------------------------------------------- main
st.title("Maestro")
st.caption("Multi-agent AI assistant · LangGraph + Groq")

if not groq_api_key() and not os.getenv("OLLAMA_HOST"):
    st.warning(
        "**No `GROQ_API_KEY` found.**\n\n"
        "Get a free key at [console.groq.com](https://console.groq.com/keys), then:\n"
        "- **Streamlit Cloud:** app ⋮ menu → *Settings* → *Secrets* → add `GROQ_API_KEY = \"gsk_...\"`\n"
        "- **Local:** put it in `.streamlit/secrets.toml` (see `secrets.toml.example`)\n\n"
        "Without a key the app falls back to a local Ollama server at http://localhost:11434.",
        icon="🔑",
    )

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg["role"] == "assistant":
            render_trace(msg.get("events", []))
        st.markdown(msg["content"])

prompt = st.chat_input("Ask Maestro anything…")

if not st.session_state.messages and not prompt:
    st.markdown("**Try one of these:**")
    cols = st.columns(2)
    for i, example in enumerate(EXAMPLES):
        if cols[i % 2].button(example, key=f"ex{i}", use_container_width=True):
            st.session_state.pending = example
            st.rerun()

prompt = prompt or st.session_state.pop("pending", None)

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Routing to the right agent…"):
            try:
                answer, events = run_query(get_orchestrator(active_model()), prompt)
                answer = answer or "_(no answer)_"
            except Exception as exc:  # show the problem instead of crashing the app
                events = []
                answer = f"⚠️ Something went wrong: `{exc}`"
                if "401" in str(exc) or "api_key" in str(exc).lower():
                    answer += "\n\nCheck that `GROQ_API_KEY` is set correctly in your secrets."
                elif "model" in str(exc).lower():
                    answer += "\n\nTry another model via the `GROQ_MODEL` secret, e.g. `llama-3.3-70b-versatile`."
                elif "rate" in str(exc).lower() or "429" in str(exc):
                    answer += "\n\nGroq free-tier rate limit reached — wait a minute and try again."
        render_trace(events)
        st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer, "events": events})
