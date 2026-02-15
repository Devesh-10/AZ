"""
Main FastAPI application for Sustainability Insight Agent
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uuid
from datetime import datetime

from app.graph import run_query

app = FastAPI(
    title="Sustainability Insight Agent API",
    description="AI-powered sustainability data analysis using LangGraph",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None


class AgentLogResponse(BaseModel):
    agent_name: str
    input_summary: str
    output_summary: str
    reasoning_summary: Optional[str]
    status: str
    timestamp: str


class QueryResponse(BaseModel):
    session_id: str
    answer: str
    sql: Optional[str] = None
    visualization: Optional[dict] = None
    agent_logs: list[AgentLogResponse] = []


# In-memory session storage (for conversation history)
sessions: dict[str, list] = {}
session_telemetry: dict[str, list] = {}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.post("/api/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """Process a sustainability query through the agent system"""
    try:
        session_id = request.session_id or str(uuid.uuid4())

        # Get conversation history for session
        conversation_history = sessions.get(session_id, [])

        result = await run_query(
            query=request.query,
            session_id=session_id,
            conversation_history=conversation_history
        )

        # Extract answer
        answer = result.get("final_answer", "No response generated")

        # Update session history
        conversation_history.append({"role": "user", "content": request.query})
        conversation_history.append({"role": "assistant", "content": answer})
        sessions[session_id] = conversation_history[-20:]  # Keep last 20 messages

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

        # Store telemetry for this session
        if session_id not in session_telemetry:
            session_telemetry[session_id] = []
        session_telemetry[session_id].extend(agent_logs)
        session_telemetry[session_id] = session_telemetry[session_id][-50:]

        return QueryResponse(
            session_id=session_id,
            answer=answer,
            sql=result.get("generated_sql"),
            visualization=result.get("visualization_config"),
            agent_logs=agent_logs
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sessions/{session_id}/history")
async def get_session_history(session_id: str):
    """Get conversation history for a session"""
    history = sessions.get(session_id, [])
    return {"session_id": session_id, "history": history}


@app.get("/api/sessions/{session_id}/telemetry")
async def get_session_telemetry(session_id: str):
    """Get agent telemetry logs for a session"""
    logs = session_telemetry.get(session_id, [])
    return logs


@app.delete("/api/sessions/{session_id}")
async def clear_session(session_id: str):
    """Clear session history"""
    if session_id in sessions:
        del sessions[session_id]
    if session_id in session_telemetry:
        del session_telemetry[session_id]
    return {"status": "cleared", "session_id": session_id}


@app.get("/api/kpis")
async def list_kpis():
    """List available sustainability KPIs"""
    from app.tools.data_catalogue import KPI_CATALOGUE

    kpis = []
    for kpi_id, info in KPI_CATALOGUE.items():
        kpis.append({
            "id": kpi_id,
            "name": info["name"],
            "description": info["description"],
            "unit": info["unit"],
            "category": info["table"].split("_")[0].lower()
        })

    return {"kpis": kpis}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
