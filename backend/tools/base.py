"""The tool abstraction.

A *tool* is just a Python function the model is allowed to call. The ``@tool``
decorator attaches an Ollama-compatible JSON schema to a function so it can be
advertised to the model, and exposes a ``.spec`` (what the model sees) and a
``.run()`` (what actually executes).

Keeping tools as plain functions means they are trivial to unit-test in
isolation, with no model in the loop.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class Tool:
    name: str
    description: str
    parameters: dict[str, Any]
    func: Callable[..., str]

    @property
    def spec(self) -> dict[str, Any]:
        """The function schema advertised to the model."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }

    def run(self, **kwargs: Any) -> str:
        """Execute the tool, always returning a string for the model to read."""
        try:
            return str(self.func(**kwargs))
        except Exception as exc:  # surface errors back to the model, don't crash
            return f"Tool error: {exc}"


def tool(description: str, parameters: dict[str, Any]):
    """Decorator that turns a function into a :class:`Tool`.

    ``parameters`` is a JSON-schema object describing the arguments, e.g.::

        {"type": "object",
         "properties": {"city": {"type": "string", "description": "City name"}},
         "required": ["city"]}
    """

    def wrapper(func: Callable[..., str]) -> Tool:
        return Tool(
            name=func.__name__,
            description=description,
            parameters=parameters,
            func=func,
        )

    return wrapper
