"""LLM factory — returns a LangChain chat model.

Auto-selects backend:
  - GROQ_API_KEY set     → ChatGroq   (cloud, fast, free tier)
  - GROQ_API_KEY not set → ChatOllama (local fallback)

Settings are read from the environment each time they are needed, so a host
(e.g. the Streamlit app reading st.secrets) can set them before first use.
"""

from __future__ import annotations

import os
from pathlib import Path

import httpx

# Load .env from the project root so GROQ_API_KEY etc. work without exporting.
_env_file = Path(__file__).resolve().parent.parent / ".env"
if _env_file.exists():
    from dotenv import load_dotenv
    load_dotenv(_env_file)

from langchain_core.language_models import BaseChatModel

# A Groq model that supports tool calling and is available on the free tier.
DEFAULT_GROQ_MODEL = "openai/gpt-oss-20b"


def groq_api_key() -> str:
    return os.getenv("GROQ_API_KEY", "").strip()


def groq_model() -> str:
    return os.getenv("GROQ_MODEL", "").strip() or DEFAULT_GROQ_MODEL


def ollama_host() -> str:
    return os.getenv("OLLAMA_HOST", "http://localhost:11434")


def ollama_model() -> str:
    return os.getenv("MAESTRO_MODEL", "mistral:latest")


def active_model() -> str:
    """Name of the model that get_llm() will use."""
    return groq_model() if groq_api_key() else ollama_model()


def get_llm(temperature: float = 0.0) -> BaseChatModel:
    """Return the active LangChain chat model."""
    if groq_api_key():
        from langchain_groq import ChatGroq

        return ChatGroq(
            api_key=groq_api_key(),
            model=groq_model(),
            temperature=temperature,
            max_retries=2,
        )
    from langchain_ollama import ChatOllama

    return ChatOllama(
        base_url=ollama_host(),
        model=ollama_model(),
        temperature=temperature,
    )


async def check_health() -> bool:
    """True if the active LLM backend is reachable."""
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            if groq_api_key():
                resp = await client.get(
                    "https://api.groq.com/openai/v1/models",
                    headers={"Authorization": f"Bearer {groq_api_key()}"},
                )
            else:
                resp = await client.get(f"{ollama_host()}/api/tags")
            return resp.status_code == 200
    except httpx.HTTPError:
        return False
