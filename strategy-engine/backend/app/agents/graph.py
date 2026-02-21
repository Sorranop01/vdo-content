"""
Strategy Engine — LangGraph Orchestrator

Defines the multi-agent pipeline as a LangGraph StateGraph.
Stages: Intent Extraction → SEO/GEO Strategy → Topic Clustering → HITL → Dispatch

Uses TypedDict state for LangGraph compatibility and chains agents
through a compilable graph with proper state transitions.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional, TypedDict, Annotated

from langgraph.graph import StateGraph, END

from app.models.schemas import (
    PipelineState,
    PipelineStatus,
    ContentBlueprintPayload,
    IntentExtractionOutput,
    SEOStrategyOutput,
    ClusterOutput,
)
from app.agents.intent_extractor import extract_intent
from app.agents.seo_strategist import formulate_strategy
from app.agents.cluster_builder import build_cluster
from app.agents.guards import GarbageInputError, get_rag_miss_handler

logger = logging.getLogger(__name__)


# ============================================================
# LangGraph State (TypedDict for graph compatibility)
# ============================================================


class GraphState(TypedDict, total=False):
    """State passed between LangGraph nodes."""

    run_id: str
    status: str
    raw_input: str
    model_used: str

    # Stage outputs
    intent: Optional[IntentExtractionOutput]
    seo_strategy: Optional[SEOStrategyOutput]
    cluster: Optional[ClusterOutput]
    blueprint: Optional[ContentBlueprintPayload]

    # Metadata
    created_at: str
    updated_at: Optional[str]
    error: Optional[str]


# ============================================================
# Node Functions
# ============================================================


async def node_extract_intent(state: GraphState) -> GraphState:
    """Stage 1: Extract persona, pain points, emotions from raw text."""
    run_id = state["run_id"]
    logger.info(f"[Pipeline {run_id}] 🔍 Stage 1: Intent Extraction")

    try:
        result = await extract_intent(
            raw_text=state["raw_input"],
            model=state.get("model_used", "deepseek-chat"),
        )
        return {
            "intent": result,
            "status": PipelineStatus.EXTRACTING_INTENT.value,
            "updated_at": datetime.utcnow().isoformat(),
        }
    except GarbageInputError as e:
        # EC1: Input was rejected by GarbageInputGuard — not an agent failure
        # Use REJECTED status so the UI can show a distinct user-friendly message
        logger.warning(f"[Pipeline {run_id}] EC1 Garbage input: {e.message}")
        return {
            "status": PipelineStatus.REJECTED.value,
            "error": f"Input rejected: {e.reason}",
            "updated_at": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"[Pipeline {run_id}] Stage 1 failed: {e}")
        return {
            "status": PipelineStatus.FAILED.value,
            "error": f"Stage 1 (Intent Extraction) failed: {e}",
            "updated_at": datetime.utcnow().isoformat(),
        }


async def node_formulate_seo(state: GraphState) -> GraphState:
    """Stage 2: Generate SEO/GEO strategy from extracted intent."""
    run_id = state["run_id"]

    if state.get("error"):
        return state

    logger.info(f"[Pipeline {run_id}] 📊 Stage 2: SEO/GEO Strategy")

    try:
        result = await formulate_strategy(
            intent=state["intent"],
            model=state.get("model_used", "deepseek-chat"),
        )
        return {
            "seo_strategy": result,
            "status": PipelineStatus.FORMULATING_SEO.value,
            "updated_at": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"[Pipeline {run_id}] Stage 2 failed: {e}")
        return {
            "status": PipelineStatus.FAILED.value,
            "error": f"Stage 2 (SEO/GEO Strategy) failed: {e}",
            "updated_at": datetime.utcnow().isoformat(),
        }


async def node_build_cluster(state: GraphState) -> GraphState:
    """Stage 3: Build Hub & Spoke topic cluster with internal links + RAG cannibalization check."""
    run_id = state["run_id"]

    if state.get("error"):
        return state

    logger.info(f"[Pipeline {run_id}] 🏗️ Stage 3: Topic Clustering (with RAG)")

    try:
        # --- RAG Step: Check for cannibalization against published content ---
        existing_content = None
        try:
            from app.services.rag_service import get_rag_service

            rag = get_rag_service()
            seo = state["seo_strategy"]
            rag_handler = get_rag_miss_handler()  # EC3

            # Search for content similar to our cluster keyword
            similar = await rag.search_similar(
                query=seo.cluster_primary_keyword,
                limit=5,
                threshold=0.7,
            )

            # EC3: classify the result — handles empty registry and below-threshold
            miss_result = rag_handler.handle(
                similar_items=similar,
                threshold=0.7,
                keyword=seo.cluster_primary_keyword,
            )
            existing_content = rag_handler.build_safe_context(miss_result)
            # existing_content is None on miss → Agent 3 uses internal-links-only strategy

            if existing_content:
                logger.info(
                    f"[Pipeline {run_id}] RAG found {len(existing_content)} items "
                    f"(top: '{existing_content[0]['title']}' at {existing_content[0]['score']:.2f})"
                )
            else:
                logger.info(
                    f"[Pipeline {run_id}] EC3 RAG miss ({miss_result.strategy}): "
                    "no existing content links will be added"
                )

        except Exception as rag_err:
            # RAG is optional — don't fail the pipeline if Qdrant is down
            logger.warning(
                f"[Pipeline {run_id}] RAG check skipped (Qdrant unavailable): {rag_err}"
            )

        # --- Agent 3: Build cluster with RAG context ---
        cluster = await build_cluster(
            intent=state["intent"],
            seo_strategy=state["seo_strategy"],
            existing_content=existing_content,
            model=state.get("model_used", "deepseek-chat"),
        )

        # Assemble the draft blueprint
        intent = state["intent"]
        seo = state["seo_strategy"]

        blueprint = ContentBlueprintPayload(
            target_persona=intent.target_persona,
            core_pain_points=intent.core_pain_points,
            underlying_emotions=intent.underlying_emotions,
            raw_input_snippet=intent.raw_input_snippet,
            hub=cluster.hub,
            spokes=cluster.spokes,
            internal_links=cluster.internal_links,
            cluster_primary_keyword=seo.cluster_primary_keyword,
            estimated_total_search_volume=seo.estimated_total_search_volume,
            pipeline_run_id=run_id,
            agent_model_used=state.get("model_used", "deepseek-chat"),
            cannibalization_checked=existing_content is not None,
            existing_content_links=cluster.existing_content_links,
        )

        return {
            "cluster": cluster,
            "blueprint": blueprint,
            "status": PipelineStatus.AWAITING_REVIEW.value,
            "updated_at": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"[Pipeline {run_id}] Stage 3 failed: {e}")
        return {
            "status": PipelineStatus.FAILED.value,
            "error": f"Stage 3 (Topic Clustering) failed: {e}",
            "updated_at": datetime.utcnow().isoformat(),
        }


# ============================================================
# Conditional Edge: Check for errors
# ============================================================


def should_continue(state: GraphState) -> str:
    """Route to next node or END based on error status."""
    if state.get("error"):
        return "end"
    return "continue"


# ============================================================
# Build the LangGraph
# ============================================================


def build_pipeline_graph() -> StateGraph:
    """
    Build and compile the LangGraph state machine.

    Flow: extract_intent → formulate_seo → build_cluster → END (HITL pause)
    """
    graph = StateGraph(GraphState)

    # Add nodes
    graph.add_node("extract_intent", node_extract_intent)
    graph.add_node("formulate_seo", node_formulate_seo)
    graph.add_node("build_cluster", node_build_cluster)

    # Set entry point
    graph.set_entry_point("extract_intent")

    # Add conditional edges (continue or stop on error)
    graph.add_conditional_edges(
        "extract_intent",
        should_continue,
        {"continue": "formulate_seo", "end": END},
    )
    graph.add_conditional_edges(
        "formulate_seo",
        should_continue,
        {"continue": "build_cluster", "end": END},
    )
    graph.add_edge("build_cluster", END)

    return graph


# Compile once at module level
_compiled_graph = None


def get_compiled_graph():
    """Get or create the compiled pipeline graph (singleton)."""
    global _compiled_graph
    if _compiled_graph is None:
        graph = build_pipeline_graph()
        _compiled_graph = graph.compile()
    return _compiled_graph


# ============================================================
# Public API
# ============================================================


async def run_pipeline(
    raw_input: str,
    model: str = "deepseek-chat",
    run_id: str | None = None,
) -> PipelineState:
    """
    Run the full agent pipeline (Stages 1-3).

    The pipeline PAUSES after Stage 3, returning a draft blueprint
    in AWAITING_REVIEW status for human review via the HITL dashboard.

    Stage 4 (HITL) and Stage 5 (dispatch) are triggered separately
    via the API endpoints.

    Args:
        raw_input: Raw research text from user.
        model: LLM model to use.
        run_id: Optional pre-generated run ID.

    Returns:
        PipelineState with status and generated blueprint.
    """
    import uuid

    if run_id is None:
        run_id = str(uuid.uuid4())

    logger.info(f"[Pipeline {run_id}] 🚀 Starting 3-stage agent pipeline...")

    initial_state: GraphState = {
        "run_id": run_id,
        "status": PipelineStatus.PENDING.value,
        "raw_input": raw_input,
        "model_used": model,
        "intent": None,
        "seo_strategy": None,
        "cluster": None,
        "blueprint": None,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": None,
        "error": None,
    }

    compiled = get_compiled_graph()
    final_state = await compiled.ainvoke(initial_state)

    # Convert graph output back to PipelineState
    pipeline_state = PipelineState(
        run_id=run_id,
        raw_input=raw_input,
        model_used=model,
        status=PipelineStatus(final_state.get("status", "failed")),
        intent=final_state.get("intent"),
        seo_strategy=final_state.get("seo_strategy"),
        cluster=final_state.get("cluster"),
        blueprint=final_state.get("blueprint"),
        error=final_state.get("error"),
    )

    logger.info(
        f"[Pipeline {run_id}] Pipeline finished: status={pipeline_state.status.value}"
    )
    return pipeline_state
