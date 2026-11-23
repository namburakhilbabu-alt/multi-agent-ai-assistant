#!/usr/bin/env bash
# Start the FastAPI server locally with Ollama. For the Streamlit app use: streamlit run streamlit_app.py
set -euo pipefail

cd "$(dirname "$0")"

if ! curl -sf http://localhost:11434/api/tags >/dev/null; then
  echo "Ollama doesn't seem to be running on http://localhost:11434"
  echo "Start it with 'ollama serve' and pull the model: 'ollama pull mistral'"
  exit 1
fi

echo "Starting Maestro on http://localhost:8000"
exec uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
