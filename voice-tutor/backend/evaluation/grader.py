from __future__ import annotations
import re
import json
import os
from typing import Optional
from anthropic import AsyncAnthropic

_client: Optional[AsyncAnthropic] = None


def _get_client() -> AsyncAnthropic:
    global _client
    if _client is None:
        _client = AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    return _client


def _normalize(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[¿¡.,!?;:]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text


async def grade_answer(
    learner_answer: str,
    expected_answer: str,
    accepted_variants: list[str],
    question_type: str,
) -> dict:
    norm_learner = _normalize(learner_answer)
    norm_expected = _normalize(expected_answer)
    candidates = [norm_expected] + [_normalize(v) for v in accepted_variants]

    if norm_learner in candidates:
        return {"correct": True, "score": 1.0, "feedback": f"Correct! '{expected_answer}' is right."}

    # Substring check only for multi-word candidates (length > 5) to avoid false matches
    # like "hi" matching inside "somet**hi**ng"
    for candidate in candidates:
        if len(candidate) > 5 and (norm_learner in candidate or candidate in norm_learner):
            return {"correct": True, "score": 0.9, "feedback": f"Correct! '{expected_answer}' is right."}

    try:
        client = _get_client()
        variants_str = ", ".join(accepted_variants) if accepted_variants else "none"
        response = await client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=256,
            system="You are a Spanish language answer grader. Return ONLY valid JSON with no extra text.",
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Grade this Spanish learner's answer.\n"
                        f"Question type: {question_type}\n"
                        f"Expected answer: {expected_answer}\n"
                        f"Also accepted: {variants_str}\n"
                        f"Learner said: {learner_answer}\n\n"
                        "Return JSON:\n"
                        '{"correct": bool, "score": 0.0-1.0, "feedback": "One specific sentence. If wrong, state the correct answer."}\n\n'
                        "Be lenient on: minor spelling in spoken responses, extra polite words (gracias/por favor added), equivalent phrasing.\n"
                        "Be strict on: wrong vocabulary, wrong gender (el/la), wrong verb tense."
                    ),
                }
            ],
        )
        raw = response.content[0].text.strip()
        result = json.loads(raw)
        return {
            "correct": bool(result.get("correct", False)),
            "score": float(result.get("score", 0.0)),
            "feedback": str(result.get("feedback", "No feedback available.")),
        }
    except Exception:
        return {"correct": False, "score": 0.0, "feedback": "Could not grade — please try again."}
