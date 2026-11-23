# Frequently asked questions

## What do I need to run Maestro?

Python 3.10+ and either a free Groq API key (from console.groq.com, set as
`GROQ_API_KEY`) or a running Ollama server with the Mistral model pulled
(`ollama pull mistral`). Start the Streamlit app with `streamlit run streamlit_app.py`.

## Does Maestro send my data anywhere?

With Ollama, the model runs locally and nothing leaves your machine. With Groq,
your messages are sent to the Groq API to be answered. The Weather Agent also
queries a free public weather API (Open-Meteo) when you ask about the weather.

## How do I add a new agent?

Create a new agent in `backend/agents/`, give it a name, description, system
prompt and any tools it needs, then register it in the orchestrator. The
supervisor will start routing matching requests to it automatically.

## Which model does it use?

With a Groq key it uses `openai/gpt-oss-20b` by default; change it with the
`GROQ_MODEL` setting (any Groq model that supports tool calling, e.g.
`llama-3.3-70b-versatile`). Without a key it uses Mistral served by Ollama;
pick another Ollama model with the `MAESTRO_MODEL` environment variable.

## How do I deploy Maestro?

The easiest free option is Streamlit Community Cloud: point it at the GitHub
repository, choose `streamlit_app.py` as the main file, and add `GROQ_API_KEY`
in the app's Secrets.
