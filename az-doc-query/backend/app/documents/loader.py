"""
Loads sample AZ documents from JSON, chunks them, and feeds them into the vector store.
"""

import json
import os
from pathlib import Path

from app.core.config import get_settings
from app.core.vector_store import DocumentChunk, get_vector_store

settings = get_settings()

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """Split text into overlapping chunks by character count."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
    return chunks


def load_documents() -> int:
    """Load all JSON documents from data/ and index them."""
    store = get_vector_store()
    all_chunks: list[DocumentChunk] = []

    docs_file = DATA_DIR / "documents.json"
    if not docs_file.exists():
        print(f"[Loader] No documents.json found at {docs_file}")
        return 0

    with open(docs_file, "r") as f:
        documents = json.load(f)

    for doc in documents:
        doc_id = doc["id"]
        doc_title = doc["title"]
        doc_type = doc["type"]

        for section in doc.get("sections", []):
            section_title = section.get("title", "General")
            text = section.get("content", "")
            text_chunks = chunk_text(
                text,
                chunk_size=settings.chunk_size,
                chunk_overlap=settings.chunk_overlap,
            )
            for i, chunk_text_str in enumerate(text_chunks):
                all_chunks.append(
                    DocumentChunk(
                        text=chunk_text_str,
                        doc_id=doc_id,
                        doc_title=doc_title,
                        doc_type=doc_type,
                        section=section_title,
                        chunk_index=i,
                    )
                )

    store.build_index(all_chunks)
    print(f"[Loader] Loaded {len(documents)} documents → {len(all_chunks)} chunks")
    return len(all_chunks)
