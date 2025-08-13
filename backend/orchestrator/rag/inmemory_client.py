"""In-memory RAG client for fast tests.

Provides a small, dependency-free retrieval implementation to avoid FAISS and
model initialization in unit tests.
"""

from __future__ import annotations

from typing import Iterable, List, Dict


class InMemoryRAGClient:
    def __init__(self, corpus: Iterable[str]):
        self._chunks: List[str] = [str(text) for text in corpus]

    def retrieve(self, query: str, k: int = 3) -> List[Dict[str, object]]:
        """Return up to k chunks that contain any query token (case-insensitive)."""
        query_tokens = [t for t in query.lower().split() if t]
        scored: List[tuple[int, str]] = []
        for chunk in self._chunks:
            text = chunk.lower()
            score = sum(1 for t in query_tokens if t in text)
            if score > 0:
                scored.append((score, chunk))
        # Sort by score desc; stable for deterministic tests
        scored.sort(key=lambda x: (-x[0], x[1]))
        results = [
            {"chunk": c, "score": float(s)}
            for s, c in scored[: max(1, k)]
        ]
        # Fallback: if nothing matched, return first k items with minimal score
        if not results:
            results = [{"chunk": c, "score": 0.0} for c in self._chunks[: max(1, k)]]
        return results


