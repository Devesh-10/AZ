"""
FastAPI Application for DSA LangGraph Backend
Data Quality Lifecycle Agent with Collibra Integration
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uuid

from app.core.config import get_settings
from app.graph import run_query

settings = get_settings()

app = FastAPI(
    title="DSA - Data Quality Lifecycle Agent",
    description="LangGraph-powered DQ lifecycle assistant with Collibra integration",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================
# Request/Response Models
# ==========================================

class ChatRequest(BaseModel):
    question: str
    session_id: Optional[str] = None


class ConnectRequest(BaseModel):
    type: str  # "collibra" | "sap_mdg" | "excel" | "demo"
    url: Optional[str] = None
    token: Optional[str] = None
    community: Optional[str] = None


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
    lifecycle_stages: Optional[list[str]] = None
    is_valid: bool = True
    validation_issues: list[str] = []
    visualization_config: Optional[dict] = None
    generated_sql: Optional[str] = None
    agent_logs: list[AgentLogResponse] = []


class HealthResponse(BaseModel):
    status: str
    version: str


# ==========================================
# Session State
# ==========================================

sessions: dict[str, list] = {}
session_telemetry: dict[str, list] = {}
connected_sources: dict[str, dict] = {}  # session_id -> data_source


# ==========================================
# Health Check
# ==========================================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(status="healthy", version="2.0.0")


# ==========================================
# Data Source Connection
# ==========================================

@app.post("/api/connect")
async def connect_data_source(request: ConnectRequest):
    """Connect to a data source (Collibra, SAP MDG, Excel, or Demo data)."""

    if request.type == "collibra":
        from app.tools.collibra_connector import connect_collibra, get_collibra_catalog, get_collibra_rules, get_collibra_glossary

        connection = connect_collibra(
            url=request.url or "https://astrazeneca.collibra.com",
            token=request.token or "demo-token",
            community=request.community or "Manufacturing Data Quality"
        )

        catalog = get_collibra_catalog()
        rules = get_collibra_rules()
        glossary = get_collibra_glossary()

        data_source = {
            "type": "collibra",
            "name": "Collibra DGC",
            "status": "connected",
            "connection": connection,
            "collibra_assets": catalog,
            "collibra_rules": rules,
            "collibra_glossary": glossary,
            "asset_count": len(catalog),
            "rule_count": len(rules)
        }

        # Store for all sessions (demo: single user)
        connected_sources["default"] = data_source

        return {
            "status": "connected",
            "type": "collibra",
            "name": "Collibra DGC",
            "assets": len(catalog),
            "rules": len(rules),
            "glossary_terms": len(glossary),
            "community": request.community or "Manufacturing Data Quality",
            "domains": connection.get("domains", [])
        }

    elif request.type == "sap_mdg":
        data_source = {
            "type": "sap_mdg",
            "name": "SAP Master Data Governance",
            "status": "connected",
            "collibra_assets": [],
            "collibra_rules": [],
            "asset_count": 14,
            "rule_count": 8
        }
        connected_sources["default"] = data_source
        return {
            "status": "connected",
            "type": "sap_mdg",
            "name": "SAP Master Data Governance",
            "assets": 14,
            "rules": 8
        }

    elif request.type == "demo":
        data_source = {
            "type": "demo",
            "name": "Demo Data (AZ Manufacturing)",
            "status": "connected",
            "collibra_assets": [],
            "collibra_rules": [],
            "asset_count": 14,
            "rule_count": 0
        }
        connected_sources["default"] = data_source
        return {
            "status": "connected",
            "type": "demo",
            "name": "Demo Data (AZ Manufacturing)",
            "assets": 14,
            "rules": 0
        }

    else:
        raise HTTPException(status_code=400, detail=f"Unsupported source type: {request.type}")


@app.get("/api/sources")
async def get_connected_sources():
    """Get the currently connected data source."""
    source = connected_sources.get("default")
    if not source:
        return {"connected": False}
    return {
        "connected": True,
        "type": source["type"],
        "name": source["name"],
        "status": source["status"],
        "asset_count": source.get("asset_count", 0),
        "rule_count": source.get("rule_count", 0)
    }


@app.get("/api/assets")
async def get_data_assets():
    """Get discovered data assets from the connected source."""
    source = connected_sources.get("default")
    if not source:
        raise HTTPException(status_code=404, detail="No data source connected")
    return {
        "assets": source.get("collibra_assets", []),
        "source_type": source["type"],
        "source_name": source["name"]
    }


@app.get("/api/rules")
async def get_dq_rules():
    """Get DQ rules from the connected source."""
    source = connected_sources.get("default")
    if not source:
        raise HTTPException(status_code=404, detail="No data source connected")
    return {
        "rules": source.get("collibra_rules", []),
        "source_type": source["type"]
    }


# ==========================================
# Chat / Query
# ==========================================

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    session_id = request.session_id or str(uuid.uuid4())
    conversation_history = sessions.get(session_id, [])

    # Get connected data source
    data_source = connected_sources.get("default")

    try:
        import asyncio
        result = await asyncio.wait_for(
            run_query(
                session_id=session_id,
                user_query=request.question,
                conversation_history=conversation_history,
                data_source=data_source
            ),
            timeout=120  # 2 minute hard timeout
        )

        answer = result.get("final_answer", "I apologize, but I couldn't generate a response.")

        conversation_history.append({"role": "user", "content": request.question})
        conversation_history.append({"role": "assistant", "content": answer})
        sessions[session_id] = conversation_history[-20:]

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

        if session_id not in session_telemetry:
            session_telemetry[session_id] = []
        session_telemetry[session_id].extend(agent_logs)
        session_telemetry[session_id] = session_telemetry[session_id][-50:]

        return ChatResponse(
            answer=answer,
            session_id=session_id,
            route_type=result.get("route_type"),
            matched_kpi=result.get("matched_kpi"),
            lifecycle_stages=result.get("lifecycle_stages"),
            is_valid=result.get("is_valid", True),
            validation_issues=result.get("validation_issues", []),
            visualization_config=result.get("visualization_config"),
            generated_sql=result.get("generated_sql"),
            agent_logs=agent_logs
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sessions/{session_id}/history")
async def get_session_history(session_id: str):
    history = sessions.get(session_id, [])
    return {"session_id": session_id, "history": history}


@app.get("/api/sessions/{session_id}/telemetry")
async def get_session_telemetry(session_id: str):
    logs = session_telemetry.get(session_id, [])
    return logs


@app.delete("/api/sessions/{session_id}")
async def clear_session(session_id: str):
    if session_id in sessions:
        del sessions[session_id]
    return {"status": "cleared", "session_id": session_id}


@app.get("/api/kpis")
async def list_kpis():
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
