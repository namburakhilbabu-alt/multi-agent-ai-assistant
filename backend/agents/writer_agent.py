"""Specialist agent for writing tasks. Needs no tools — just the model."""

from __future__ import annotations

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
    )
