"""
FastAPI app exposing /api/chat for the MDM Agent.
Sessions are kept in-memory for the POC.
"""
import uuid
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
from pydantic import BaseModel

from app.agents.mdm_agent import get_agent
from app.core.config import get_settings

settings = get_settings()
app = FastAPI(title="MDM Agent", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session store (POC scope)
SESSIONS: dict[str, list[Any]] = {}


class ChatRequest(BaseModel):
    question: str
    session_id: str | None = None


class AgentStep(BaseModel):
    type: str  # "tool_call" | "tool_result" | "ai_message"
    name: str | None = None
    content: str
    args: dict | None = None


class ChatResponse(BaseModel):
    answer: str
    session_id: str
    steps: list[AgentStep] = []


@app.get("/health")
def health():
    return {"status": "ok", "reltio": settings.reltio_base_url}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    session_id = req.session_id or str(uuid.uuid4())
    history = SESSIONS.setdefault(session_id, [])
    history.append(HumanMessage(content=req.question))

    agent = get_agent()
    try:
        result = await agent.ainvoke({"messages": history})
    except Exception as e:
        raise HTTPException(500, f"Agent error: {e}")

    new_messages = result["messages"][len(history) - 1:]  # everything since the user's input
    SESSIONS[session_id] = result["messages"]

    steps: list[AgentStep] = []
    final_answer = ""
    for msg in new_messages:
        if isinstance(msg, AIMessage):
            if msg.tool_calls:
                for tc in msg.tool_calls:
                    steps.append(AgentStep(
                        type="tool_call",
                        name=tc["name"],
                        content="",
                        args=tc.get("args", {}),
                    ))
            if isinstance(msg.content, str) and msg.content.strip():
                steps.append(AgentStep(type="ai_message", name=None, content=msg.content))
                final_answer = msg.content
        elif isinstance(msg, ToolMessage):
            steps.append(AgentStep(
                type="tool_result",
                name=msg.name,
                content=str(msg.content)[:2000],
            ))

    return ChatResponse(answer=final_answer or "(no response)", session_id=session_id, steps=steps)


@app.delete("/api/sessions/{session_id}")
def clear_session(session_id: str):
    SESSIONS.pop(session_id, None)
    return {"status": "cleared"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.host, port=settings.port)
