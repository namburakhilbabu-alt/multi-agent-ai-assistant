"""Specialist agent for writing tasks — no tools, pure LLM."""

from __future__ import annotations

from ..llm import get_llm
from .base import Agent

SYSTEM_PROMPT = (
    "You are the Writer Agent. You help with writing: drafting, rewriting, "
    "summarizing, and translating text. Produce clean, well-structured prose and "
    "return only the requested text without extra commentary."
)


def build() -> Agent:
    return Agent(
        name="Writer Agent",
        description="Drafts, rewrites, summarizes and translates text.",
        system_prompt=SYSTEM_PROMPT,
        tools=[],
        llm=get_llm(temperature=0.3),
    )
