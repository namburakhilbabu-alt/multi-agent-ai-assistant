# About Maestro

Maestro is a local-first multi-agent AI assistant. A central supervisor
(the "orchestrator") reads each user request and routes it to the specialist
agent best suited to answer it. Each agent can call real tools to do its job.

Maestro runs with a free cloud model on Groq (when a GROQ_API_KEY is set) or
entirely on your own machine using Ollama and the Mistral model. It has a
Streamlit web app and a FastAPI server with its own web UI.

## The agents

- **Math Agent** — performs calculations and unit conversions.
- **Research Agent** — answers questions from this local knowledge base.
- **Weather Agent** — looks up live weather for any city.
- **Writer Agent** — drafts, rewrites, summarizes and translates text.
