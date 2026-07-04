"""The Orchestrator — a supervisor agent built with create_react_agent.

Each specialist agent is wrapped as a LangChain @tool so the supervisor
can call them exactly like any other tool. When a query arrives, the supervisor
LLM reasons about which agent-tool to call, calls it, and returns the answer.

Architecture:
    Supervisor (create_react_agent)
        └─▶ call_math_agent     (tool)  →  Math Agent     (create_react_agent)
        └─▶ call_weather_agent  (tool)  →  Weather Agent  (create_react_agent)
        └─▶ call_research_agent (tool)  →  Research Agent (create_react_agent)
        └─▶ call_writer_agent   (tool)  →  Writer Agent   (create_react_agent)
"""

from __future__ import annotations

from typing import Awaitable, Callable

from langchain_core.messages import HumanMessage
from langchain_core.tools import tool as lc_tool
from langgraph.prebuilt import create_react_agent

from .agents import math_agent, research_agent, weather_agent, writer_agent
from .agents.base import Agent
from .llm import get_llm

EmitFn = Callable[[dict], Awaitable[None]]

# Maps the tool function name → display agent name shown in the UI.
_TOOL_TO_AGENT: dict[str, str] = {
    "call_math_agent":     "Math Agent",
    "call_weather_agent":  "Weather Agent",
    "call_research_agent": "Research Agent",
    "call_writer_agent":   "Writer Agent",
}

SUPERVISOR_PROMPT = (
    "You are Maestro, a supervisor AI. For every user request, call exactly ONE "
    "of the available agent tools to handle it. Never answer directly yourself — "
    "always delegate to an agent tool."
)


class Orchestrator:
    def __init__(self):
        llm = get_llm(temperature=0.0)

        # Build the four specialist agents (each is a create_react_agent graph).
        math    = math_agent.build()
        weather = weather_agent.build()
        research = research_agent.build()
        writer  = writer_agent.build()

        self._agents: dict[str, Agent] = {
            a.name: a for a in [math, weather, research, writer]
        }

        # --- Wrap each agent as a LangChain tool ---
        # The supervisor treats each agent like a tool: it calls the tool with the
        # user's query, the agent runs its own ReAct loop, and the result comes back.

        @lc_tool
        def call_math_agent(query: str) -> str:
            """Handles arithmetic calculations and unit conversions (length, mass, temperature)."""
            return math.invoke(query)

        @lc_tool
        def call_weather_agent(query: str) -> str:
            """Looks up the current live weather and temperature for any city."""
            return weather.invoke(query)

        @lc_tool
        def call_research_agent(query: str) -> str:
            """Answers questions about Maestro — what it is, how it works, how to use or extend it."""
            return research.invoke(query)

        @lc_tool
        def call_writer_agent(query: str) -> str:
            """Drafts, rewrites, summarizes, or translates text."""
            return writer.invoke(query)

        agent_tools = [
            call_math_agent,
            call_weather_agent,
            call_research_agent,
            call_writer_agent,
        ]

        # The supervisor is itself a create_react_agent whose "tools" are the agents.
        self._supervisor = create_react_agent(
            model=llm,
            tools=agent_tools,
            prompt=SUPERVISOR_PROMPT,
        )

    def roster(self) -> list[dict[str, str]]:
        return [{"name": a.name, "description": a.description}
                for a in self._agents.values()]

    async def handle(self, query: str, emit: EmitFn) -> str:
        """Run the supervisor, stream routing + tool events, return the final answer."""
        await emit({"type": "orchestrator_start", "query": query})

        answer = ""

        async for event in self._supervisor.astream_events(
            {"messages": [HumanMessage(content=query)]},
            version="v2",
        ):
            kind = event["event"]
            tool_name = event.get("name", "")
            data = event.get("data", {})

            if kind == "on_tool_start" and tool_name in _TOOL_TO_AGENT:
                # Supervisor just decided which agent to call.
                agent_display = _TOOL_TO_AGENT[tool_name]
                agent = self._agents[agent_display]
                await emit({
                    "type": "route",
                    "agent": agent_display,
                    "description": agent.description,
                })
                await emit({"type": "agent_start", "agent": agent_display})

            elif kind == "on_tool_end" and tool_name in _TOOL_TO_AGENT:
                agent_display = _TOOL_TO_AGENT[tool_name]
                raw = data.get("output", "")
                result = raw.content if hasattr(raw, "content") else str(raw)
                await emit({"type": "agent_end", "agent": agent_display})
                answer = result  # agent's answer is the tool's return value

            elif kind == "on_chain_end" and tool_name == "LangGraph":
                # Final message from the supervisor graph.
                messages = data.get("output", {}).get("messages", [])
                if messages:
                    last = messages[-1]
                    candidate = last.content if hasattr(last, "content") else str(last)
                    if candidate:
                        answer = candidate

        await emit({"type": "final", "answer": answer})
        return answer
