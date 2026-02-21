"""
Strategy Engine — RAG Service (Qdrant + fastembed)

Manages embeddings and similarity search for published content.
Used by Agent 3 for keyword cannibalization detection.

Embeddings: fastembed (BAAI/bge-small-en-v1.5) — local, no API key needed.
Vector DB: Qdrant (self-hosted on Cloud Run).
"""

from __future__ import annotations

import logging
from typing import Optional

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)
from pydantic import BaseModel, Field

from app.config import get_settings

logger = logging.getLogger(__name__)

# ============================================================
# Data Models
# ============================================================

COLLECTION_NAME = "published_content"
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"  # 384 dimensions, local, no API key
EMBEDDING_DIM = 384  # bge-small-en dimensions


class PublishedContent(BaseModel):
    """A piece of published content stored in the vector DB."""

    content_id: str = Field(description="Unique ID for this content")
    url: str = Field(description="Published URL")
    title: str = Field(description="Content title")
    primary_keyword: str = Field(description="Primary SEO keyword")
    all_keywords: list[str] = Field(default_factory=list, description="All keywords")
    content_type: str = Field(default="article", description="video, article, short, etc.")
    summary: str = Field(default="", description="Brief summary for embedding")
    published_date: Optional[str] = Field(default=None, description="ISO date")
    word_count: Optional[int] = Field(default=None)


class SimilarContent(BaseModel):
    """A search result from the vector DB."""

    content_id: str
    url: str
    title: str
    primary_keyword: str
    score: float = Field(description="Cosine similarity score (0-1)")
    content_type: str = ""


# ============================================================
# Embedding via fastembed (local, no API key)
# ============================================================

_embed_model = None


def _get_embed_model():
    """Lazy-load fastembed model (downloads ~100MB on first call)."""
    global _embed_model
    if _embed_model is None:
        from fastembed import TextEmbedding
        _embed_model = TextEmbedding(model_name=EMBEDDING_MODEL)
        logger.info(f"[RAG] Loaded fastembed model: {EMBEDDING_MODEL}")
    return _embed_model


def _embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a list of texts using fastembed (synchronous)."""
    model = _get_embed_model()
    embeddings = list(model.embed(texts))
    return [e.tolist() for e in embeddings]


def _embed_text(text: str) -> list[float]:
    """Embed a single text string."""
    return _embed_texts([text])[0]


# ============================================================
# RAG Service
# ============================================================


class RAGService:
    """Manages vector embeddings and similarity search."""

    def __init__(self):
        self._settings = get_settings()
        self._qdrant: Optional[AsyncQdrantClient] = None

    async def _get_qdrant(self) -> AsyncQdrantClient:
        """Lazy-init Qdrant client."""
        if self._qdrant is None:
            url = self._settings.qdrant_url
            api_key = self._settings.qdrant_api_key
            if api_key:
                self._qdrant = AsyncQdrantClient(url=url, api_key=api_key)
            else:
                self._qdrant = AsyncQdrantClient(url=url)
            logger.info(f"[RAG] Connected to Qdrant at {url}")
        return self._qdrant

    # ----------------------------------------------------------
    # Collection Management
    # ----------------------------------------------------------

    async def ensure_collection(self) -> None:
        """Create the collection if it doesn't exist."""
        client = await self._get_qdrant()

        collections = await client.get_collections()
        existing = [c.name for c in collections.collections]

        if COLLECTION_NAME not in existing:
            await client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=EMBEDDING_DIM,
                    distance=Distance.COSINE,
                ),
            )
            logger.info(f"[RAG] Created collection '{COLLECTION_NAME}' (dim={EMBEDDING_DIM})")
        else:
            logger.debug(f"[RAG] Collection '{COLLECTION_NAME}' already exists")

    # ----------------------------------------------------------
    # Embedding Helpers
    # ----------------------------------------------------------

    def _build_embed_text(self, content: PublishedContent) -> str:
        """Build the text to embed from a PublishedContent item."""
        parts = [content.title, content.primary_keyword]
        if content.summary:
            parts.append(content.summary)
        if content.all_keywords:
            parts.append(", ".join(content.all_keywords))
        return " | ".join(parts)

    # ----------------------------------------------------------
    # Ingest (Store published content)
    # ----------------------------------------------------------

    async def ingest(self, content: PublishedContent) -> str:
        """
        Embed and store a published content item in Qdrant.
        Uses fastembed locally — no OpenAI calls needed.
        """
        await self.ensure_collection()

        embed_text = self._build_embed_text(content)

        # Run fastembed in threadpool to avoid blocking event loop
        import asyncio
        loop = asyncio.get_event_loop()
        vector = await loop.run_in_executor(None, _embed_text, embed_text)

        client = await self._get_qdrant()
        await client.upsert(
            collection_name=COLLECTION_NAME,
            points=[
                PointStruct(
                    id=content.content_id,
                    vector=vector,
                    payload={
                        "content_id": content.content_id,
                        "url": content.url,
                        "title": content.title,
                        "primary_keyword": content.primary_keyword,
                        "all_keywords": content.all_keywords,
                        "content_type": content.content_type,
                        "summary": content.summary,
                        "published_date": content.published_date,
                        "word_count": content.word_count,
                    },
                )
            ],
        )

        logger.info(
            f"[RAG] Ingested: '{content.title}' (keyword: {content.primary_keyword})"
        )
        return content.content_id

    # ----------------------------------------------------------
    # Search (Cannibalization Check)
    # ----------------------------------------------------------

    async def search_similar(
        self,
        query: str,
        limit: int = 5,
        threshold: float = 0.7,
        content_type: Optional[str] = None,
    ) -> list[SimilarContent]:
        """
        Search for published content similar to a query.
        Uses fastembed for the query embedding — no OpenAI calls.
        """
        await self.ensure_collection()

        import asyncio
        loop = asyncio.get_event_loop()
        vector = await loop.run_in_executor(None, _embed_text, query)

        client = await self._get_qdrant()

        query_filter = None
        if content_type:
            query_filter = Filter(
                must=[
                    FieldCondition(
                        key="content_type",
                        match=MatchValue(value=content_type),
                    )
                ]
            )

        results = await client.search(
            collection_name=COLLECTION_NAME,
            query_vector=vector,
            limit=limit,
            score_threshold=threshold,
            query_filter=query_filter,
        )

        similar = [
            SimilarContent(
                content_id=str(r.id),
                url=r.payload.get("url", ""),
                title=r.payload.get("title", ""),
                primary_keyword=r.payload.get("primary_keyword", ""),
                score=r.score,
                content_type=r.payload.get("content_type", ""),
            )
            for r in results
        ]

        logger.info(
            f"[RAG] Search for '{query[:50]}': {len(similar)} results above {threshold}"
        )
        return similar

    async def check_cannibalization(
        self,
        keyword: str,
        threshold: float = 0.85,
    ) -> list[SimilarContent]:
        """Check if a keyword cannibalizes existing published content."""
        return await self.search_similar(
            query=keyword,
            limit=3,
            threshold=threshold,
        )

    # ----------------------------------------------------------
    # List & Delete
    # ----------------------------------------------------------

    async def list_content(self, limit: int = 100) -> list[dict]:
        """List all stored content metadata."""
        await self.ensure_collection()
        client = await self._get_qdrant()

        results = await client.scroll(
            collection_name=COLLECTION_NAME,
            limit=limit,
            with_payload=True,
            with_vectors=False,
        )

        return [point.payload for point in results[0]]

    async def delete_content(self, content_id: str) -> bool:
        """Delete a content item from the vector DB."""
        client = await self._get_qdrant()
        await client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=[content_id],
        )
        logger.info(f"[RAG] Deleted content: {content_id}")
        return True

    async def get_collection_stats(self) -> dict:
        """Get collection statistics."""
        try:
            client = await self._get_qdrant()
            info = await client.get_collection(COLLECTION_NAME)
            return {
                "collection": COLLECTION_NAME,
                "embedding_model": EMBEDDING_MODEL,
                "points_count": info.points_count,
                "vectors_count": info.vectors_count,
                "status": info.status.value,
            }
        except Exception:
            return {
                "collection": COLLECTION_NAME,
                "status": "not_initialized",
                "points_count": 0,
            }


# Singleton
_rag_service: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    """Get or create the RAG service singleton."""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
