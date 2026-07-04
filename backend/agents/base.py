"""Shared LangChain agent runtime.

Every specialist agent is built with LangChain's create_tool_calling_agent
and run via AgentExecutor. The reason-and-act loop is handled by LangChain
internally — tools are called automatically until the model gives a final answer.

Progress is reported through an async emit callback so the API can stream a
live view of what the agent is doing.
"""

from __future__ import annotations

from typing import Awaitable, Callable

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import BaseTool

EmitFn = Callable[[dict], Awaitable[None]]

MAX_ITERATIONS = 5


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

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ])

        lc_agent = create_tool_calling_agent(llm, tools, prompt)
        self._executor = AgentExecutor(
            agent=lc_agent,
            tools=tools,
            max_iterations=MAX_ITERATIONS,
            handle_parsing_errors=True,
            verbose=False,
        )

    async def run(self, query: str, emit: EmitFn) -> str:
        """Run the agent, stream tool events, return the final answer."""
        answer = ""

        async for event in self._executor.astream_events(
            {"input": query}, version="v2"
        ):
            kind = event["event"]
            name = event.get("name", "")
            data = event.get("data", {})

            if kind == "on_tool_start":
                await emit({
                    "type": "tool_start",
                    "agent": self.name,
                    "tool": name,
                    "args": data.get("input", {}),
                })

            elif kind == "on_tool_end":
                output = data.get("output", "")
                result = output.content if hasattr(output, "content") else str(output)
                await emit({
                    "type": "tool_end",
                    "agent": self.name,
                    "tool": name,
                    "result": result,
                })

            elif kind == "on_chain_end" and name == "AgentExecutor":
                # Capture final answer from the AgentExecutor's output
                out = data.get("output", {})
                answer = out.get("output", "") if isinstance(out, dict) else str(out)

        return answer.strip()
