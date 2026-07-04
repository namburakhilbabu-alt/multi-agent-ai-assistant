"""FastAPI application that exposes Maestro over HTTP.

POST /api/chat streams the run as newline-delimited JSON (NDJSON): one event
per line for the routing decision, each tool call, and the final answer.
The frontend reads this stream to animate the agent flow live.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .llm import MODEL, check_health
from .orchestrator import Orchestrator

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

app = FastAPI(title="Maestro", description="A multi-agent AI assistant powered by LangChain.")
orchestrator = Orchestrator()


class ChatRequest(BaseModel):
    message: str


@app.get("/api/health")
async def health() -> dict:
    return {"ok": await check_health(), "model": MODEL}


@app.get("/api/agents")
async def agents() -> dict:
    return {"agents": orchestrator.roster()}


@app.post("/api/chat")
async def chat(request: ChatRequest) -> StreamingResponse:
    """Run the orchestrator and stream every event as NDJSON."""
    queue: asyncio.Queue[dict | None] = asyncio.Queue()

    async def emit(event: dict) -> None:
        await queue.put(event)

    async def run() -> None:
        try:
            await orchestrator.handle(request.message, emit)
        except Exception as exc:
            await queue.put({"type": "error", "message": str(exc)})
        finally:
            await queue.put(None)

    async def stream():
        task = asyncio.create_task(run())
        while True:
            event = await queue.get()
            if event is None:
                break
            yield json.dumps(event) + "\n"
        await task

    return StreamingResponse(stream(), media_type="application/x-ndjson")


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")


app.mount("/", StaticFiles(directory=FRONTEND_DIR), name="static")
