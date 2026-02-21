"""
Tests for DataForSEO Service (Phase 4.4)

Covers:
  - Graceful degradation when API is not configured (returns is_verified=False)
  - Batch metrics parsing with mocked API responses
  - Single keyword metric fallback
  - API failure → non-fatal degradation (pipeline continues)
  - Auth header construction
  - Result structure validation (KeywordMetrics, BatchKeywordResult)
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.seo_api_service import (
    BatchKeywordResult,
    DataForSEOService,
    KeywordMetrics,
    get_seo_service,
)


# ============================================================
# Fixtures
# ============================================================


def _make_settings(login=None, password=None):
    s = MagicMock()
    s.dataforseo_login = login
    s.dataforseo_password = password
    return s


def _make_volume_response(keywords: list[str], volumes: dict[str, int]) -> dict:
    """Build a DataForSEO-shaped volume response."""
    items = [
        {
            "keyword": kw,
            "search_volume": volumes.get(kw, 0),
            "cpc": 0.5,
            "competition": 0.3,
        }
        for kw in keywords
    ]
    return {
        "tasks": [
            {"status_code": 20000, "result": [{"items": items}]}
        ]
    }


def _make_kd_response(keywords: list[str], kds: dict[str, float]) -> dict:
    """Build a DataForSEO-shaped KD response."""
    items = [
        {"keyword": kw, "keyword_difficulty": kds.get(kw, 0.0)}
        for kw in keywords
    ]
    return {
        "tasks": [
            {"status_code": 20000, "result": [{"items": items}]}
        ]
    }


# ============================================================
# Tests
# ============================================================


class TestDataForSEOServiceNotConfigured:
    @pytest.mark.asyncio
    async def test_returns_unverified_when_not_configured(self):
        """If DATAFORSEO_LOGIN/PASSWORD not set, returns graceful placeholder."""
        with patch("app.services.seo_api_service.get_settings", return_value=_make_settings()):
            svc = DataForSEOService()
            result = await svc.get_batch_metrics(["เก้าอี้ทำงาน คนตัวเล็ก"])

        assert not result.api_available
        assert result.error == "not_configured"
        metric = result.results["เก้าอี้ทำงาน คนตัวเล็ก"]
        assert metric.is_verified is False
        assert metric.search_volume is None

    @pytest.mark.asyncio
    async def test_single_keyword_not_configured_returns_unverified(self):
        with patch("app.services.seo_api_service.get_settings", return_value=_make_settings()):
            svc = DataForSEOService()
            metric = await svc.get_keyword_metrics("test keyword")

        assert metric.is_verified is False
        assert metric.keyword == "test keyword"

    @pytest.mark.asyncio
    async def test_empty_keywords_returns_empty_result(self):
        with patch("app.services.seo_api_service.get_settings", return_value=_make_settings("u", "p")):
            svc = DataForSEOService()
            result = await svc.get_batch_metrics([])

        assert result.results == {}
        assert result.api_available is True


class TestDataForSEOServiceConfigured:
    @pytest.mark.asyncio
    async def test_batch_returns_verified_metrics(self):
        """Mocked API returns correct volume + KD, results are marked verified."""
        keywords = ["เก้าอี้ทำงาน คนตัวเล็ก", "ergonomic chair petite"]
        volumes = {"เก้าอี้ทำงาน คนตัวเล็ก": 1200, "ergonomic chair petite": 500}
        kds = {"เก้าอี้ทำงาน คนตัวเล็ก": 34.5, "ergonomic chair petite": 55.0}

        vol_resp = _make_volume_response(keywords, volumes)
        kd_resp = _make_kd_response(keywords, kds)

        settings = _make_settings("user@test.com", "pass123")
        with patch("app.services.seo_api_service.get_settings", return_value=settings):
            with patch("app.services.seo_api_service.asyncio.sleep", new_callable=AsyncMock):
                svc = DataForSEOService()
                with patch.object(
                    svc, "_post", new_callable=AsyncMock,
                    side_effect=[vol_resp, kd_resp]
                ):
                    result = await svc.get_batch_metrics(keywords)

        assert result.api_available is True
        th_metric = result.results["เก้าอี้ทำงาน คนตัวเล็ก"]
        assert th_metric.is_verified is True
        assert th_metric.search_volume == 1200
        assert th_metric.keyword_difficulty == 34.5

    @pytest.mark.asyncio
    async def test_zero_volume_returns_none(self):
        """Keywords with 0 volume should have search_volume = None (not 0)."""
        keywords = ["ไม่มีคนหา"]
        vol_resp = _make_volume_response(keywords, {"ไม่มีคนหา": 0})
        kd_resp = _make_kd_response(keywords, {})

        settings = _make_settings("u", "p")
        with patch("app.services.seo_api_service.get_settings", return_value=settings):
            with patch("app.services.seo_api_service.asyncio.sleep", new_callable=AsyncMock):
                svc = DataForSEOService()
                with patch.object(svc, "_post", new_callable=AsyncMock, side_effect=[vol_resp, kd_resp]):
                    result = await svc.get_batch_metrics(keywords)

        assert result.results["ไม่มีคนหา"].search_volume is None

    @pytest.mark.asyncio
    async def test_api_failure_returns_graceful_degradation(self):
        """If the API call raises, returns is_verified=False for all keywords."""
        settings = _make_settings("u", "p")
        with patch("app.services.seo_api_service.get_settings", return_value=settings):
            svc = DataForSEOService()
            with patch.object(svc, "_post", new_callable=AsyncMock, side_effect=Exception("connection refused")):
                result = await svc.get_batch_metrics(["keyword1"])

        assert not result.api_available
        assert result.results["keyword1"].is_verified is False

    @pytest.mark.asyncio
    async def test_kd_failure_is_non_fatal(self):
        """KD fetch failure should NOT abort the entire batch call."""
        keywords = ["test kw"]
        vol_resp = _make_volume_response(keywords, {"test kw": 800})

        settings = _make_settings("u", "p")
        with patch("app.services.seo_api_service.get_settings", return_value=settings):
            with patch("app.services.seo_api_service.asyncio.sleep", new_callable=AsyncMock):
                svc = DataForSEOService()
                # Volume succeeds, KD raises
                with patch.object(
                    svc, "_post", new_callable=AsyncMock,
                    side_effect=[vol_resp, Exception("KD timeout")]
                ):
                    result = await svc.get_batch_metrics(keywords)

        # Still returns verified volume despite KD failure
        assert result.api_available is True
        assert result.results["test kw"].search_volume == 800
        assert result.results["test kw"].keyword_difficulty is None

    def test_auth_header_is_base64_encoded(self):
        """Authorization header should be valid Basic Auth."""
        import base64
        settings = _make_settings("user@dataforseo.com", "mysecretpassword")
        with patch("app.services.seo_api_service.get_settings", return_value=settings):
            svc = DataForSEOService()
            header = svc._get_auth_header()

        assert header.startswith("Basic ")
        decoded = base64.b64decode(header[6:]).decode()
        assert decoded == "user@dataforseo.com:mysecretpassword"

    def test_keyword_metrics_defaults(self):
        """KeywordMetrics with no data should have safe defaults."""
        m = KeywordMetrics(keyword="test")
        assert m.search_volume is None
        assert m.keyword_difficulty is None
        assert m.is_verified is False


class TestGetSeoServiceSingleton:
    def test_get_seo_service_returns_singleton(self):
        """get_seo_service() should return the same instance."""
        # Reset singleton via module access
        import app.services.seo_api_service as mod
        mod._seo_service = None

        with patch("app.services.seo_api_service.get_settings", return_value=_make_settings()):
            a = get_seo_service()
            b = get_seo_service()

        assert a is b
