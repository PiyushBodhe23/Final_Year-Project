"""Local RAG over short guideline notes.

sklearn TF-IDF is used so the demo needs no extra vector database. Chunks are
the markdown files in docs/guidelines. Retrieval is lexical, not generative.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from backend.app.core.config import GUIDELINES_DIR, RAG_TOP_K


@dataclass(frozen=True)
class Passage:
    """One retrieved guideline chunk."""

    source: str
    title: str
    text: str
    score: float


def _split_markdown(text: str, filename: str) -> list[tuple[str, str]]:
    """Split a file on headings so each section is its own chunk."""
    title = filename.replace(".md", "").replace("-", " ")
    parts: list[tuple[str, str]] = []
    current_title = title
    current: list[str] = []
    for line in text.splitlines():
        if line.startswith("#"):
            if current:
                parts.append((current_title, "\n".join(current).strip()))
            current_title = line.lstrip("# ").strip() or title
            current = []
        else:
            current.append(line)
    if current:
        parts.append((current_title, "\n".join(current).strip()))
    return [(heading, body) for heading, body in parts if len(body) > 40]


@lru_cache(maxsize=1)
def _index() -> tuple[TfidfVectorizer, object, list[tuple[str, str, str]]]:
    """Fit TF-IDF once per process. Rebuilds when the process restarts."""
    records: list[tuple[str, str, str]] = []
    GUIDELINES_DIR.mkdir(parents=True, exist_ok=True)
    for path in sorted(GUIDELINES_DIR.glob("*.md")):
        for heading, body in _split_markdown(path.read_text(encoding="utf-8"), path.name):
            records.append((path.name, heading, body))
    if not records:
        raise RuntimeError("No guideline markdown files in docs/guidelines.")
    corpus = [f"{heading}\n{body}" for _, heading, body in records]
    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
    matrix = vectorizer.fit_transform(corpus)
    return vectorizer, matrix, records


def retrieve(query: str, k: int = RAG_TOP_K) -> list[Passage]:
    """Return the top-k guideline passages for this question."""
    vectorizer, matrix, records = _index()
    scores = cosine_similarity(vectorizer.transform([query]), matrix).ravel()
    order = scores.argsort()[::-1][:k]
    passages: list[Passage] = []
    for index in order:
        if scores[index] <= 0:
            continue
        source, title, text = records[index]
        passages.append(Passage(source=source, title=title, text=text, score=float(scores[index])))
    return passages
