"""
Scene Card component for displaying individual scenes
With prompt quality scoring and voice preview
"""

import streamlit as st
from typing import Callable, Any, Optional


def show_scene_card(
    scene,
    index: int,
    on_copy_prompt: Callable[[str, str], None] = None,
    on_regenerate: Callable[[Any], None] = None,
    on_edit: Callable[[Any, str], None] = None,
    expanded: bool = False,
    show_score: bool = True,
    show_voice: bool = True
):
    """
    Render a scene card with prompt, narration, and actions
    
    Args:
        scene: Scene object
        index: Scene index (0-based)
        on_copy_prompt: Callback when copying prompt
        on_regenerate: Callback when regenerating prompt
        on_edit: Callback when editing scene
        expanded: Whether the expander is initially expanded
        show_score: Whether to show quality score badge
        show_voice: Whether to show voice preview button
    """
    status_icon = "✅" if scene.video_generated else "⏳"
    
    # Get quality score if enabled
    score_badge = ""
    if show_score and scene.veo_prompt:
        try:
            from core.prompt_scorer import PromptScorer, get_score_emoji
            scorer = PromptScorer(use_ai=False)
            score = scorer.score(scene.veo_prompt)
            emoji = get_score_emoji(score.total_score)
            score_badge = f" {emoji} {score.grade}"
        except ImportError:
            pass
    
    with st.expander(f"Scene {scene.order} | {scene.time_range} | {status_icon}{score_badge}", expanded=expanded):
        # Two column layout
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("**🎤 Thai Narration:**")
            st.markdown(f"_{scene.narration_text}_")
            st.caption(f"Duration: {scene.audio_duration:.1f}s | Words: {scene.word_count}")
            
            # Voice preview button
            if show_voice and scene.narration_text:
                if st.button("🔊 Preview", key=f"voice_{scene.scene_id}", use_container_width=True):
                    _play_voice_preview(scene.narration_text, scene.scene_id)
        
        with col2:
            st.markdown("**🎬 Veo 3 Prompt:**")
            if scene.veo_prompt:
                st.code(scene.veo_prompt, language="text")
                
                # Show quality suggestions if score is low
                if show_score:
                    _show_quality_hints(scene.veo_prompt)
            else:
                st.warning("No prompt generated yet")
            
            # Actions row
            action_col1, action_col2 = st.columns(2)
            
            with action_col1:
                if scene.veo_prompt and on_copy_prompt:
                    if st.button("📋 Copy", key=f"copy_{scene.scene_id}", use_container_width=True):
                        on_copy_prompt(scene.veo_prompt, f"prompt_{scene.scene_id}")
            
            with action_col2:
                if on_regenerate:
                    if st.button("🔄 Regenerate", key=f"regen_{scene.scene_id}", use_container_width=True):
                        on_regenerate(scene)


def _play_voice_preview(text: str, scene_id: str):
    """Play voice preview for narration text"""
    try:
        from core.voice_preview import VoicePreview
        
        with st.spinner("Generating preview..."):
            preview = VoicePreview()
            audio_path = preview.generate_preview(text[:200])  # Limit text length
            
            # Display audio player
            audio_bytes = audio_path.read_bytes()
            st.audio(audio_bytes, format="audio/mp3")
    except ImportError:
        st.warning("Voice preview not available. Install: pip install edge-tts")
    except Exception as e:
        st.error(f"Preview error: {e}")


def _show_quality_hints(prompt: str):
    """Show quality improvement hints"""
    try:
        from core.prompt_scorer import PromptScorer
        
        scorer = PromptScorer(use_ai=False)
        score = scorer.score(prompt)
        
        if score.total_score < 60 and score.suggestions:
            with st.popover("💡 Tips"):
                for suggestion in score.suggestions[:2]:
                    st.caption(suggestion)
    except ImportError:
        pass


def show_scene_timeline(scenes: list, current_time: float = 0):
    """
    Render a horizontal timeline of scenes
    
    Args:
        scenes: List of Scene objects
        current_time: Current playback position in seconds
    """
    if not scenes:
        st.info("No scenes available")
        return
    
    total_duration = sum(s.audio_duration for s in scenes)
    
    # Create timeline visualization
    st.markdown("**📊 Timeline:**")
    
    cols = st.columns(len(scenes))
    for i, (col, scene) in enumerate(zip(cols, scenes)):
        with col:
            width_pct = (scene.audio_duration / total_duration) * 100 if total_duration > 0 else 100 / len(scenes)
            status_color = "🟢" if scene.video_generated else "🔴"
            
            # Add score indicator
            score_text = ""
            if scene.veo_prompt:
                try:
                    from core.prompt_scorer import PromptScorer, get_score_emoji
                    scorer = PromptScorer(use_ai=False)
                    score = scorer.score(scene.veo_prompt)
                    score_text = f" {get_score_emoji(score.total_score)}"
                except ImportError:
                    pass
            
            st.caption(f"{status_color}{score_text} Scene {scene.order}")
            st.caption(f"{scene.audio_duration:.1f}s")

