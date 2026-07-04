"""The orchestrator — Maestro's supervisor.

Owns the roster of specialist agents and routes each request to exactly one
agent using an LLM-based select_agent tool call (LangChain style).
Emits events throughout so the whole run can be streamed to the UI.
"""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

from .agents import math_agent, research_agent, weather_agent, writer_agent
from .agents.base import Agent, EmitFn
from .llm import get_llm


class Orchestrator:
    def __init__(self):
        self._llm = get_llm(temperature=0.0)
        self.agents: dict[str, Agent] = {
            agent.name: agent
            for agent in (
                math_agent.build(),
                research_agent.build(),
                weather_agent.build(),
                writer_agent.build(),
            )
        }
        self.default_agent = "Research Agent"

    def roster(self) -> list[dict[str, str]]:
        return [{"name": a.name, "description": a.description} for a in self.agents.values()]

    async def handle(self, query: str, emit: EmitFn) -> str:
        await emit({"type": "orchestrator_start", "query": query})

        agent_name = await self._route(query)
        agent = self.agents[agent_name]

        await emit({"type": "route", "agent": agent.name, "description": agent.description})
        await emit({"type": "agent_start", "agent": agent.name})

        answer = await agent.run(query, emit)

        await emit({"type": "agent_end", "agent": agent.name})
        await emit({"type": "final", "agent": agent.name, "answer": answer})
        return answer

    async def _route(self, query: str) -> str:
        roster = "\n".join(
            f"- {a.name}: {a.description}" for a in self.agents.values()
        )
        names = list(self.agents.keys())

        system = (
            f"You are a router. Given the user's request, reply with ONLY the name "
            f"of the best agent from this list — no other words:\n{roster}"
        )

        try:
            response = await self._llm.ainvoke([
                SystemMessage(content=system),
                HumanMessage(content=query),
            ])
            chosen = response.content.strip()
            # Match to exact agent name
            for name in names:
                if name.lower() in chosen.lower():
                    return name
        except Exception:
            pass

        return self.default_agent
