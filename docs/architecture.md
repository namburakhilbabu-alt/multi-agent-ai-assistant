# Architecture

Maestro is a deliberately small demonstration of a multi-agent pattern:
**a supervisor that routes to specialist agents, each of which uses tools.**
This document walks through the moving parts.

## Request lifecycle

```
POST /api/chat {"message": "..."}
        │
        ▼
┌──────────────────┐   1. select_agent(...)        ┌──────────────────────┐
│   Orchestrator   │ ─────── LLM call ───────────▶ │  picks ONE agent      │
└──────────────────┘                               └──────────────────────┘
        │
        ▼
┌──────────────────┐   2. reason → act loop
│ Specialist Agent │ ──────────────────────────────┐
└──────────────────┘                               │
        │  needs a tool?                            │
        ├── yes ──▶ run tool ──▶ feed result back ──┘ (repeat)
        └── no  ──▶ final answer
        │
        ▼
   NDJSON event stream  ──▶  UI renders the live flow + answer
```

Every stage emits an event (`orchestrator_start`, `route`, `tool_start`,
`tool_end`, `final`). The API forwards these to the browser as
newline-delimited JSON so the flow can be animated as it happens.

## Components

### LLM client — `backend/llm.py`
The single point of contact with the model. It wraps Ollama's `/api/chat`
endpoint and returns the assistant message, including any `tool_calls` the
model requested. Swapping models or providers is a one-file change.

### Tools — `backend/tools/`
A tool is a plain Python function wrapped by the `@tool` decorator, which
attaches an Ollama-compatible JSON schema. Because tools are ordinary
functions, they can be tested with no model in the loop. Included tools:

- `calculator` — safe arithmetic via an AST evaluator (no `eval`).
- `convert_units` — length, mass and temperature conversions.
- `get_weather` — live data from the free, key-less Open-Meteo API.
- `search_knowledge_base` — keyword search over local Markdown docs.

### Agent runtime — `backend/agents/base.py`
The `Agent` class runs the reason-and-act loop: call the model with the agent's
tools, execute any requested tool calls, append the results, and repeat until
the model answers in plain text (bounded by a step budget).

### Specialist agents — `backend/agents/`
Each agent is a thin module that supplies a name, description, system prompt and
tool list. Keeping prompts short and imperative is intentional — small local
models call tools far more reliably when the prompt only tells them *to use the
tool*, rather than also describing what to do with the result.

### Orchestrator — `backend/orchestrator.py`
Holds the agent roster and routes each request. Routing is implemented as a
forced tool call (`select_agent`) whose argument is an enum of agent names,
which makes the model's choice both reliable and easy to parse. If routing ever
fails, it falls back to a safe default agent.

### API & UI — `backend/main.py`, `frontend/`
FastAPI exposes the chat endpoint and serves the single-page UI. The frontend
reads the NDJSON stream and renders each event as a step in the agent-flow
trace, with the final answer shown beneath it.

## Design choices

- **Routing over one mega-prompt.** Small, focused prompts are easier to make
  reliable and to debug, and new capabilities are added in isolation.
- **Tools as plain functions.** No framework lock-in; trivially unit-testable.
- **Streaming events.** The point of a multi-agent system is the *process* —
  showing it live makes the orchestration legible instead of a black box.
- **Local-first.** Everything runs through Ollama on your own machine.
