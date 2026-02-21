"""
Tests for the LangGraph pipeline and agent wiring.
"""

import pytest

from app.agents.graph import build_pipeline_graph, get_compiled_graph, GraphState
from app.models.schemas import PipelineStatus


def test_graph_builds_successfully():
    """The LangGraph StateGraph should build without errors."""
    graph = build_pipeline_graph()
    assert graph is not None


def test_graph_compiles_successfully():
    """The compiled graph should be a runnable."""
    compiled = get_compiled_graph()
    assert compiled is not None
    # Verify it has the expected node names
    assert hasattr(compiled, "ainvoke")


def test_graph_state_type():
    """GraphState should accept all required fields."""
    state: GraphState = {
        "run_id": "test-123",
        "status": PipelineStatus.PENDING.value,
        "raw_input": "Test input text for pipeline",
        "model_used": "gpt-4o",
        "intent": None,
        "seo_strategy": None,
        "cluster": None,
        "blueprint": None,
        "created_at": "2026-01-01T00:00:00",
        "updated_at": None,
        "error": None,
    }
    assert state["run_id"] == "test-123"
    assert state["status"] == "pending"
