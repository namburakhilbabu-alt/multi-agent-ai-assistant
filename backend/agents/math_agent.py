"""Specialist agent for calculations and unit conversions."""

from __future__ import annotations

from ..llm import get_llm
from ..tools.calculator import calculator
from ..tools.units import convert_units
from .base import Agent

SYSTEM_PROMPT = (
    "You are the Math Agent. Always use the calculator tool for arithmetic and "
    "the convert_units tool for unit conversions. Never calculate in your head."
)


def build() -> Agent:
    return Agent(
        name="Math Agent",
        description="Performs arithmetic, calculations and unit conversions (length, mass, temperature).",
        system_prompt=SYSTEM_PROMPT,
        tools=[calculator, convert_units],
        llm=get_llm(temperature=0.0),
    )
