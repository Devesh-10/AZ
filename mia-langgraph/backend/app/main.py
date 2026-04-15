"""
FastAPI Application for MIA LangGraph Backend
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uuid

from app.core.config import get_settings
from app.core.session_store import (
    get_session_history,
    save_session_history,
    delete_session,
)
from app.core.trace_store import get_trace_telemetry
from app.graph import run_query

settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="MIA - Manufacturing Insight Agent",
    description="LangGraph-powered manufacturing analytics assistant",
    version="2.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response models
class ChatRequest(BaseModel):
    question: str
    session_id: Optional[str] = None


class AgentLogResponse(BaseModel):
    agent_name: str
    input_summary: str
    output_summary: str
    reasoning_summary: Optional[str]
    status: str
    timestamp: str


class ChatResponse(BaseModel):
    answer: str
    session_id: str
    route_type: Optional[str] = None
    matched_kpi: Optional[str] = None
    is_valid: bool = True
    validation_issues: list[str] = []
    visualization_config: Optional[dict] = None
    generated_sql: Optional[str] = None
    agent_logs: list[AgentLogResponse] = []


class HealthResponse(BaseModel):
    status: str
    version: str


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(status="healthy", version="2.0.0")


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint for MIA queries.
    """
    # Generate or use provided session ID
    session_id = request.session_id or str(uuid.uuid4())

    # Get conversation history from DynamoDB
    conversation_history = get_session_history(session_id)

    try:
        # Run query through LangGraph
        result = await run_query(
            session_id=session_id,
            user_query=request.question,
            conversation_history=conversation_history
        )

        # Extract response
        answer = result.get("final_answer", "I apologize, but I couldn't generate a response.")

        # Update session history in DynamoDB
        conversation_history.append({"role": "user", "content": request.question})
        conversation_history.append({"role": "assistant", "content": answer})
        save_session_history(session_id, conversation_history)

        # Build agent logs response
        agent_logs = []
        for log in result.get("agent_logs", []):
            agent_logs.append(AgentLogResponse(
                agent_name=log.get("agent_name", "Unknown"),
                input_summary=log.get("input_summary", ""),
                output_summary=log.get("output_summary", ""),
                reasoning_summary=log.get("reasoning_summary"),
                status=log.get("status", "unknown"),
                timestamp=log.get("timestamp", "")
            ))

        return ChatResponse(
            answer=answer,
            session_id=session_id,
            route_type=result.get("route_type"),
            matched_kpi=result.get("matched_kpi"),
            is_valid=result.get("is_valid", True),
            validation_issues=result.get("validation_issues", []),
            visualization_config=result.get("visualization_config"),
            generated_sql=result.get("generated_sql"),
            agent_logs=agent_logs
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sessions/{session_id}/history")
async def fetch_session_history(session_id: str):
    """Get conversation history for a session from DynamoDB"""
    history = get_session_history(session_id)
    return {"session_id": session_id, "history": history}


@app.get("/api/traces/{query_hash}")
async def fetch_trace(query_hash: str):
    """Get LangGraph execution trace by query hash"""
    trace = get_trace_telemetry(query_hash)
    if not trace:
        raise HTTPException(status_code=404, detail="Trace not found")
    return trace


@app.delete("/api/sessions/{session_id}")
async def clear_session(session_id: str):
    """Clear session history from DynamoDB"""
    delete_session(session_id)
    return {"status": "cleared", "session_id": session_id}


@app.get("/api/kpis")
async def list_kpis():
    """List available KPIs"""
    from app.tools.data_catalogue import KPI_CATALOGUE

    kpis = []
    for kpi_id, info in KPI_CATALOGUE.items():
        kpis.append({
            "id": kpi_id,
            "name": info["name"],
            "description": info["description"],
            "unit": info["unit"],
            "target": info.get("target"),
            "aliases": info["aliases"]
        })

    return {"kpis": kpis}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.host, port=settings.port)
