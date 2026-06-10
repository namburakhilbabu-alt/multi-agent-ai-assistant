"""The shared agent runtime.

Every specialist agent is an instance of :class:`Agent`. An agent owns a system
prompt and a set of tools, and runs a reason-and-act loop against the model:

    1. Ask the model, advertising the agent's tools.
    2. If the model asks to call tools, run them and feed the results back.
    3. Repeat until the model answers in plain text (or a step budget runs out).

Progress is reported through an async ``emit`` callback so the API can stream a
live view of what the agent is doing.
"""

from __future__ import annotations

from typing import Awaitable, Callable

from ..llm import LLMClient
from ..tools.base import Tool

# An emit callback receives one event dict at a time.
EmitFn = Callable[[dict], Awaitable[None]]

MAX_STEPS = 5


class Agent:
    def __init__(
        self,
        name: str,
        description: str,
        system_prompt: str,
        tools: list[Tool] | None = None,
        llm: LLMClient | None = None,
    ):
        self.name = name
        self.description = description
        self.system_prompt = system_prompt
        self.tools = tools or []
        self.llm = llm or LLMClient()
        self._by_name = {t.name: t for t in self.tools}

    async def run(self, query: str, emit: EmitFn) -> str:
        """Answer ``query``, emitting progress events, and return the final text."""
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": query},
        ]
        specs = [t.spec for t in self.tools] or None

        for _ in range(MAX_STEPS):
            message = await self.llm.chat(messages, tools=specs)
            tool_calls = message.get("tool_calls") or []

            if not tool_calls:
                return (message.get("content") or "").strip()

            # Record the model's request to call tools, then execute each one.
            messages.append(message)
            for call in tool_calls:
                fn = call.get("function", {})
                result = await self._run_tool(fn.get("name"), fn.get("arguments", {}), emit)
                messages.append({"role": "tool", "content": result})

        # Out of steps: ask the model for a final answer without tools.
        messages.append({
            "role": "user",
            "content": "Answer now using the information gathered above.",
        })
        message = await self.llm.chat(messages)
        return (message.get("content") or "").strip()

    async def _run_tool(self, name: str | None, args: dict, emit: EmitFn) -> str:
        tool = self._by_name.get(name)
        if tool is None:
            return f"Unknown tool '{name}'."

        await emit({"type": "tool_start", "agent": self.name, "tool": name, "args": args})
        result = tool.run(**args)
        await emit({"type": "tool_end", "agent": self.name, "tool": name, "result": result})
        return result
