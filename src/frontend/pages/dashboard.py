"""
Dashboard Page -- Analytics and project overview.
"""

import streamlit as st


def render():
    """Dashboard: analytics and project-level metrics."""
    st.title("?? Dashboard")
    st.caption("????????????????? pipeline ????????? prompt")

    st.markdown("---")

    try:
        from src.core.analytics import (
            get_project_stats,
            get_quality_distribution,
            get_recent_projects,
            get_video_type_breakdown,
            get_platform_breakdown,
        )
    except ImportError as e:
        st.error(f"Cannot load analytics module: {e}")
        return

    # ??? Top-level KPIs ???????????????????????????????????????????????????????
    stats = get_project_stats()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("?? Projects", stats["total_projects"])
    col2.metric("?? Scenes", stats["total_scenes"])
    col3.metric("? Prompts Generated", stats["total_prompts_generated"])
    col4.metric(
        "? Avg Quality Score",
        f"{stats['avg_quality_score']:.1f}" if stats["avg_quality_score"] > 0 else "--",
        delta=None,
    )

    st.markdown("---")

    # ??? Quality Distribution ?????????????????????????????????????????????????
    st.subheader("?? Quality Score Distribution")
    quality = get_quality_distribution()

    if quality["scores"]:
        q_col1, q_col2, q_col3, q_col4 = st.columns(4)
        q_col1.metric("?? Excellent (?90)", quality["excellent"], help="Score >= 90")
        q_col2.metric("? Good (80-89)", quality["good"], help="Score 80-89")
        q_col3.metric("?? Fair (70-79)", quality["fair"], help="Score 70-79")
        q_col4.metric("?? Poor (<70)", quality["poor"], help="Score < 70")

        # Simple bar chart
        import json
        scores = quality["scores"]
        # Bucket into 10-point ranges
        buckets = {}
        for score in scores:
            bucket = f"{int(score // 10) * 10}-{int(score // 10) * 10 + 9}"
            buckets[bucket] = buckets.get(bucket, 0) + 1

        # Display as horizontal progress bars
        st.caption(f"Avg: **{quality['avg']}** | Min: {quality['min']} | Max: {quality['max']}")

        for label, count in sorted(buckets.items()):
            total = len(scores)
            pct = count / total if total > 0 else 0
            st.progress(pct, text=f"{label}: {count} prompts ({pct*100:.0f}%)")
    else:
        st.info("?????????????? Quality Score -- ????? Veo Prompts ?? Step 4 ????????????")

    st.markdown("---")

    # ??? Recent Projects ??????????????????????????????????????????????????????
    st.subheader("??? Recent Projects")
    recent = get_recent_projects(limit=10)

    if recent:
        for proj in recent:
            score_badge = (
                f"? {proj['avg_score']}"
                if proj["avg_score"] > 0
                else "--"
            )
            prompt_badge = (
                f"? {proj['prompt_count']}/{proj['scene_count']} Prompts"
                if proj["prompt_count"] > 0
                else f"? {proj['scene_count']} Scenes (no prompts)"
            )
            platforms = ", ".join(proj["platforms"]) if proj["platforms"] else "--"

            with st.expander(f"**{proj['title']}** -- {score_badge} | {prompt_badge}"):
                col_a, col_b = st.columns(2)
                with col_a:
                    st.caption(f"??? Topic: {proj['topic'] or '--'}")
                    st.caption(f"?? Platforms: {platforms}")
                with col_b:
                    st.caption(f"?? Scenes: {proj['scene_count']}")
                    st.caption(f"?? Created: {proj['created_at'][:10] if proj['created_at'] else '--'}")
    else:
        st.info("?????????????????????????? -- ???????????????? Step 1")

    st.markdown("---")

    # ??? Breakdown Charts ?????????????????????????????????????????????????????
    col_vt, col_pl = st.columns(2)

    with col_vt:
        st.subheader("?? Video Type Breakdown")
        vt_data = get_video_type_breakdown()
        if vt_data:
            for vtype, count in sorted(vt_data.items(), key=lambda x: -x[1]):
                label_map = {
                    "with_person": "?? With Person",
                    "no_person": "?? No Person",
                    "mixed": "?? Mixed",
                }
                label = label_map.get(vtype, vtype)
                total = sum(vt_data.values())
                pct = count / total if total > 0 else 0
                st.progress(pct, text=f"{label}: {count} ({pct*100:.0f}%)")
        else:
            st.caption("??????????????")

    with col_pl:
        st.subheader("?? Platform Breakdown")
        pl_data = get_platform_breakdown()
        if pl_data:
            for platform, count in sorted(pl_data.items(), key=lambda x: -x[1]):
                icon_map = {
                    "tiktok": "?? TikTok",
                    "youtube": "?? YouTube",
                    "instagram_reels": "?? Instagram",
                    "youtube_shorts": "?? YT Shorts",
                    "facebook_reels": "?? Facebook",
                }
                label = icon_map.get(platform, platform)
                total = sum(pl_data.values())
                pct = count / total if total > 0 else 0
                st.progress(pct, text=f"{label}: {count} ({pct*100:.0f}%)")
        else:
            st.caption("??????????????")

    st.markdown("---")
    st.caption("?? ?????????????????? projects ??????????? `data/projects/`")
