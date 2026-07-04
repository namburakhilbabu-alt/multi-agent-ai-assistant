"""Specialist agent for live weather lookups."""

from __future__ import annotations

from ..llm import get_llm
from ..tools.weather import get_weather
from .base import Agent

SYSTEM_PROMPT = (
    "You are the Weather Agent. Always use the get_weather tool to look up the "
    "weather for the city the user mentions. Never guess the weather."
)


def build() -> Agent:
    return Agent(
        name="Weather Agent",
        description="Looks up the current weather and temperature for any city.",
        system_prompt=SYSTEM_PROMPT,
        tools=[get_weather],
        llm=get_llm(temperature=0.0),
    )
