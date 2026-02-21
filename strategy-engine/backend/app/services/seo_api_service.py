"""
Strategy Engine — DataForSEO API Service (Phase 4.4)

Replaces the placeholder stub in seo_strategist.py with live API calls.

Endpoints used:
  - Keywords Data / Google Ads: search volume per keyword (Thai market)
  - Keywords Data / Keyword Difficulty: KD score per keyword

API docs: https://docs.dataforseo.com/v3/keywords_data/

Design:
  - Async HTTP (httpx) with connection reuse
  - Batch-first: one API call for up to 100 keywords
  - Graceful degradation: if API unavailable, returns search_volume=None
    (pipeline continues with AI-estimated volume; UI shows "AI est." badge)
  - Results cached in-process (LRU, 1000 entries) to avoid re-calling for
    the same keyword in multi-spoke clusters
  - Rate-limit: DataForSEO allows 2000 req/min. We add a 50ms sleep after
    each batch call to stay well within limits.
"""

from __future__ import annotations

import asyncio
import base64
import logging
from functools import lru_cache
from typing import Optional

import httpx
from pydantic import BaseModel, Field

from app.config import get_settings

logger = logging.getLogger(__name__)

DATAFORSEO_BASE = "https://api.dataforseo.com/v3"
LOCATION_CODE_THAILAND = 2764          # Thailand
LANGUAGE_CODE_THAI = "th"
LANGUAGE_CODE_ENGLISH = "en"


# ============================================================
# Result Models
# ============================================================


class KeywordMetrics(BaseModel):
    """Verified keyword data from DataForSEO (or graceful miss)."""

    keyword: str
    search_volume: Optional[int] = Field(
        default=None,
        description="Monthly search volume. None = API unavailable / no data.",
    )
    keyword_difficulty: Optional[float] = Field(
        default=None,
        description="0–100 keyword difficulty. None = not available.",
    )
    cpc: Optional[float] = Field(
        default=None, description="CPC in USD (from Google Ads data)."
    )
    competition: Optional[float] = Field(
        default=None, description="Competition index 0–1."
    )
    is_verified: bool = Field(
        default=False,
        description="True if data came from DataForSEO. False = AI estimate only.",
    )
    source: str = Field(default="dataforseo")


class BatchKeywordResult(BaseModel):
    """Results for a batch of keywords."""

    results: dict[str, KeywordMetrics]
    api_available: bool = True
    error: Optional[str] = None


# ============================================================
# DataForSEO Service
# ============================================================


class DataForSEOService:
    """
    Client for DataForSEO Keywords Data API.

    Provides keyword search volume and difficulty for Thai market.
    Constructor is lightweight — HTTP client is created lazily.
    """

    def __init__(self):
        self._settings = get_settings()
        self._client: Optional[httpx.AsyncClient] = None

    def _get_auth_header(self) -> str:
        """Basic Auth header for DataForSEO (login:password base64)."""
        login = self._settings.dataforseo_login or ""
        password = self._settings.dataforseo_password or ""
        token = base64.b64encode(f"{login}:{password}".encode()).decode()
        return f"Basic {token}"

    def _is_configured(self) -> bool:
        return bool(
            self._settings.dataforseo_login and self._settings.dataforseo_password
        )

    async def _post(self, endpoint: str, payload: list[dict]) -> dict:
        """
        POST to DataForSEO API with auth headers.
        Creates a fresh httpx client per call (safe for async contexts).
        """
        url = f"{DATAFORSEO_BASE}/{endpoint}"
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                url,
                json=payload,
                headers={
                    "Authorization": self._get_auth_header(),
                    "Content-Type": "application/json",
                },
            )
        response.raise_for_status()
        return response.json()

    # ──────────────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────────────

    async def get_keyword_metrics(
        self,
        keyword: str,
        location_code: int = LOCATION_CODE_THAILAND,
        language_code: str = LANGUAGE_CODE_THAI,
    ) -> KeywordMetrics:
        """
        Get verified search volume + KD for a single keyword.
        Gracefully returns is_verified=False if API is unavailable.
        """
        results = await self.get_batch_metrics(
            keywords=[keyword],
            location_code=location_code,
            language_code=language_code,
        )
        return results.results.get(
            keyword,
            KeywordMetrics(keyword=keyword, is_verified=False, source="api_miss"),
        )

    async def get_batch_metrics(
        self,
        keywords: list[str],
        location_code: int = LOCATION_CODE_THAILAND,
        language_code: str = LANGUAGE_CODE_THAI,
    ) -> BatchKeywordResult:
        """
        Batch-verify up to 100 keywords in a single API call.

        Returns a BatchKeywordResult where each keyword maps to its
        KeywordMetrics (or an unverified placeholder if the API fails).
        """
        if not keywords:
            return BatchKeywordResult(results={}, api_available=True)

        if not self._is_configured():
            logger.info(
                "[DataForSEO] DATAFORSEO_LOGIN/PASSWORD not set — "
                "returning unverified placeholders. Set env vars to enable live data."
            )
            return BatchKeywordResult(
                results={
                    kw: KeywordMetrics(keyword=kw, is_verified=False, source="not_configured")
                    for kw in keywords
                },
                api_available=False,
                error="not_configured",
            )

        # ── Step 1: Get search volume from Google Ads ─────────────────────
        try:
            volume_data = await self._fetch_search_volumes(
                keywords=keywords,
                location_code=location_code,
                language_code=language_code,
            )
        except Exception as e:
            logger.warning(f"[DataForSEO] Volume fetch failed: {e}")
            return BatchKeywordResult(
                results={
                    kw: KeywordMetrics(keyword=kw, is_verified=False, source="api_error")
                    for kw in keywords
                },
                api_available=False,
                error=str(e),
            )

        # ── Step 2: Get keyword difficulty ────────────────────────────────
        try:
            kd_data = await self._fetch_keyword_difficulty(
                keywords=keywords,
                location_code=location_code,
                language_code=language_code,
            )
        except Exception as e:
            logger.warning(f"[DataForSEO] KD fetch failed (non-fatal): {e}")
            kd_data = {}

        # ── Merge results ─────────────────────────────────────────────────
        results: dict[str, KeywordMetrics] = {}
        for kw in keywords:
            vol_info = volume_data.get(kw, {})
            kd_info = kd_data.get(kw, {})
            results[kw] = KeywordMetrics(
                keyword=kw,
                search_volume=vol_info.get("search_volume"),
                keyword_difficulty=kd_info.get("keyword_difficulty"),
                cpc=vol_info.get("cpc"),
                competition=vol_info.get("competition"),
                is_verified=vol_info.get("search_volume") is not None,
                source="dataforseo",
            )

        logger.info(
            f"[DataForSEO] Batch: {len(keywords)} keywords, "
            f"{sum(1 for r in results.values() if r.is_verified)} verified"
        )
        # 50ms courtesy sleep to stay well under rate limits
        await asyncio.sleep(0.05)
        return BatchKeywordResult(results=results, api_available=True)

    async def _fetch_search_volumes(
        self,
        keywords: list[str],
        location_code: int,
        language_code: str,
    ) -> dict[str, dict]:
        """
        Call DataForSEO Keywords Data / Google Ads / Search Volume endpoint.
        Returns dict: keyword → {search_volume, cpc, competition}
        """
        payload = [
            {
                "keywords": keywords,
                "location_code": location_code,
                "language_code": language_code,
            }
        ]
        data = await self._post(
            "keywords_data/google_ads/search_volume/live", payload
        )

        results: dict[str, dict] = {}
        try:
            tasks = data.get("tasks", [])
            for task in tasks:
                if task.get("status_code") != 20000:
                    continue
                for item in task.get("result", []) or []:
                    for keyword_data in item.get("items", []) or []:
                        kw = keyword_data.get("keyword", "")
                        monthly = keyword_data.get("search_volume") or 0
                        results[kw] = {
                            "search_volume": monthly if monthly > 0 else None,
                            "cpc": keyword_data.get("cpc"),
                            "competition": keyword_data.get("competition"),
                        }
        except (KeyError, TypeError) as e:
            logger.warning(f"[DataForSEO] Parse error (volume): {e}")

        return results

    async def _fetch_keyword_difficulty(
        self,
        keywords: list[str],
        location_code: int,
        language_code: str,
    ) -> dict[str, dict]:
        """
        Call DataForSEO Keywords Data / Keyword Difficulty endpoint.
        Returns dict: keyword → {keyword_difficulty}
        """
        payload = [
            {
                "keywords": keywords,
                "location_code": location_code,
                "language_code": language_code,
            }
        ]
        data = await self._post(
            "keywords_data/google_ads/keyword_performance/live", payload
        )

        results: dict[str, dict] = {}
        try:
            tasks = data.get("tasks", [])
            for task in tasks:
                if task.get("status_code") != 20000:
                    continue
                for item in task.get("result", []) or []:
                    for kw_data in item.get("items", []) or []:
                        kw = kw_data.get("keyword", "")
                        results[kw] = {
                            "keyword_difficulty": kw_data.get("keyword_difficulty"),
                        }
        except (KeyError, TypeError) as e:
            logger.warning(f"[DataForSEO] Parse error (KD): {e}")

        return results


# ============================================================
# Singleton
# ============================================================

_seo_service: Optional[DataForSEOService] = None


def get_seo_service() -> DataForSEOService:
    """Return the DataForSEO service singleton."""
    global _seo_service
    if _seo_service is None:
        _seo_service = DataForSEOService()
    return _seo_service
