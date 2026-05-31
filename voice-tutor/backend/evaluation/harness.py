#!/usr/bin/env python3
"""Standalone evaluation harness for the answer grader.

Run with:
    cd backend
    python evaluation/harness.py
"""
from __future__ import annotations
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from evaluation.grader import grade_answer

# (question_type, learner_answer, expected_answer, accepted_variants, should_be_correct, label)
TEST_CASES: list[tuple] = [
    # ── exact matches (no LLM call expected) ──────────────────────────────
    ("translation_en_es", "hola",         "hola",        [],              True,  "exact match"),
    ("translation_en_es", "HOLA",         "hola",        [],              True,  "case insensitive"),
    ("translation_en_es", "hola!",        "hola",        [],              True,  "punctuation stripped"),
    ("translation_en_es", "buenos dias",  "buenos días", ["buenos dias"], True,  "accepted variant"),
    ("translation_es_en", "good morning", "good morning",["good morning"],True,  "exact ES→EN"),
    ("translation_en_es", "estoy bien",   "estoy bien",  [],              True,  "two-word exact"),

    # ── wrong answers ──────────────────────────────────────────────────────
    ("translation_en_es", "adios",        "hola",        [],              False, "wrong word"),
    ("translation_en_es", "",             "hola",        [],              False, "empty answer"),

    # ── LLM-graded (fuzzy / paraphrase) ───────────────────────────────────
    ("translation_es_en", "what's your name",   "what is your name", ["what's your name"], True,  "contraction variant"),
    ("translation_es_en", "so-so",              "more or less",      ["so-so","okay"],     True,  "slang variant"),
    ("spoken_response",   "me llamo sofia",     "me llamo",          ["me llamo sofia"],   True,  "name slot filled"),
    ("spoken_response",   "quisiera tres por favor", "quisiera tres, por favor",
                          ["quisiera tres por favor"],                              True,  "comma omitted"),
    ("translation_es_en", "nice to meet you",   "nice to meet you",  [],              True,  "exact phrase"),

    # ── listening comprehension type ──────────────────────────────────────
    ("listening",         "good evening",       "good evening",      ["good night"],  True,  "listening exact"),
    ("listening",         "good night",         "good evening",      ["good night"],  True,  "listening variant"),
    ("listening",         "hello",              "good evening",      ["good night"],  False, "listening wrong"),
]


async def run() -> bool:
    print("=" * 64)
    print("  Answer Grader Evaluation Harness")
    print("=" * 64)

    passed = failed = 0
    failures: list[str] = []

    for i, (q_type, learner, expected, variants, should_correct, label) in enumerate(TEST_CASES, 1):
        result = await grade_answer(learner, expected, variants, q_type)
        got = result["correct"]
        ok = got == should_correct
        status = "PASS" if ok else "FAIL"
        fb = result.get("feedback", "")[:55]

        print(f"  [{status}] #{i:02d} {label:<28} correct={got} want={should_correct}  {fb}")

        if ok:
            passed += 1
        else:
            failed += 1
            failures.append(f"    #{i:02d} {label}: learner='{learner}' expected='{expected}' got_correct={got}")

    pct = 100 * passed // len(TEST_CASES)
    print()
    print("=" * 64)
    print(f"  Result: {passed}/{len(TEST_CASES)} passed ({pct}%)")

    if failures:
        print("\n  Failed cases:")
        for f in failures:
            print(f)

    return failed == 0


if __name__ == "__main__":
    ok = asyncio.run(run())
    sys.exit(0 if ok else 1)
