"""Generator, Reflector, and Curator components (local copy)."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from .delta import DeltaBatch
from .llm_base import LLMClient
from .playbook import Playbook
from .prompts import CURATOR_PROMPT, GENERATOR_PROMPT, REFLECTOR_PROMPT

logger = logging.getLogger(__name__)


def _safe_json_loads(text: str) -> Dict[str, Any]:
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        debug_path = Path("logs/json_failures.log")
        debug_path.parent.mkdir(parents=True, exist_ok=True)
        with debug_path.open("a", encoding="utf-8") as fh:
            fh.write("----\n")
            fh.write(repr(text))
            fh.write("\n")
        raise ValueError(f"LLM response is not valid JSON: {exc}\n{text}") from exc
    if not isinstance(data, dict):
        raise ValueError("Expected a JSON object from LLM.")
    return data


def _format_optional(value: Optional[str]) -> str:
    return value or "(none)"


@dataclass
class GeneratorOutput:
    reasoning: str
    final_answer: str
    bullet_ids: List[str]
    raw: Dict[str, Any]


class Generator:
    """Produces trajectories using the current playbook."""

    def __init__(
        self,
        llm: LLMClient,
        prompt_template: str = GENERATOR_PROMPT,
        *,
        max_retries: int = 3,
    ) -> None:
        self.llm = llm
        self.prompt_template = prompt_template
        self.max_retries = max_retries

    def generate(
        self,
        *,
        question: str,
        context: Optional[str],
        playbook: Playbook,
        reflection: Optional[str] = None,
        answer_format: Optional[str] = None,
        **kwargs: Any,
    ) -> GeneratorOutput:
        logger.info("[Generator] Starting generation...")
        base_prompt = self.prompt_template.format(
            playbook=playbook.as_prompt() or "(empty playbook)",
            reflection=_format_optional(reflection),
            question=question,
            context=_format_optional(context),
            answer_format=_format_optional(answer_format),
        )
        prompt = base_prompt
        # logger.info(f"[Generator] Prompt: {prompt}")
        logger.info(f"[Playbook]: {playbook.as_prompt()}")
        last_error: Optional[Exception] = None
        for attempt in range(self.max_retries):
            response = self.llm.complete(prompt, **kwargs)
            try:
                data = _safe_json_loads(response.text)
                reasoning = str(data.get("reasoning", ""))
                final_answer = str(data.get("final_answer", ""))
                bullet_ids = [
                    str(item)
                    for item in data.get("bullet_ids", [])
                    if isinstance(item, (str, int))
                ]
                logger.info(f"[Generator] Completed successfully. Final answer: {final_answer[:100]}...")
                return GeneratorOutput(
                    reasoning=reasoning,
                    final_answer=final_answer,
                    bullet_ids=bullet_ids,
                    raw=data,
                )
            except ValueError as err:
                last_error = err
                if attempt + 1 >= self.max_retries:
                    break
                prompt = (
                    base_prompt
                    + "\n\nPlease output only a single valid JSON object. "
                    "Escape all quotes or use single quotes, and avoid any extra text."
                )
        logger.error(f"[Generator] Failed after {self.max_retries} attempts - returning fallback response")
        logger.error(f"[Generator] Last error: {last_error}")
        
        # Return a fallback response to continue training
        fallback_data = {
            "reasoning": "Generator failed to produce valid JSON - using fallback response",
            "final_answer": "Not answerable (Generator error)",
            "bullet_ids": []
        }
        return GeneratorOutput(
            reasoning=fallback_data["reasoning"],
            final_answer=fallback_data["final_answer"],
            bullet_ids=fallback_data["bullet_ids"],
            raw=fallback_data
        )


@dataclass
class BulletTag:
    id: str
    tag: str


@dataclass
class ReflectorOutput:
    reasoning: str
    error_identification: str
    root_cause_analysis: str
    correct_approach: str
    key_insight: str
    bullet_tags: List[BulletTag]
    raw: Dict[str, Any]


class Reflector:
    """Extracts lessons and bullet feedback from trajectories."""

    def __init__(
        self,
        llm: LLMClient,
        prompt_template: str = REFLECTOR_PROMPT,
        *,
        max_retries: int = 3,
    ) -> None:
        self.llm = llm
        self.prompt_template = prompt_template
        self.max_retries = max_retries

    def reflect(
        self,
        *,
        question: str,
        generator_output: GeneratorOutput,
        playbook: Playbook,
        ground_truth: Optional[str],
        feedback: Optional[str],
        max_refinement_rounds: int = 1,
        **kwargs: Any,
    ) -> ReflectorOutput:
        logger.info("[Reflector] Starting reflection...")
        logger.info(f"[Reflector] Ground truth: {ground_truth if ground_truth else '(none)'}")
        playbook_excerpt = _make_playbook_excerpt(playbook, generator_output.bullet_ids)
        base_prompt = self.prompt_template.format(
            question=question,
            reasoning=generator_output.reasoning,
            prediction=generator_output.final_answer,
            ground_truth=_format_optional(ground_truth),
            feedback=_format_optional(feedback),
            playbook_excerpt=playbook_excerpt or "(no bullets referenced)",
        )
        # logger.info("=" * 80)
        # logger.info("[Reflector] PROMPT:")
        # logger.info(base_prompt)
        # logger.info("=" * 80)
        result: Optional[ReflectorOutput] = None
        prompt = base_prompt
        last_error: Optional[Exception] = None
        for round_idx in range(max_refinement_rounds):
            prompt = base_prompt
            for attempt in range(self.max_retries):
                response = self.llm.complete(
                    prompt, refinement_round=round_idx, **kwargs
                )
                try:
                    data = _safe_json_loads(response.text)
                    bullet_tags: List[BulletTag] = []
                    tags_payload = data.get("bullet_tags", [])
                    if isinstance(tags_payload, Sequence):
                        for item in tags_payload:
                            if isinstance(item, dict) and "id" in item and "tag" in item:
                                bullet_tags.append(
                                    BulletTag(
                                        id=str(item["id"]), tag=str(item["tag"]).lower()
                                    )
                                )
                    candidate = ReflectorOutput(
                        reasoning=str(data.get("reasoning", "")),
                        error_identification=str(data.get("error_identification", "")),
                        root_cause_analysis=str(data.get("root_cause_analysis", "")),
                        correct_approach=str(data.get("correct_approach", "")),
                        key_insight=str(data.get("key_insight", "")),
                        bullet_tags=bullet_tags,
                        raw=data,
                    )
                    result = candidate
                    if bullet_tags or candidate.key_insight:
                        logger.info(f"[Reflector] Completed successfully. Key insight: {candidate.key_insight[:100] if candidate.key_insight else '(none)'}...")
                        return candidate
                    break
                except ValueError as err:
                    last_error = err
                    if attempt + 1 >= self.max_retries:
                        break
                    prompt = (
                        base_prompt
                        + "\n\nPlease strictly output valid JSON, escape double quotes, "
                        "and do not output any additional explanatory text."
                    )
        if result is None:
            logger.error(f"[Reflector] Failed after {self.max_retries} attempts - returning fallback reflection")
            logger.error(f"[Reflector] Last error: {last_error}")
            
            # Return a fallback reflection to continue training
            fallback_data = {
                "reasoning": "Reflector failed to produce valid JSON - using fallback reflection",
                "error_identification": "JSON parsing error in reflector",
                "root_cause_analysis": "LLM output was not valid JSON",
                "correct_approach": "Ensure JSON output format is correct",
                "key_insight": "Handle JSON parsing errors gracefully to continue training",
                "bullet_tags": []
            }
            result = ReflectorOutput(
                reasoning=fallback_data["reasoning"],
                error_identification=fallback_data["error_identification"],
                root_cause_analysis=fallback_data["root_cause_analysis"],
                correct_approach=fallback_data["correct_approach"],
                key_insight=fallback_data["key_insight"],
                bullet_tags=[],
                raw=fallback_data
            )
        logger.info("[Reflector] Completed (no key insights found, but valid result)")
        return result


@dataclass
class CuratorOutput:
    delta: DeltaBatch
    raw: Dict[str, Any]


class Curator:
    """Transforms reflections into delta updates."""

    def __init__(
        self,
        llm: LLMClient,
        prompt_template: str = CURATOR_PROMPT,
        *,
        max_retries: int = 3,
    ) -> None:
        self.llm = llm
        self.prompt_template = prompt_template
        self.max_retries = max_retries

    def curate(
        self,
        *,
        reflection: ReflectorOutput,
        playbook: Playbook,
        question_context: str,
        progress: str,
        **kwargs: Any,
    ) -> CuratorOutput:
        logger.info("[Curator] Starting curation...")
        base_prompt = self.prompt_template.format(
            progress=progress,
            stats=json.dumps(playbook.stats()),
            reflection=json.dumps(reflection.raw, ensure_ascii=False, indent=2),
            playbook=playbook.as_prompt() or "(empty playbook)",
            question_context=question_context,
        )
        prompt = base_prompt
        last_error: Optional[Exception] = None
        for attempt in range(self.max_retries):
            response = self.llm.complete(prompt, **kwargs)
            try:
                data = _safe_json_loads(response.text)
                delta = DeltaBatch.from_json(data)
                logger.info(f"[Curator] Completed successfully. Delta operations: {len(delta.operations)}")
                return CuratorOutput(delta=delta, raw=data)
            except ValueError as err:
                last_error = err
                logger.warning(f"[Curator] Attempt {attempt + 1}/{self.max_retries} failed: JSON parsing error")
                if attempt + 1 >= self.max_retries:
                    break
                prompt = (
                    base_prompt
                    + "\n\nReminder: Output only valid JSON, escape all double quotes or use single quotes, "
                    "and do not add any extra text."
                )

        # Instead of raising an error, return an empty delta to continue training
        logger.error(f"[Curator] Failed after {self.max_retries} attempts - returning empty delta to continue training")
        logger.error(f"[Curator] Last error: {last_error}")

        # Create an empty delta batch to allow training to continue
        reasoning = "Curator failed to produce valid JSON - skipping this reflection"
        empty_delta = DeltaBatch(reasoning=reasoning, operations=[])
        empty_data = {"reasoning": reasoning, "operations": []}

        return CuratorOutput(delta=empty_delta, raw=empty_data)


def _make_playbook_excerpt(playbook: Playbook, bullet_ids: Sequence[str]) -> str:
    lines: List[str] = []
    seen = set()
    for bullet_id in bullet_ids:
        if bullet_id in seen:
            continue
        bullet = playbook.get_bullet(bullet_id)
        if bullet:
            seen.add(bullet_id)
            lines.append(f"[{bullet.id}] {bullet.content}")
    return "\n".join(lines)


