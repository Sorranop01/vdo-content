# -*- coding: utf-8 -*-
import sys
import os

# Ensure src is in the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from core.prompt_scorer import PromptScorer
from core.script_generator import ScriptGenerator
from pprint import pprint

def test_prompt_scoring():
    print("=== Testing Prompt Scoring ===")
    scorer = PromptScorer(use_ai=False)
    
    good_prompt = "A high quality cinematic shot of a young Thai woman in her 20s, smiling brightly while holding a fresh green apple in a modern, brightly lit kitchen. The camera slowly zooms in. Soft, natural sunlight from the window highlights her face, photorealistic, 4k resolution."
    print("\nGood Prompt:")
    print(good_prompt)
    score_prompt(scorer, good_prompt)
    
    bad_prompt = "A person doing something, maybe eating stuff, whatever. etc."
    print("\nBad Prompt:")
    print(bad_prompt)
    score_prompt(scorer, bad_prompt)

def score_prompt(scorer, prompt):
    score = scorer.score(prompt)
    print(f"Total Score: {score.total_score} (Grade: {score.grade})")
    print(f"Clarity: {score.clarity}/25")
    print(f"Specificity: {score.specificity}/25")
    print(f"Veo Compatibility: {score.veo_compatibility}/25")
    print(f"Visual Richness: {score.visual_richness}/25")
    print(f"Suggestions: {score.suggestions}")
    return score

def test_script_generation():
    print("\n=== Testing Script Generation (Hooks & Closures) ===")
    generator = ScriptGenerator()
    
    if not generator.is_available():
        print("Skipping Script Generation (No API Key or Model Configured)")
        return
        
    topic = "ประโยชน์ของการดื่มน้ำตอนเช้า"
    
    # Test Question Hook + CTA Comment
    print("\n--- Test 1: Hook=question, Closing=cta_comment ---")
    script1 = generator.generate_script(
        topic=topic,
        target_duration=30,  # Short video
        language="th",
        hook_type="question",
        closing_type="cta_comment"
    )
    print("\nGenerated Script 1:")
    print(script1)
    
    # Test Shocking Fact Hook + Tease Next Closing
    print("\n--- Test 2: Hook=shocking_fact, Closing=tease_next ---")
    script2 = generator.generate_script(
        topic=topic,
        target_duration=60,  # Medium video
        language="th",
        hook_type="shocking_fact",
        closing_type="tease_next"
    )
    print("\nGenerated Script 2:")
    print(script2)

if __name__ == '__main__':
    test_prompt_scoring()
    test_script_generation()
