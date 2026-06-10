"""Specialist agent that answers from the local knowledge base."""

from __future__ import annotations

from ..tools import search_knowledge_base
from .base import Agent

SYSTEM_PROMPT = (
    "You are the Research Agent. Always use the search_knowledge_base tool to look "
    "up information before answering questions about Maestro."
)


def build() -> Agent:
    return Agent(
        name="Research Agent",
        description="Answers questions about Maestro itself — what it is, how it "
        "works, and how to use, configure or extend it — from the knowledge base.",
        system_prompt=SYSTEM_PROMPT,
        tools=[search_knowledge_base],
    )
