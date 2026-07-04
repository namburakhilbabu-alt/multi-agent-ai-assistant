"""LLM factory — returns a LangChain chat model.

Auto-selects backend:
  - GROQ_API_KEY set  → ChatGroq  (cloud, fast, free)
  - GROQ_API_KEY not set → ChatOllama (local fallback)
"""

from __future__ import annotations

import os

import httpx
from langchain_core.language_models import BaseChatModel
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("MAESTRO_MODEL", "mistral:latest")

MODEL = GROQ_MODEL if GROQ_API_KEY else OLLAMA_MODEL


def get_llm(temperature: float = 0.0) -> BaseChatModel:
    """Return the active LangChain chat model."""
    if GROQ_API_KEY:
        return ChatGroq(
            api_key=GROQ_API_KEY,
            model=GROQ_MODEL,
            temperature=temperature,
        )
    return ChatOllama(
        base_url=OLLAMA_HOST,
        model=OLLAMA_MODEL,
        temperature=temperature,
    )


async def check_health() -> bool:
    """True if the active LLM backend is reachable."""
    if GROQ_API_KEY:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(
                    "https://api.groq.com/openai/v1/models",
                    headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
                )
                return resp.status_code == 200
        except httpx.HTTPError:
            return False
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{OLLAMA_HOST}/api/tags")
            return resp.status_code == 200
    except httpx.HTTPError:
        return False
