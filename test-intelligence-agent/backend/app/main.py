"""
FastAPI Application for Test Intelligence Agent Backend
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import asyncio
import io
import json
import uuid

from app.core.config import get_settings
from app.graph import run_test_query, run_test_query_streaming

settings = get_settings()

app = FastAPI(
    title="TIA - Test Intelligence Agent",
    description="LangGraph-powered 7-step AI testing pipeline for R&D platforms",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response models
class TestRunRequest(BaseModel):
    platform: str
    question: str
    session_id: Optional[str] = None


class AgentLogResponse(BaseModel):
    agent_name: str
    step_number: int
    input_summary: str
    output_summary: str
    reasoning_summary: Optional[str]
    status: str
    timestamp: str
    duration_seconds: Optional[float]
    is_conditional: bool
    was_executed: bool


class TestRunResponse(BaseModel):
    session_id: str
    answer: str
    platform: str
    requirements: Optional[list[dict]] = None
    requirements_count: Optional[int] = None
    test_cases: Optional[list[dict]] = None
    test_cases_count: Optional[int] = None
    test_results: Optional[list[dict]] = None
    failure_analyses: Optional[list[dict]] = None
    refactor_suggestions: Optional[list[dict]] = None
    pass_rate: Optional[float] = None
    compliance_status: Optional[str] = None
    visualization_config: Optional[dict] = None
    timing_comparison: Optional[dict] = None
    compliance_report: Optional[dict] = None
    agent_logs: list[AgentLogResponse] = []


class HealthResponse(BaseModel):
    status: str
    version: str


# In-memory session storage
sessions: dict[str, list] = {}
session_telemetry: dict[str, list] = {}


@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(status="healthy", version="1.0.0")


@app.post("/api/test", response_model=TestRunResponse)
async def run_test(request: TestRunRequest):
    """Main test execution endpoint - runs the 7-step LangGraph pipeline."""
    session_id = request.session_id or str(uuid.uuid4())
    conversation_history = sessions.get(session_id, [])

    try:
        result = await run_test_query(
            session_id=session_id,
            user_query=request.question,
            selected_platform=request.platform,
            conversation_history=conversation_history,
        )

        answer = result.get("final_answer", "The test pipeline did not produce a result.")

        # Update session history
        conversation_history.append({"role": "user", "content": request.question})
        conversation_history.append({"role": "assistant", "content": answer})
        sessions[session_id] = conversation_history[-20:]

        # Build agent logs
        agent_logs = []
        for log in result.get("agent_logs", []):
            agent_logs.append(AgentLogResponse(
                agent_name=log.get("agent_name", "Unknown"),
                step_number=log.get("step_number", 0),
                input_summary=log.get("input_summary", ""),
                output_summary=log.get("output_summary", ""),
                reasoning_summary=log.get("reasoning_summary"),
                status=log.get("status", "unknown"),
                timestamp=log.get("timestamp", ""),
                duration_seconds=log.get("duration_seconds"),
                is_conditional=log.get("is_conditional", False),
                was_executed=log.get("was_executed", True),
            ))

        # Store telemetry
        if session_id not in session_telemetry:
            session_telemetry[session_id] = []
        session_telemetry[session_id].extend(agent_logs)
        session_telemetry[session_id] = session_telemetry[session_id][-100:]

        # Extract test results
        test_results = result.get("test_results")
        failure_analyses = result.get("failure_analyses")
        refactor_suggestions = result.get("refactor_suggestions")
        requirements = result.get("requirements")
        test_cases = result.get("test_cases")
        compliance_report = result.get("compliance_report")

        pass_rate = None
        if test_results:
            passed = sum(1 for t in test_results if t.get("status") == "PASS")
            pass_rate = (passed / len(test_results)) * 100 if test_results else None

        return TestRunResponse(
            session_id=session_id,
            answer=answer,
            platform=request.platform,
            requirements=requirements,
            requirements_count=len(requirements) if requirements else None,
            test_cases=test_cases,
            test_cases_count=len(test_cases) if test_cases else None,
            test_results=test_results,
            failure_analyses=failure_analyses,
            refactor_suggestions=refactor_suggestions,
            pass_rate=pass_rate,
            compliance_status=compliance_report.get("compliance_status") if compliance_report else None,
            visualization_config=result.get("visualization_config"),
            timing_comparison=result.get("timing_comparison"),
            compliance_report=compliance_report,
            agent_logs=agent_logs,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/test/stream")
async def run_test_stream(request: TestRunRequest):
    """
    Streaming test execution endpoint using Server-Sent Events (SSE).
    Streams agent progress events as each pipeline step completes,
    keeping the HTTP connection alive to avoid gateway timeouts.
    """
    session_id = request.session_id or str(uuid.uuid4())
    conversation_history = sessions.get(session_id, [])

    queue: asyncio.Queue = asyncio.Queue()

    async def on_agent_complete(event: dict):
        await queue.put(event)

    async def run_pipeline():
        try:
            result = await run_test_query_streaming(
                session_id=session_id,
                user_query=request.question,
                selected_platform=request.platform,
                conversation_history=conversation_history,
                on_agent_complete=on_agent_complete,
            )
            # Send final result
            await queue.put({"type": "final", "result": result})
        except Exception as e:
            await queue.put({"type": "error", "error": str(e)})
        finally:
            await queue.put(None)  # Sentinel to end stream

    async def event_generator():
        task = asyncio.create_task(run_pipeline())

        try:
            while True:
                event = await queue.get()
                if event is None:
                    break

                if event["type"] == "agent_complete":
                    log = event["log"]
                    data = json.dumps({
                        "type": "agent_log",
                        "agent_name": log.get("agent_name", "Unknown"),
                        "step_number": log.get("step_number", 0),
                        "input_summary": log.get("input_summary", ""),
                        "output_summary": log.get("output_summary", ""),
                        "reasoning_summary": log.get("reasoning_summary"),
                        "status": log.get("status", "unknown"),
                        "timestamp": log.get("timestamp", ""),
                        "duration_seconds": log.get("duration_seconds"),
                        "is_conditional": log.get("is_conditional", False),
                        "was_executed": log.get("was_executed", True),
                    })
                    yield f"data: {data}\n\n"

                elif event["type"] == "final":
                    result = event["result"]
                    answer = result.get("final_answer", "The test pipeline did not produce a result.")

                    # Update session
                    conversation_history.append({"role": "user", "content": request.question})
                    conversation_history.append({"role": "assistant", "content": answer})
                    sessions[session_id] = conversation_history[-20:]

                    # Build agent logs
                    agent_logs = []
                    for log in result.get("agent_logs", []):
                        agent_logs.append({
                            "agent_name": log.get("agent_name", "Unknown"),
                            "step_number": log.get("step_number", 0),
                            "input_summary": log.get("input_summary", ""),
                            "output_summary": log.get("output_summary", ""),
                            "reasoning_summary": log.get("reasoning_summary"),
                            "status": log.get("status", "unknown"),
                            "timestamp": log.get("timestamp", ""),
                            "duration_seconds": log.get("duration_seconds"),
                            "is_conditional": log.get("is_conditional", False),
                            "was_executed": log.get("was_executed", True),
                        })

                    # Store telemetry
                    if session_id not in session_telemetry:
                        session_telemetry[session_id] = []
                    session_telemetry[session_id].extend(agent_logs)
                    session_telemetry[session_id] = session_telemetry[session_id][-100:]

                    test_results = result.get("test_results")
                    pass_rate = None
                    if test_results:
                        passed = sum(1 for t in test_results if t.get("status") == "PASS")
                        pass_rate = (passed / len(test_results)) * 100 if test_results else None

                    final_data = json.dumps({
                        "type": "final_result",
                        "session_id": session_id,
                        "answer": answer,
                        "platform": request.platform,
                        "requirements": result.get("requirements"),
                        "requirements_count": len(result.get("requirements") or []) or None,
                        "test_cases": result.get("test_cases"),
                        "test_cases_count": len(result.get("test_cases") or []) or None,
                        "test_results": test_results,
                        "failure_analyses": result.get("failure_analyses"),
                        "refactor_suggestions": result.get("refactor_suggestions"),
                        "pass_rate": pass_rate,
                        "compliance_status": (result.get("compliance_report") or {}).get("compliance_status"),
                        "visualization_config": result.get("visualization_config"),
                        "timing_comparison": result.get("timing_comparison"),
                        "compliance_report": result.get("compliance_report"),
                        "agent_logs": agent_logs,
                    })
                    yield f"data: {final_data}\n\n"

                elif event["type"] == "error":
                    error_data = json.dumps({
                        "type": "error",
                        "error": event.get("error", "Unknown error"),
                    })
                    yield f"data: {error_data}\n\n"

        except asyncio.CancelledError:
            task.cancel()
            raise

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


def _extract_text_from_upload(file: UploadFile) -> str:
    """Extract text content from uploaded file based on extension."""
    filename = file.filename or "unknown"
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    content_bytes = file.file.read()

    if ext == "txt":
        return content_bytes.decode("utf-8", errors="replace")

    if ext == "csv":
        text = content_bytes.decode("utf-8", errors="replace")
        return text

    if ext == "pdf":
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(io.BytesIO(content_bytes))
            pages = []
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    pages.append(extracted)
            return "\n\n".join(pages)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to parse PDF: {str(e)}")

    if ext == "docx":
        try:
            from docx import Document
            doc = Document(io.BytesIO(content_bytes))
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            return "\n\n".join(paragraphs)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to parse DOCX: {str(e)}")

    raise HTTPException(
        status_code=400,
        detail=f"Unsupported file type: .{ext}. Supported: .pdf, .csv, .txt, .docx",
    )


@app.post("/api/test/upload", response_model=TestRunResponse)
async def run_test_with_upload(
    platform: str = Form(...),
    question: str = Form(...),
    session_id: Optional[str] = Form(None),
    file: UploadFile = File(...),
):
    """Run test pipeline with an uploaded requirements document."""
    # Extract text from uploaded file
    document_text = _extract_text_from_upload(file)
    document_name = file.filename or "uploaded_document"

    sid = session_id or str(uuid.uuid4())
    conversation_history = sessions.get(sid, [])

    try:
        result = await run_test_query(
            session_id=sid,
            user_query=question,
            selected_platform=platform,
            conversation_history=conversation_history,
            uploaded_document=document_text,
            uploaded_document_name=document_name,
        )

        answer = result.get("final_answer", "The test pipeline did not produce a result.")

        # Update session history
        conversation_history.append({"role": "user", "content": question})
        conversation_history.append({"role": "assistant", "content": answer})
        sessions[sid] = conversation_history[-20:]

        # Build agent logs
        agent_logs = []
        for log in result.get("agent_logs", []):
            agent_logs.append(AgentLogResponse(
                agent_name=log.get("agent_name", "Unknown"),
                step_number=log.get("step_number", 0),
                input_summary=log.get("input_summary", ""),
                output_summary=log.get("output_summary", ""),
                reasoning_summary=log.get("reasoning_summary"),
                status=log.get("status", "unknown"),
                timestamp=log.get("timestamp", ""),
                duration_seconds=log.get("duration_seconds"),
                is_conditional=log.get("is_conditional", False),
                was_executed=log.get("was_executed", True),
            ))

        # Store telemetry
        if sid not in session_telemetry:
            session_telemetry[sid] = []
        session_telemetry[sid].extend(agent_logs)
        session_telemetry[sid] = session_telemetry[sid][-100:]

        # Extract results
        test_results = result.get("test_results")
        failure_analyses = result.get("failure_analyses")
        refactor_suggestions = result.get("refactor_suggestions")
        requirements = result.get("requirements")
        test_cases = result.get("test_cases")
        compliance_report = result.get("compliance_report")

        pass_rate = None
        if test_results:
            passed = sum(1 for t in test_results if t.get("status") == "PASS")
            pass_rate = (passed / len(test_results)) * 100 if test_results else None

        return TestRunResponse(
            session_id=sid,
            answer=answer,
            platform=platform,
            requirements=requirements,
            requirements_count=len(requirements) if requirements else None,
            test_cases=test_cases,
            test_cases_count=len(test_cases) if test_cases else None,
            test_results=test_results,
            failure_analyses=failure_analyses,
            refactor_suggestions=refactor_suggestions,
            pass_rate=pass_rate,
            compliance_status=compliance_report.get("compliance_status") if compliance_report else None,
            visualization_config=result.get("visualization_config"),
            timing_comparison=result.get("timing_comparison"),
            compliance_report=compliance_report,
            agent_logs=agent_logs,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/platforms")
async def list_platforms():
    """List all 9 platforms with their metadata and metrics."""
    from app.tools.platform_catalogue import PLATFORM_CATALOGUE

    platforms = []
    for pid, info in PLATFORM_CATALOGUE.items():
        platforms.append({
            "id": pid,
            "name": info["name"],
            "description": info.get("description", ""),
            "depth": info["depth"],
            "icon": info.get("icon", "flask"),
            "color": info.get("color", "#7c3a5c"),
            "test_domains": info.get("test_domains", []),
            "sample_queries": info.get("sample_queries", []),
            "metrics": info.get("metrics", {}),
        })

    return {"platforms": platforms}


@app.get("/api/platforms/{platform_id}")
async def get_platform(platform_id: str):
    """Get detailed info for a specific platform."""
    from app.tools.platform_catalogue import PLATFORM_CATALOGUE

    info = PLATFORM_CATALOGUE.get(platform_id)
    if not info:
        raise HTTPException(status_code=404, detail=f"Platform '{platform_id}' not found")

    return {
        "id": platform_id,
        **info,
    }


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
    sessions.pop(session_id, None)
    session_telemetry.pop(session_id, None)
    return {"status": "cleared", "session_id": session_id}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.host, port=settings.port)
