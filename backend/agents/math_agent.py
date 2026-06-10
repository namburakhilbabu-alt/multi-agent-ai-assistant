"""Specialist agent for calculations and unit conversions."""

from __future__ import annotations

from ..tools import calculator, convert_units
from .base import Agent

# Kept deliberately short and imperative: small local models reliably call tools
# when told only to use them, but tend to answer from memory when the prompt also
# describes what to do *after* the tool returns.
SYSTEM_PROMPT = (
    "You are the Math Agent. Always use the calculator tool for arithmetic and "
    "the convert_units tool for unit conversions."
)


def build() -> Agent:
    return Agent(
        name="Math Agent",
        description="Performs arithmetic, calculations and unit conversions "
        "(length, mass, temperature).",
        system_prompt=SYSTEM_PROMPT,
        tools=[calculator, convert_units],
    )
