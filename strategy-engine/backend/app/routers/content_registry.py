"""
Strategy Engine — Content Registry Router

Endpoints for managing published content in the vector DB (Qdrant).
This is the content that Agent 3 checks against for cannibalization.
"""

from __future__ import annotations

import uuid
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.rag_service import (
    get_rag_service,
    PublishedContent,
    SimilarContent,
)

router = APIRouter()
logger = logging.getLogger(__name__)


# ============================================================
# Request / Response Models
# ============================================================


class IngestRequest(BaseModel):
    """Request to add published content to the vector DB."""

    url: str = Field(description="Published URL")
    title: str = Field(description="Content title")
    primary_keyword: str = Field(description="Primary SEO keyword")
    all_keywords: list[str] = Field(default_factory=list)
    content_type: str = Field(default="article")
    summary: str = Field(default="")
    published_date: Optional[str] = Field(default=None)
    word_count: Optional[int] = Field(default=None)


class IngestResponse(BaseModel):
    content_id: str
    message: str


class SearchRequest(BaseModel):
    """Request to search for similar content."""

    query: str = Field(min_length=2, description="Search query (keyword or title)")
    limit: int = Field(default=5, ge=1, le=20)
    threshold: float = Field(default=0.7, ge=0, le=1)
    content_type: Optional[str] = None


class BulkIngestRequest(BaseModel):
    """Request to ingest multiple content items at once."""

    items: list[IngestRequest]


# ============================================================
# Endpoints
# ============================================================


@router.post("/ingest", response_model=IngestResponse)
async def ingest_content(request: IngestRequest):
    """
    Add a published content item to the vector DB.

    This embeds the content and stores it for future RAG queries.
    Use this to register existing published articles, videos, etc.
    """
    rag = get_rag_service()

    content = PublishedContent(
        content_id=str(uuid.uuid4()),
        url=request.url,
        title=request.title,
        primary_keyword=request.primary_keyword,
        all_keywords=request.all_keywords,
        content_type=request.content_type,
        summary=request.summary,
        published_date=request.published_date,
        word_count=request.word_count,
    )

    content_id = await rag.ingest(content)

    return IngestResponse(
        content_id=content_id,
        message=f"Content '{request.title}' ingested successfully",
    )


@router.post("/bulk-ingest")
async def bulk_ingest(request: BulkIngestRequest):
    """Ingest multiple content items at once."""
    rag = get_rag_service()
    results = []

    for item in request.items:
        content = PublishedContent(
            content_id=str(uuid.uuid4()),
            url=item.url,
            title=item.title,
            primary_keyword=item.primary_keyword,
            all_keywords=item.all_keywords,
            content_type=item.content_type,
            summary=item.summary,
            published_date=item.published_date,
            word_count=item.word_count,
        )
        content_id = await rag.ingest(content)
        results.append({"content_id": content_id, "title": item.title})

    return {"ingested": len(results), "items": results}


@router.post("/search", response_model=list[SimilarContent])
async def search_content(request: SearchRequest):
    """
    Search for content similar to a query.

    Use this to manually check for keyword cannibalization
    or find related published content.
    """
    rag = get_rag_service()

    results = await rag.search_similar(
        query=request.query,
        limit=request.limit,
        threshold=request.threshold,
        content_type=request.content_type,
    )

    return results


@router.get("/")
async def list_content():
    """List all published content in the vector DB."""
    rag = get_rag_service()
    items = await rag.list_content()
    return {"count": len(items), "items": items}


@router.delete("/{content_id}")
async def delete_content(content_id: str):
    """Remove a content item from the vector DB."""
    rag = get_rag_service()
    await rag.delete_content(content_id)
    return {"message": f"Content '{content_id}' deleted"}


@router.get("/stats")
async def collection_stats():
    """Get vector DB collection statistics."""
    rag = get_rag_service()
    stats = await rag.get_collection_stats()
    return stats
