"""A lightweight keyword search over local Markdown documents.

This is a deliberately simple, dependency-free stand-in for a vector database.
Documents are split into sections, and sections are scored by how many of the
query's words they contain. It is enough to demonstrate retrieval-augmented
answering without pulling in an embedding model.
"""

from __future__ import annotations

import re
from pathlib import Path

from .base import tool

_KNOWLEDGE_DIR = Path(__file__).resolve().parent.parent / "data" / "knowledge"
_STOPWORDS = {"the", "a", "an", "is", "are", "do", "does", "how", "what", "of",
              "to", "in", "on", "for", "and", "or", "i", "you", "it", "my"}


def _sections() -> list[tuple[str, str]]:
    """Return (heading, body) pairs from every Markdown file."""
    sections: list[tuple[str, str]] = []
    for path in sorted(_KNOWLEDGE_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        # Split on Markdown headings, keeping the heading with its body.
        chunks = re.split(r"\n(?=#{1,6}\s)", text)
        for chunk in chunks:
            chunk = chunk.strip()
            if chunk:
                heading = chunk.splitlines()[0].lstrip("# ").strip()
                sections.append((heading, chunk))
    return sections


def _tokenize(text: str) -> list[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return [w for w in words if w not in _STOPWORDS and len(w) > 1]


def _matches(query_word: str, doc_word: str) -> bool:
    """Loose match so 'agents' finds 'agent' (shared 4+ char stem)."""
    if query_word == doc_word:
        return True
    short, long = sorted((query_word, doc_word), key=len)
    return len(short) >= 4 and long.startswith(short)


@tool(
    description="Search Maestro's local knowledge base of documentation and FAQs. "
    "Use this to answer questions about Maestro, how it works, or how to use it.",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "What to search for."}
        },
        "required": ["query"],
    },
)
def search_knowledge_base(query: str) -> str:
    query_words = set(_tokenize(query))
    if not query_words:
        return "No searchable terms in the query."

    scored = []
    for heading, body in _sections():
        heading_words = _tokenize(heading)
        body_words = _tokenize(body)
        score = 0
        for q in query_words:
            # Term frequency in the body, plus a strong boost for heading matches
            # (a query word appearing in a section title is a good signal).
            score += sum(1 for w in body_words if _matches(q, w))
            score += 5 * sum(1 for w in heading_words if _matches(q, w))
        if score:
            scored.append((score, heading, body))

    if not scored:
        return "No relevant documents found in the knowledge base."

    scored.sort(key=lambda s: s[0], reverse=True)
    top = scored[:3]
    return "\n\n---\n\n".join(body for _, _, body in top)
