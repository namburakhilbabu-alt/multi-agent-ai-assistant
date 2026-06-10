# Frequently asked questions

## What do I need to run Maestro?

Python 3.10+ and a running Ollama server with the Mistral model pulled
(`ollama pull mistral`). That's it — no cloud account, no API keys.

## Does Maestro send my data anywhere?

No. The model runs locally through Ollama. The only optional outbound call is
the Weather Agent, which queries a free public weather API when you ask about
the weather.

## How do I add a new agent?

Create a new agent in `backend/agents/`, give it a name, description, system
prompt and any tools it needs, then register it in the orchestrator. The
supervisor will start routing matching requests to it automatically.

## Which model does it use?

Mistral by default, served by Ollama. You can point Maestro at any other
Ollama model by setting the `MAESTRO_MODEL` environment variable.
