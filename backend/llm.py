"""LLM client — auto-selects backend based on environment:
  - GROQ_API_KEY is set  → Groq cloud API (for production / HF Spaces)
  - GROQ_API_KEY not set → Ollama local (for local development)

This is the only file that knows how to speak to the model.
Swapping backends is a one-file change.
"""

from __future__ import annotations

import os
from typing import Any

import httpx

# Ollama (local)
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("MAESTRO_MODEL", "mistral:latest")
REQUEST_TIMEOUT = float(os.getenv("MAESTRO_TIMEOUT", "120"))

# Groq (cloud)
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# Whichever is active becomes MODEL (shown in /api/health)
MODEL = GROQ_MODEL if GROQ_API_KEY else OLLAMA_MODEL


class LLMClient:
    def __init__(self):
        self.use_groq = bool(GROQ_API_KEY)

    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.0,
    ) -> dict[str, Any]:
        if self.use_groq:
            return await self._chat_groq(messages, tools, temperature)
        return await self._chat_ollama(messages, tools, temperature)

    async def _chat_groq(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None,
        temperature: float,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": GROQ_MODEL,
            "messages": messages,
            "temperature": temperature,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            resp = await client.post(GROQ_API_URL, json=payload, headers=headers)
            if resp.status_code != 200:
                print(f"Groq error {resp.status_code}: {resp.text}")
            resp.raise_for_status()

        choice = resp.json()["choices"][0]["message"]
        # Normalise to Ollama shape: {content, tool_calls}
        result: dict[str, Any] = {"content": choice.get("content") or ""}
        if choice.get("tool_calls"):
            result["tool_calls"] = [
                {
                    "function": {
                        "name": tc["function"]["name"],
                        "arguments": _parse_args(tc["function"].get("arguments", {})),
                    }
                }
                for tc in choice["tool_calls"]
            ]
        return result

    async def _chat_ollama(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None,
        temperature: float,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": OLLAMA_MODEL,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature},
        }
        if tools:
            payload["tools"] = tools

        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            resp = await client.post(f"{OLLAMA_HOST}/api/chat", json=payload)
            resp.raise_for_status()
            return resp.json().get("message", {})

    async def health(self) -> bool:
        if self.use_groq:
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


def _parse_args(arguments: Any) -> dict:
    """Groq returns arguments as a JSON string; normalise to dict."""
    if isinstance(arguments, dict):
        return arguments
    if isinstance(arguments, str):
        import json
        try:
            return json.loads(arguments)
        except Exception:
            return {}
    return {}
