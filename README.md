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

**A local-first, multi-agent AI assistant.**

One supervisor orchestrator routes every request to the right specialist agent —
and each agent uses real tools to get the job done. Runs 100% on your machine
with [Ollama](https://ollama.com) + Mistral. No API keys. No cloud.

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)
![Ollama](https://img.shields.io/badge/Ollama-Mistral-000000?logo=ollama&logoColor=white)
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

Every step is streamed to the UI, so you can **watch the orchestrator route the
request and the agent call its tools live**.

## Demo

The web UI shows the live agent flow for each request — which agent was chosen,
which tools ran, and what they returned — alongside the final answer.

> *Add a screenshot or GIF here once you've run it locally:* `docs/demo.png`

## The agents

| Agent | What it does | Tools |
|-------|--------------|-------|
| **Math Agent** | Arithmetic & unit conversions | `calculator`, `convert_units` |
| **Research Agent** | Answers from a local knowledge base | `search_knowledge_base` |
| **Weather Agent** | Live weather for any city | `get_weather` (Open-Meteo) |
| **Writer Agent** | Draft, rewrite, summarize, translate | — |

## Quick start

**Prerequisites:** Python 3.10+ and [Ollama](https://ollama.com) running locally.

```bash
# 1. Pull the model
ollama pull mistral

# 2. Install dependencies
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 3. Run
./run.sh            # or: uvicorn backend.main:app --reload
```

Open **http://localhost:8000** and start chatting.

## How it works

The whole system is small and readable — about 600 lines of Python.

| Piece | File | Responsibility |
|-------|------|----------------|
| LLM client | [`backend/llm.py`](backend/llm.py) | The only code that talks to Ollama |
| Tool abstraction | [`backend/tools/base.py`](backend/tools/base.py) | `@tool` decorator → JSON schema + runnable function |
| Agent runtime | [`backend/agents/base.py`](backend/agents/base.py) | The reason-and-act loop shared by every agent |
| Specialists | [`backend/agents/`](backend/agents/) | One small module per agent |
| Orchestrator | [`backend/orchestrator.py`](backend/orchestrator.py) | LLM-based routing to a single agent |
| API | [`backend/main.py`](backend/main.py) | FastAPI; streams the run as NDJSON |
| UI | [`frontend/`](frontend/) | Single-page chat with a live flow visualizer |

Routing is itself a tool call: the orchestrator gives the model one
`select_agent` function whose only argument is an enum of agent names, which
makes the decision reliable and trivial to parse.

See [`docs/architecture.md`](docs/architecture.md) for a deeper walkthrough.

## Add your own agent

1. Create `backend/agents/my_agent.py` with a `build()` that returns an `Agent`.
2. Register it in the `Orchestrator` roster.

That's it — the supervisor starts routing matching requests to it automatically.

## API

| Method | Route | Description |
|--------|-------|-------------|
| `POST` | `/api/chat` | Run the orchestrator; streams events as NDJSON |
| `GET` | `/api/agents` | List the available agents |
| `GET` | `/api/health` | Model/backend health |

## Tech

Python · FastAPI · httpx · Ollama (Mistral) · vanilla JS — no build step, no
external services beyond an optional weather lookup.

## License

MIT — see [LICENSE](LICENSE).
