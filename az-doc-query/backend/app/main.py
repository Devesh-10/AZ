"""
FastAPI Application for AZ Document Query — RAG-powered internal document search.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from contextlib import asynccontextmanager
import uuid
import os

from app.core.config import get_settings
from app.core.vector_store import get_vector_store
from app.documents.loader import load_documents

settings = get_settings()

# ── Session store (in-memory for demo) ──────────────────────────────
_sessions: dict[str, list[dict]] = {}


def _get_history(sid: str) -> list[dict]:
    return _sessions.setdefault(sid, [])


# ── Lifespan (load docs on startup) ────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    load_documents()
    yield


app = FastAPI(
    title="AZ Document Query",
    description="RAG-powered internal document search for AstraZeneca",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Models ──────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    question: str
    session_id: Optional[str] = None
    doc_type_filter: Optional[str] = None


class SourceRef(BaseModel):
    doc_title: str
    doc_type: str
    section: str
    relevance: float


class ChatResponse(BaseModel):
    answer: str
    session_id: str
    sources: list[SourceRef] = []


class DocSummary(BaseModel):
    id: str
    title: str
    type: str
    section_count: int


# ── Answer generation ───────────────────────────────────────────────
def _build_answer(question: str, context_chunks: list[dict], history: list[dict]) -> str:
    """
    Build an answer from retrieved context.
    Uses OpenAI if OPENAI_API_KEY is set; otherwise falls back to a
    simple extractive summary so the demo works without any API key.
    """
    context_text = "\n\n---\n\n".join(
        f"[{c['doc_title']} — {c['section']}]\n{c['text']}" for c in context_chunks
    )

    if settings.openai_api_key:
        from openai import OpenAI

        client = OpenAI(api_key=settings.openai_api_key)

        messages = [
            {
                "role": "system",
                "content": (
                    "You are the AstraZeneca Internal Document Assistant. "
                    "Answer the user's question using ONLY the context provided below. "
                    "Cite the document title and section when referencing information. "
                    "If the context does not contain enough information, say so.\n\n"
                    f"CONTEXT:\n{context_text}"
                ),
            }
        ]
        # Add conversation history
        for msg in history[-6:]:
            messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": question})

        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.2,
            max_tokens=1024,
        )
        return resp.choices[0].message.content

    # ── Fallback: extractive summary (no API key needed) ────────────
    if not context_chunks:
        return "I couldn't find any relevant documents for your query. Try rephrasing or broadening your question."

    lines = [
        "**Based on internal AZ documents, here is what I found:**\n",
    ]
    seen_docs = set()
    for chunk in context_chunks[:3]:
        key = (chunk["doc_title"], chunk["section"])
        if key in seen_docs:
            continue
        seen_docs.add(key)
        snippet = chunk["text"][:300].strip()
        if len(chunk["text"]) > 300:
            snippet += "…"
        lines.append(
            f"### {chunk['doc_title']} — {chunk['section']}\n> {snippet}\n"
        )
    lines.append(
        "\n*Set the `OPENAI_API_KEY` environment variable for full generative answers.*"
    )
    return "\n".join(lines)


# ── Endpoints ───────────────────────────────────────────────────────
@app.get("/health")
async def health():
    store = get_vector_store()
    return {
        "status": "healthy",
        "version": "1.0.0",
        "indexed_chunks": len(store.chunks),
    }


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    session_id = request.session_id or str(uuid.uuid4())
    history = _get_history(session_id)
    store = get_vector_store()

    # Retrieve relevant chunks
    results = store.search(request.question, top_k=settings.top_k_results)

    # Optional doc-type filter
    if request.doc_type_filter:
        results = [r for r in results if r["doc_type"] == request.doc_type_filter]

    # Generate answer
    answer = _build_answer(request.question, results, history)

    # Update history
    history.append({"role": "user", "content": request.question})
    history.append({"role": "assistant", "content": answer})

    # Build sources
    sources = []
    seen = set()
    for r in results:
        key = (r["doc_title"], r["section"])
        if key not in seen:
            seen.add(key)
            sources.append(
                SourceRef(
                    doc_title=r["doc_title"],
                    doc_type=r["doc_type"],
                    section=r["section"],
                    relevance=round(r["score"], 3),
                )
            )

    return ChatResponse(answer=answer, session_id=session_id, sources=sources)


@app.get("/api/documents", response_model=list[DocSummary])
async def list_documents():
    """List all indexed documents."""
    import json
    from pathlib import Path

    docs_file = Path(__file__).resolve().parent.parent / "data" / "documents.json"
    if not docs_file.exists():
        return []
    with open(docs_file) as f:
        docs = json.load(f)
    return [
        DocSummary(
            id=d["id"],
            title=d["title"],
            type=d["type"],
            section_count=len(d.get("sections", [])),
        )
        for d in docs
    ]


@app.get("/api/doc-types")
async def list_doc_types():
    """List distinct document types."""
    import json
    from pathlib import Path

    docs_file = Path(__file__).resolve().parent.parent / "data" / "documents.json"
    if not docs_file.exists():
        return {"types": []}
    with open(docs_file) as f:
        docs = json.load(f)
    types = sorted(set(d["type"] for d in docs))
    return {"types": types}


@app.delete("/api/sessions/{session_id}")
async def clear_session(session_id: str):
    _sessions.pop(session_id, None)
    return {"status": "cleared", "session_id": session_id}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.host, port=settings.port)
