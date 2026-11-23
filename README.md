---
title: Maestro
emoji: 🤖
colorFrom: indigo
colorTo: blue
sdk: docker
pinned: false
---

<div align="center">

# ◆ Maestro

**A multi-agent AI assistant.**

One supervisor orchestrator routes every request to the right specialist agent —
and each agent uses real tools to get the job done. Runs on a **free** cloud
model via [Groq](https://console.groq.com), or 100% locally with
[Ollama](https://ollama.com) + Mistral.

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-app-FF4B4B?logo=streamlit&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-agents-1C3C3C)
![Groq](https://img.shields.io/badge/Groq-free_tier-F55036)
![License](https://img.shields.io/badge/License-MIT-22c55e)

</div>

---

## What it is

Instead of asking one big model to do everything, Maestro splits the work across
a small team of focused agents and a supervisor that decides who handles what:

```
                                    ┌─────────────────┐
                          ┌────────▶│   Math Agent     │──▶ calculator, convert_units
   User ──▶ Orchestrator ─┤        ├─────────────────┤
            (routes the    ├───────▶│  Research Agent  │──▶ search_knowledge_base
             request to    │        ├─────────────────┤
             one agent)    ├───────▶│  Weather Agent   │──▶ get_weather (live API)
                           └───────▶│  Writer Agent    │──▶ (no tools — pure LLM)
                                    └─────────────────┘
```

1. **Orchestrator** — reads your message and picks the single best agent for it.
2. **Specialist agent** — runs a *reason → act* loop: decides if it needs a tool,
   calls it, reads the result, and answers.
3. **Tools** — plain Python functions that do the real work.

The UI shows **which agent handled each request and every tool call it made**.

## The agents

| Agent | What it does | Tools |
|-------|--------------|-------|
| **Math Agent** | Arithmetic & unit conversions | `calculator`, `convert_units` |
| **Research Agent** | Answers from a local knowledge base | `search_knowledge_base` |
| **Weather Agent** | Live weather for any city | `get_weather` (Open-Meteo, free, no key) |
| **Writer Agent** | Draft, rewrite, summarize, translate | — |

## Which model? (all free)

| Backend | When it's used | Default model | Cost |
|---------|----------------|---------------|------|
| **Groq** (cloud) | `GROQ_API_KEY` is set | `openai/gpt-oss-20b` | Free tier, no credit card |
| **Ollama** (local) | no `GROQ_API_KEY` | `mistral:latest` | Free, runs on your machine |

Change the Groq model with the `GROQ_MODEL` setting — any Groq model that
supports **tool calling** works (e.g. `llama-3.3-70b-versatile`). See the
current list at <https://console.groq.com/docs/models>.

---

## Deploy on Streamlit Community Cloud (free)

You need: a GitHub account and a free Groq API key. Takes about 5 minutes.

### Step 1 — Get a free Groq API key

1. Go to <https://console.groq.com> and sign in (Google or GitHub login works).
2. Open **API Keys** → **Create API Key** → give it a name → **Submit**.
3. Copy the key (starts with `gsk_...`). You only see it once, so save it somewhere safe.

### Step 2 — Have the code on GitHub

- If this is your repository, you're done: it's already on GitHub.
- Otherwise click **Fork** at the top of the GitHub page to copy it to your account.

### Step 3 — Create the app

1. Go to <https://share.streamlit.io> and **sign in with GitHub**
   (first time: allow Streamlit to access your repositories).
2. Click **Create app** → **Deploy a public app from GitHub** (or "Yup, I have an app").
3. Fill in:
   - **Repository:** `<your-github-username>/multi-agent-ai-assistant`
   - **Branch:** `main`
   - **Main file path:** `streamlit_app.py`
   - **App URL:** pick a name, e.g. `maestro-agents`
4. Click **Advanced settings**:
   - **Python version:** `3.12`
   - **Secrets:** paste this (with your real key):
     ```toml
     GROQ_API_KEY = "gsk_your_key_here"
     ```
   - Click **Save**.
5. Click **Deploy**. The first build takes 2–4 minutes while it installs the
   requirements. Then your app is live at `https://<app-url>.streamlit.app`.

### Step 4 — Try it

Click one of the example buttons, or ask:
- `What is (1200 * 1.18) / 12?` → Math Agent
- `What's the weather in Hyderabad?` → Weather Agent
- `How do I add a new agent to Maestro?` → Research Agent
- `Rewrite: hey can u send the report asap` → Writer Agent

Open the **"Handled by …"** expander above each answer to see the routing and tool calls.

### Updating the app later

Push to the `main` branch and Streamlit redeploys automatically. To change
secrets: open your app → **⋮** (top right) → **Settings** → **Secrets** → edit → **Save**.

---

## Run locally on another laptop

**Prerequisites:** [Python 3.10+](https://www.python.org/downloads/) (3.12 recommended) and [Git](https://git-scm.com/downloads).

```bash
# 1. Get the code
git clone https://github.com/namburakhilbabu-alt/multi-agent-ai-assistant.git
cd multi-agent-ai-assistant

# 2. Create a virtual environment and install dependencies
python -m venv .venv
# macOS / Linux:
source .venv/bin/activate
# Windows (PowerShell):
#   .venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 3. Add your Groq key
#    macOS / Linux:
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
#    Windows:
#      copy .streamlit\secrets.toml.example .streamlit\secrets.toml
#    then open .streamlit/secrets.toml and replace gsk_your_key_here with your key

# 4. Run
streamlit run streamlit_app.py
```

Your browser opens at **http://localhost:8501**.

**No internet / fully offline?** Skip step 3, install [Ollama](https://ollama.com),
run `ollama pull mistral`, keep Ollama running, then `streamlit run streamlit_app.py`.
Maestro uses Ollama automatically when no Groq key is set.

### Optional: the FastAPI server + custom web UI

```bash
cp .env.example .env        # put GROQ_API_KEY in .env (or leave empty to use Ollama)
uvicorn backend.main:app --reload
```

Open **http://localhost:8000**. The `Dockerfile` runs this server on port 7860
(e.g. for a Hugging Face Docker Space).

### Run the tests

```bash
pip install pytest
pytest
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Yellow "No `GROQ_API_KEY` found" box | Secrets not set. Cloud: ⋮ → Settings → Secrets. Local: create `.streamlit/secrets.toml`. Then reboot the app (⋮ → **Reboot app**). |
| `Error code: 401 … Invalid API Key` | Key copied wrong, or it was deleted. Create a new key at console.groq.com and update the secret. Make sure it's in quotes: `GROQ_API_KEY = "gsk_..."` |
| `model … decommissioned` / `model not found` | Groq retired that model. Add `GROQ_MODEL = "llama-3.3-70b-versatile"` (or another tool-calling model from the Groq models page) to secrets. |
| `429` / rate limit | The free tier limits requests per minute. Wait a minute and retry. Each question uses 3–4 model calls. |
| Build fails on Streamlit Cloud | Check the logs (**Manage app** at bottom right). Make sure the Python version is 3.12 in Advanced settings; to change it later, delete the app and redeploy. |
| `Connection refused … 11434` locally | No Groq key is set, so it tried Ollama. Add the key, or start Ollama (`ollama serve`) and `ollama pull mistral`. |
| `streamlit: command not found` | Activate the virtual environment first (`source .venv/bin/activate` or `.venv\Scripts\Activate.ps1`). |
| Windows: "running scripts is disabled" when activating | Run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` in PowerShell once. |
| Weather Agent says "lookup error" | Open-Meteo was briefly unreachable. Retry. |

---

## How it works

| Piece | File | Responsibility |
|-------|------|----------------|
| Streamlit app | [`streamlit_app.py`](streamlit_app.py) | Chat UI; calls the orchestrator directly |
| LLM factory | [`backend/llm.py`](backend/llm.py) | Picks Groq or Ollama and returns a LangChain chat model |
| Tools | [`backend/tools/`](backend/tools/) | LangChain `@tool` functions (calculator, units, weather, knowledge base) |
| Agent runtime | [`backend/agents/base.py`](backend/agents/base.py) | Wraps LangGraph `create_react_agent` (the reason-and-act loop) |
| Specialists | [`backend/agents/`](backend/agents/) | One small module per agent |
| Orchestrator | [`backend/orchestrator.py`](backend/orchestrator.py) | Supervisor agent whose "tools" are the specialist agents |
| API | [`backend/main.py`](backend/main.py) | FastAPI; streams the run as NDJSON |
| Web UI | [`frontend/`](frontend/) | Single-page chat with a live flow visualizer |

Routing is itself a tool call: each specialist agent is wrapped as a tool
(`call_math_agent`, `call_weather_agent`, …) and the supervisor picks one.

See [`docs/architecture.md`](docs/architecture.md) for a deeper walkthrough.

## Add your own agent

1. Create `backend/agents/my_agent.py` with a `build()` that returns an `Agent`.
2. In `backend/orchestrator.py`, build it, wrap it as a `call_my_agent` tool and
   add it to `agent_tools` and `_TOOL_TO_AGENT`.

The supervisor starts routing matching requests to it automatically.

## API (FastAPI server)

| Method | Route | Description |
|--------|-------|-------------|
| `POST` | `/api/chat` | Run the orchestrator; streams events as NDJSON |
| `GET` | `/api/agents` | List the available agents |
| `GET` | `/api/health` | Model/backend health |

## Tech

Python · Streamlit · LangChain · LangGraph · Groq / Ollama · FastAPI · vanilla JS

## License

MIT — see [LICENSE](LICENSE).
