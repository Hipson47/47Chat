"""Utilities to normalize and format RAG retrieval results.

Provides deterministic, testable formatting for context blocks returned
to the frontend, and a normalization helper for robust comparisons.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any, Dict, Iterable, List


class RAGContextFormatter:
    """Helper to normalize text and format RAG retrieval chunks."""

    @staticmethod
    def normalize(text: str) -> str:
        """Normalize text for deterministic comparisons.

        Operations:
        - Remove all control characters (Unicode category 'Cc')
        - Collapse all whitespace to single spaces
        - Strip leading/trailing whitespace
        - Lowercase
        """
        # Remove control characters
        filtered = "".join(ch for ch in text if unicodedata.category(ch) != "Cc")
        # Collapse whitespace
        collapsed = re.sub(r"\s+", " ", filtered)
        # Strip and lowercase
        return collapsed.strip().lower()

    @staticmethod
    def format_chunks(results: Iterable[Dict[str, Any]]) -> str:
        """Format retrieval results as deterministic chunk lines.

        Args:
            results: Iterable of items with keys 'chunk' (str) and 'score' (float)

        Returns:
            A string with one line per chunk in the form:
            Chunk <i>: "<text>" [score: <rounded 3dp>]
        """
        lines: List[str] = []
        for idx, item in enumerate(results, start=1):
            text = str(item.get("chunk", ""))
            score = float(item.get("score", 0.0))
            # Normalize display text for consistency in tests
            disp = RAGContextFormatter.normalize(text)
            lines.append(f"Chunk {idx}: \"{disp}\" [score: {score:.3f}]")
        return "\n".join(lines)


