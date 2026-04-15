"""
In-memory FAISS vector store for document chunks.
Embeds document chunks using sentence-transformers and indexes them for similarity search.
"""

import os
import json
from typing import Optional
from dataclasses import dataclass

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from app.core.config import get_settings

settings = get_settings()


@dataclass
class DocumentChunk:
    text: str
    doc_id: str
    doc_title: str
    doc_type: str
    section: str
    chunk_index: int


class VectorStore:
    def __init__(self):
        self.model = SentenceTransformer(settings.embedding_model)
        self.chunks: list[DocumentChunk] = []
        self.index: Optional[faiss.IndexFlatIP] = None

    def build_index(self, chunks: list[DocumentChunk]):
        """Embed all chunks and build FAISS index."""
        self.chunks = chunks
        texts = [c.text for c in chunks]
        embeddings = self.model.encode(texts, normalize_embeddings=True, show_progress_bar=True)
        embeddings = np.array(embeddings, dtype="float32")

        dim = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dim)
        self.index.add(embeddings)
        print(f"[VectorStore] Indexed {len(chunks)} chunks (dim={dim})")

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        """Search for most relevant chunks."""
        if self.index is None or len(self.chunks) == 0:
            return []

        query_vec = self.model.encode([query], normalize_embeddings=True)
        query_vec = np.array(query_vec, dtype="float32")

        scores, indices = self.index.search(query_vec, min(top_k, len(self.chunks)))

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:
                continue
            chunk = self.chunks[idx]
            results.append({
                "text": chunk.text,
                "doc_id": chunk.doc_id,
                "doc_title": chunk.doc_title,
                "doc_type": chunk.doc_type,
                "section": chunk.section,
                "score": float(score),
            })
        return results


# Singleton
_store = VectorStore()


def get_vector_store() -> VectorStore:
    return _store
