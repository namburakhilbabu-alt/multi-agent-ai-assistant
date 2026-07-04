"""Shared agent runtime using LangGraph's create_react_agent.

Each specialist agent is a compiled LangGraph ReAct graph:
  START → agent node (LLM decides) → tools node (runs tools) → loops → END

The graph handles the reason-and-act loop automatically.
We expose invoke() for the orchestrator to call the agent as a tool,
and astream_events() to surface inner tool calls to the UI.
"""

from __future__ import annotations

from typing import Awaitable, Callable

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage
from langchain_core.tools import BaseTool
from langgraph.prebuilt import create_react_agent

EmitFn = Callable[[dict], Awaitable[None]]


class Agent:
    def __init__(
        self,
        name: str,
        description: str,
        system_prompt: str,
        tools: list[BaseTool],
        llm: BaseChatModel,
    ):
        self.name = name
        self.description = description
        # create_react_agent returns a compiled LangGraph StateGraph.
        # prompt= sets the system message; the ReAct loop is wired internally.
        self._graph = create_react_agent(
            model=llm,
            tools=tools,
            prompt=system_prompt,
        )

    def invoke(self, query: str) -> str:
        """Synchronous run — used when an agent is called as a tool by the supervisor."""
        result = self._graph.invoke({"messages": [HumanMessage(content=query)]})
        return result["messages"][-1].content

    async def run(self, query: str, emit: EmitFn) -> str:
        """Async streaming run — streams tool events to the UI, returns final answer."""
        answer = ""

        async for event in self._graph.astream_events(
            {"messages": [HumanMessage(content=query)]},
            version="v2",
        ):
            kind = event["event"]
            tool_name = event.get("name", "")
            data = event.get("data", {})

            if kind == "on_tool_start":
                await emit({
                    "type": "tool_start",
                    "agent": self.name,
                    "tool": tool_name,
                    "args": data.get("input", {}),
                })

            elif kind == "on_tool_end":
                raw = data.get("output", "")
                result = raw.content if hasattr(raw, "content") else str(raw)
                await emit({
                    "type": "tool_end",
                    "agent": self.name,
                    "tool": tool_name,
                    "result": result,
                })

            elif kind == "on_chain_end" and tool_name == "LangGraph":
                messages = data.get("output", {}).get("messages", [])
                if messages:
                    last = messages[-1]
                    answer = last.content if hasattr(last, "content") else str(last)

        return answer.strip()
