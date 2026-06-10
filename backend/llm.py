"""Thin async client around the Ollama chat API.

Maestro talks to a locally-running Ollama server (default: mistral). This is the
only place in the codebase that knows how to speak to the model, so swapping the
backend (a different local model, or a hosted one) is a one-file change.
"""

from __future__ import annotations

import os
from typing import Any

import httpx

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
MODEL = os.getenv("MAESTRO_MODEL", "mistral:latest")
REQUEST_TIMEOUT = float(os.getenv("MAESTRO_TIMEOUT", "120"))


class LLMClient:
    """Minimal wrapper over `POST /api/chat`."""

    def __init__(self, model: str = MODEL, host: str = OLLAMA_HOST):
        self.model = model
        self.host = host.rstrip("/")

    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.0,
    ) -> dict[str, Any]:
        """Send a chat turn and return the assistant message.

        The returned dict follows Ollama's shape: it has a ``content`` string and,
        when the model decides to use a tool, a ``tool_calls`` list.
        """
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature},
        }
        if tools:
            payload["tools"] = tools

        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            resp = await client.post(f"{self.host}/api/chat", json=payload)
            resp.raise_for_status()
            return resp.json().get("message", {})

    async def health(self) -> bool:
        """True if the Ollama server is reachable."""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{self.host}/api/tags")
                return resp.status_code == 200
        except httpx.HTTPError:
            return False
