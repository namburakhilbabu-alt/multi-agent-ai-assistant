"""The orchestrator — Maestro's supervisor.

It owns the roster of specialist agents and, for each request, uses the model to
choose exactly one agent to handle it. Routing is itself a tool call: the model
is given a single ``select_agent`` function whose only argument is an enum of the
available agent names, which makes the decision reliable and easy to parse.

The orchestrator emits events throughout (routing decision, agent start, tool
calls, final answer) so the whole run can be streamed to the UI.
"""

from __future__ import annotations

from .agents import math_agent, research_agent, weather_agent, writer_agent
from .agents.base import Agent, EmitFn
from .llm import LLMClient


class Orchestrator:
    def __init__(self, llm: LLMClient | None = None):
        self.llm = llm or LLMClient()
        self.agents: dict[str, Agent] = {
            agent.name: agent
            for agent in (
                math_agent.build(),
                research_agent.build(),
                weather_agent.build(),
                writer_agent.build(),
            )
        }
        # If routing fails to return a choice, fall back to the Research Agent:
        # such cases are almost always "what is / how do I" questions about
        # Maestro, which it answers from the knowledge base.
        self.default_agent = "Research Agent"

    def roster(self) -> list[dict[str, str]]:
        return [{"name": a.name, "description": a.description} for a in self.agents.values()]

    async def handle(self, query: str, emit: EmitFn) -> str:
        """Route ``query`` to an agent, run it, and return the final answer."""
        await emit({"type": "orchestrator_start", "query": query})

        agent_name = await self._route(query)
        agent = self.agents[agent_name]
        await emit({
            "type": "route",
            "agent": agent.name,
            "description": agent.description,
        })

        await emit({"type": "agent_start", "agent": agent.name})
        answer = await agent.run(query, emit)
        await emit({"type": "agent_end", "agent": agent.name})

        await emit({"type": "final", "agent": agent.name, "answer": answer})
        return answer

    async def _route(self, query: str) -> str:
        names = list(self.agents)
        roster = "\n".join(f"- {a.name}: {a.description}" for a in self.agents.values())

        select_tool = {
            "type": "function",
            "function": {
                "name": "select_agent",
                "description": "Choose the single best agent to handle the request.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "agent": {"type": "string", "enum": names},
                    },
                    "required": ["agent"],
                },
            },
        }

        messages = [
            {
                "role": "system",
                "content": (
                    "Call select_agent to route the user's request to exactly one "
                    "agent. Do not answer the request yourself.\n\nAgents:\n" + roster
                ),
            },
            {"role": "user", "content": query},
        ]

        message = await self.llm.chat(messages, tools=[select_tool])
        for call in message.get("tool_calls") or []:
            chosen = call.get("function", {}).get("arguments", {}).get("agent")
            if chosen in self.agents:
                return chosen
        return self.default_agent
