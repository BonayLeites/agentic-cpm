import re
from typing import Any

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tools.base import BaseTool
from app.db.models import Document


class DocumentSearchTool(BaseTool):
    """TF-IDF search over knowledge pack documents."""

    name = "search_documents"
    description = "TF-IDF keyword search over knowledge pack documents"

    def __init__(self) -> None:
        self._vectorizer: TfidfVectorizer | None = None
        self._tfidf_matrix = None
        self._docs: list[dict[str, Any]] = []

    async def initialize(self, session: AsyncSession) -> None:
        """Load documents from DB and build the TF-IDF index."""
        stmt = select(
            Document.id,
            Document.title,
            Document.doc_type,
            Document.content,
        ).order_by(Document.id)

        result = await session.execute(stmt)
        self._docs = [
            {
                "id": row.id,
                "title": row.title,
                "doc_type": row.doc_type,
                "content": row.content,
            }
            for row in result
        ]

        if not self._docs:
            return

        corpus = [doc["content"] for doc in self._docs]
        self._vectorizer = TfidfVectorizer(
            stop_words="english",
            max_features=5000,
        )
        self._tfidf_matrix = self._vectorizer.fit_transform(corpus)

    async def execute(self, params: dict[str, Any], session: AsyncSession) -> dict[str, Any]:  # noqa: ARG002
        query: str = params["query"]
        top_k: int = params.get("top_k", 3)

        if not self._vectorizer or self._tfidf_matrix is None or not self._docs:
            return {"documents": []}

        query_vec = self._vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self._tfidf_matrix).flatten()

        ranked_indices = scores.argsort()[::-1][:top_k]

        documents: list[dict[str, Any]] = []
        for idx in ranked_indices:
            score = float(scores[idx])
            if score <= 0.0:
                continue

            doc = self._docs[idx]
            excerpt = self._extract_excerpt(doc["content"], query)

            documents.append({
                "title": doc["title"],
                "doc_type": doc["doc_type"],
                "relevance_score": round(score, 4),
                "excerpt": excerpt,
            })

        return {"documents": documents}

    def _extract_excerpt(self, content: str, query: str, max_length: int = 300) -> str:
        """Extract the paragraph with the highest keyword overlap with the query."""
        paragraphs = re.split(r"\n\n+", content)
        paragraphs = [p.strip() for p in paragraphs if len(p.strip()) > 20]

        if not paragraphs:
            return content[:max_length]

        query_words = set(query.lower().split())
        best_paragraph = paragraphs[0]
        best_score = 0

        for paragraph in paragraphs:
            paragraph_words = set(paragraph.lower().split())
            overlap = len(query_words & paragraph_words)
            if overlap > best_score:
                best_score = overlap
                best_paragraph = paragraph

        if len(best_paragraph) > max_length:
            return best_paragraph[:max_length].rsplit(" ", 1)[0] + "..."

        return best_paragraph
