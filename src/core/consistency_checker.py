"""
Visual Consistency Checker
Detects and fixes character/visual drift across scenes in a video project.
"""

import logging
import re
from typing import Optional

logger = logging.getLogger("vdo_content.consistency_checker")


class ConsistencyIssue:
    """A single consistency issue detected between scenes."""

    def __init__(self, scene_order: int, field: str, expected: str, found: str, severity: str = "minor"):
        self.scene_order = scene_order
        self.field = field
        self.expected = expected
        self.found = found
        self.severity = severity    # "critical" | "minor"

    def __str__(self):
        icon = "[CRITICAL]" if self.severity == "critical" else "[MINOR]"
        return f"{icon} Scene {self.scene_order} -- {self.field}: expected '{self.expected}', found '{self.found}'"


class ConsistencyReport:
    """Result of a consistency check across all scenes."""

    def __init__(self, issues: list, scenes_checked: int):
        self.issues = issues
        self.scenes_checked = scenes_checked
        self.critical_count = sum(1 for i in issues if i.severity == "critical")
        self.minor_count = sum(1 for i in issues if i.severity == "minor")

    @property
    def status(self) -> str:
        if not self.issues:
            return "ok"
        if self.critical_count > 0:
            return "critical"
        return "minor"

    @property
    def status_icon(self) -> str:
        icons = {"ok": "[OK]", "critical": "[CRITICAL]", "minor": "[MINOR]"}
        return icons.get(self.status, "[ ]")

    @property
    def summary(self) -> str:
        if not self.issues:
            return f"All {self.scenes_checked} scenes are visually consistent."
        return (
            f"{self.status_icon} Found {len(self.issues)} issue(s) "
            f"({self.critical_count} critical, {self.minor_count} minor) "
            f"in {self.scenes_checked} scenes."
        )

    def issues_for_scene(self, scene_order: int) -> list:
        return [i for i in self.issues if i.scene_order == scene_order]

    def to_display_lines(self) -> list:
        if not self.issues:
            return ["No consistency issues found."]
        return [str(i) for i in self.issues]


# Patterns to extract visual attributes from an English Veo prompt
_ATTRIBUTE_PATTERNS = {
    "hair_color": [
        r"\b(black|brown|blonde|gray|grey|red|dark|light|short|long)\s+hair\b",
    ],
    "hair_length": [
        r"\b(short|long|medium|shoulder-length|cropped)\s+hair\b",
    ],
    "clothing_color": [
        r"\b(?:wearing|dressed\s+in|in\s+a?)\s+(?:a\s+)?([a-z]+(?:-[a-z]+)?)\s+(?:shirt|blouse|top|dress|jacket|t-shirt|tshirt|hoodie|sweater)\b",
    ],
    "ethnicity": [
        r"\b(Thai|Japanese|Korean|Chinese|Western|Southeast\s+Asian|Asian)\s+(?:woman|man|person|girl|boy|female|male)\b",
    ],
    "gender": [
        r"\b(woman|man|girl|boy|female|male|lady|gentleman)\b",
    ],
    "lighting": [
        r"\b(warm|cool|natural|dramatic|soft|bright|dim|golden|harsh|neon)\s+(?:light(?:ing)?|tone)\b",
    ],
}


def extract_visual_attributes(prompt: str) -> dict:
    """Extract key visual attributes from a Veo prompt as a dict."""
    prompt_lower = prompt.lower()
    result = {}
    for attr, patterns in _ATTRIBUTE_PATTERNS.items():
        for pattern in patterns:
            m = re.search(pattern, prompt_lower)
            if m:
                value = m.group(m.lastindex or 0).strip()
                result[attr] = value
                break
    return result


class VisualConsistencyChecker:
    """
    Checks visual consistency across a list of Veo prompts.
    Establishes a baseline from Scene 1 and flags deviations.
    """

    CRITICAL_FIELDS = {"ethnicity", "gender", "hair_color", "hair_length", "clothing_color"}

    def __init__(self, character_reference: str = ""):
        self.character_reference = character_reference

    def check(self, scenes: list, video_type: str = "with_person") -> ConsistencyReport:
        """Check visual consistency across all scenes."""
        prompted_scenes = [s for s in scenes if s.veo_prompt]
        if not prompted_scenes:
            return ConsistencyReport(issues=[], scenes_checked=0)

        if video_type == "no_person":
            return self._check_no_person(prompted_scenes)

        return self._check_with_person(prompted_scenes)

    def _check_with_person(self, scenes: list) -> ConsistencyReport:
        issues = []
        baseline_prompt = scenes[0].veo_prompt
        if self.character_reference:
            baseline_prompt = f"{self.character_reference}. {baseline_prompt}"

        baseline = extract_visual_attributes(baseline_prompt)
        logger.info(f"Consistency baseline (scene 1): {baseline}")

        for scene in scenes[1:]:
            attrs = extract_visual_attributes(scene.veo_prompt)
            for field, baseline_val in baseline.items():
                if field not in attrs:
                    continue
                scene_val = attrs[field]
                if scene_val and scene_val != baseline_val:
                    severity = "critical" if field in self.CRITICAL_FIELDS else "minor"
                    issues.append(ConsistencyIssue(
                        scene_order=scene.order,
                        field=field,
                        expected=baseline_val,
                        found=scene_val,
                        severity=severity,
                    ))
                    logger.info(
                        f"Consistency issue [{severity}] scene {scene.order}: "
                        f"{field} = '{scene_val}' (expected '{baseline_val}')"
                    )
        return ConsistencyReport(issues=issues, scenes_checked=len(scenes))

    def _check_no_person(self, scenes: list) -> ConsistencyReport:
        issues = []
        if not scenes:
            return ConsistencyReport(issues=[], scenes_checked=0)

        baseline = extract_visual_attributes(scenes[0].veo_prompt)
        lighting_baseline = baseline.get("lighting")

        for scene in scenes[1:]:
            attrs = extract_visual_attributes(scene.veo_prompt)
            if lighting_baseline and "lighting" in attrs:
                if attrs["lighting"] != lighting_baseline:
                    issues.append(ConsistencyIssue(
                        scene_order=scene.order,
                        field="lighting",
                        expected=lighting_baseline,
                        found=attrs["lighting"],
                        severity="minor",
                    ))
        return ConsistencyReport(issues=issues, scenes_checked=len(scenes))

    def fix_scene_prompt(
        self,
        prompt: str,
        baseline: dict,
        issues: list,
        llm_client=None,
        model: str = "deepseek-chat",
    ) -> str:
        """Fix a prompt that has consistency issues, using AI or regex fallback."""
        if not issues:
            return prompt
        if llm_client is not None:
            return self._fix_with_ai(prompt, baseline, issues, llm_client, model)
        return self._fix_with_regex(prompt, baseline, issues)

    def _fix_with_regex(self, prompt: str, baseline: dict, issues: list) -> str:
        fixed = prompt
        for issue in issues:
            if issue.field in ("hair_color", "hair_length"):
                fixed = re.sub(
                    rf"\b{re.escape(issue.found)}\s+hair\b",
                    f"{issue.expected} hair",
                    fixed,
                    flags=re.IGNORECASE,
                )
            elif issue.field == "clothing_color":
                fixed = re.sub(
                    rf"\b{re.escape(issue.found)}\s+(shirt|blouse|top|dress|jacket|t-shirt)\b",
                    f"{issue.expected} \\1",
                    fixed,
                    flags=re.IGNORECASE,
                )
        return fixed

    def _fix_with_ai(self, prompt: str, baseline: dict, issues: list, llm_client, model: str) -> str:
        baseline_desc = "; ".join(f"{k}: {v}" for k, v in baseline.items())
        issues_desc = "; ".join(str(i) for i in issues)

        system_prompt = (
            "You are a Visual Continuity Editor for AI video prompts.\n"
            "Fix visual inconsistencies in Veo 3 prompts while preserving action/setting.\n"
            "Output ONLY the corrected prompt. No explanations."
        )
        user_prompt = (
            f"ORIGINAL PROMPT:\n{prompt}\n\n"
            f"CHARACTER BASELINE:\n{baseline_desc}\n\n"
            f"ISSUES TO FIX:\n{issues_desc}\n\n"
            "Rewrite the prompt fixing the visual attributes above:"
        )
        try:
            response = llm_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,
                max_tokens=600,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.warning(f"AI consistency fix failed: {e}")
            return self._fix_with_regex(prompt, baseline, issues)
