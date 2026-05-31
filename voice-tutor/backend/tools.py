from __future__ import annotations
import random
from dataclasses import dataclass
from typing import Any, Callable, Awaitable, Optional

from fsm import StateMachine, AgentState
from memory.short_term import ShortTermMemory
from memory import long_term
from evaluation.grader import grade_answer
from curriculum.spanish import get_lesson, list_lessons, get_roleplay_scenario
from curriculum.types import QuizQuestion


@dataclass
class ToolContext:
    fsm: StateMachine
    short_term: ShortTermMemory
    user_id: str
    session_id: str
    publish_state: Callable[[dict], Awaitable[None]]


TOOL_DEFINITIONS = [
    {
        "name": "start_lesson",
        "description": "Start a Spanish lesson. Call when the learner wants to begin a lesson.",
        "input_schema": {
            "type": "object",
            "properties": {
                "lessonId": {
                    "type": "string",
                    "description": "Lesson ID: 'lesson-greetings', 'lesson-numbers', or 'lesson-restaurant'",
                }
            },
            "required": ["lessonId"],
        },
    },
    {
        "name": "advance_lesson_step",
        "description": "Advance to the next step in the current lesson. Call after the learner completes the current step.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "start_quiz",
        "description": "Start the quiz for a lesson. Call when the learner wants to be tested.",
        "input_schema": {
            "type": "object",
            "properties": {
                "lessonId": {
                    "type": "string",
                    "description": "Lesson ID to quiz on",
                }
            },
            "required": ["lessonId"],
        },
    },
    {
        "name": "grade_answer",
        "description": "Grade the learner's quiz answer. Always call this — never grade manually.",
        "input_schema": {
            "type": "object",
            "properties": {
                "questionId": {"type": "string"},
                "learnerAnswer": {"type": "string", "description": "Exactly what the learner said"},
                "expectedAnswer": {"type": "string"},
                "acceptedVariants": {"type": "array", "items": {"type": "string"}},
                "questionType": {"type": "string"},
            },
            "required": ["questionId", "learnerAnswer", "expectedAnswer", "acceptedVariants", "questionType"],
        },
    },
    {
        "name": "handle_doubt",
        "description": "Handle a doubt or off-topic question from the learner mid-lesson or quiz.",
        "input_schema": {
            "type": "object",
            "properties": {
                "doubtText": {"type": "string"},
                "currentContext": {"type": "string", "description": "Brief description of where we were"},
            },
            "required": ["doubtText", "currentContext"],
        },
    },
    {
        "name": "resume_after_doubt",
        "description": "Resume the lesson or quiz after answering a doubt. Call after every handle_doubt response.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "save_progress",
        "description": "Save the learner's quiz progress to the database.",
        "input_schema": {
            "type": "object",
            "properties": {
                "lessonId": {"type": "string"},
                "score": {"type": "integer"},
                "total": {"type": "integer"},
                "weakAreas": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["lessonId", "score", "total", "weakAreas"],
        },
    },
    {
        "name": "get_user_progress",
        "description": "Retrieve the learner's past progress across all lessons.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "lookup_vocab",
        "description": "Look up a Spanish or English word in the curriculum vocabulary.",
        "input_schema": {
            "type": "object",
            "properties": {
                "word": {"type": "string"}
            },
            "required": ["word"],
        },
    },
    {
        "name": "start_roleplay",
        "description": "Start a conversational roleplay scenario. Call when the learner wants to practice by talking with a character.",
        "input_schema": {
            "type": "object",
            "properties": {
                "scenarioId": {
                    "type": "string",
                    "description": "Scenario ID: 'roleplay-restaurant', 'roleplay-market', or 'roleplay-greeting'",
                }
            },
            "required": ["scenarioId"],
        },
    },
    {
        "name": "end_roleplay",
        "description": "End the current roleplay and return to idle. Call when the learner wants to stop or the scene is complete.",
        "input_schema": {"type": "object", "properties": {}},
    },
]


async def dispatch(tool_name: str, args: dict, ctx: ToolContext) -> Any:
    handlers: dict[str, Callable] = {
        "start_lesson": _start_lesson,
        "advance_lesson_step": _advance_lesson_step,
        "start_quiz": _start_quiz,
        "grade_answer": _grade_answer,
        "handle_doubt": _handle_doubt,
        "resume_after_doubt": _resume_after_doubt,
        "save_progress": _save_progress,
        "get_user_progress": _get_user_progress,
        "lookup_vocab": _lookup_vocab,
        "start_roleplay": _start_roleplay,
        "end_roleplay": _end_roleplay,
    }
    handler = handlers.get(tool_name)
    if handler is None:
        return {"error": f"Unknown tool: {tool_name}"}
    return await handler(args, ctx)


async def _start_lesson(args: dict, ctx: ToolContext) -> dict:
    lesson_id = args["lessonId"]
    lesson = get_lesson(lesson_id)
    if lesson is None:
        return {"error": f"Lesson '{lesson_id}' not found"}

    ctx.fsm.transition(
        AgentState.TEACHING,
        current_lesson_id=lesson_id,
        current_lesson_step=0,
    )
    await ctx.publish_state({"type": "state", "state": "teaching", "lessonId": lesson_id, "lessonTitle": lesson.title})

    first_step = lesson.steps[0]
    return {
        "lessonTitle": lesson.title,
        "objective": lesson.objective,
        "firstStep": first_step.agentScript,
        "firstStepType": first_step.type,
        "firstStepExpectsResponse": first_step.expectsUserResponse,
        "totalSteps": len(lesson.steps),
    }


async def _advance_lesson_step(args: dict, ctx: ToolContext) -> dict:
    lesson_id = ctx.fsm.context.current_lesson_id
    if lesson_id is None:
        return {"error": "No active lesson"}

    lesson = get_lesson(lesson_id)
    if lesson is None:
        return {"error": "Current lesson not found"}

    next_step = ctx.fsm.context.current_lesson_step + 1
    ctx.fsm.transition(AgentState.TEACHING, current_lesson_step=next_step)

    if next_step >= len(lesson.steps):
        return {
            "complete": True,
            "summary": f"You've completed '{lesson.title}'! Great work. Would you like to take a quiz to test what you've learned?",
        }

    step = lesson.steps[next_step]
    return {
        "complete": False,
        "stepContent": step.agentScript,
        "stepType": step.type,
        "expectsResponse": step.expectsUserResponse,
        "stepIndex": next_step,
        "totalSteps": len(lesson.steps),
    }


async def _start_quiz(args: dict, ctx: ToolContext) -> dict:
    lesson_id = args["lessonId"]
    lesson = get_lesson(lesson_id)
    if lesson is None:
        return {"error": f"Lesson '{lesson_id}' not found"}

    questions = list(lesson.quizQuestions)
    random.shuffle(questions)

    ctx.fsm.transition(
        AgentState.QUIZ,
        current_lesson_id=lesson_id,
        quiz_questions=questions,
        quiz_score=0,
        quiz_total=len(questions),
        current_question_index=0,
    )
    await ctx.publish_state({
        "type": "state", "state": "quiz", "lessonId": lesson_id,
        "lessonTitle": lesson.title, "total": len(questions), "questionType": questions[0].type,
    })

    first_q = questions[0]
    return {
        "firstQuestion": {
            "id": first_q.id,
            "type": first_q.type,
            "prompt": first_q.prompt,
            "expectedAnswer": first_q.expectedAnswer,
            "acceptedVariants": first_q.acceptedVariants,
        },
        "totalQuestions": len(questions),
    }


async def _grade_answer(args: dict, ctx: ToolContext) -> dict:
    learner_answer = args["learnerAnswer"]
    expected = args["expectedAnswer"]
    variants = args.get("acceptedVariants", [])
    q_type = args.get("questionType", "translation_en_es")

    result = await grade_answer(learner_answer, expected, variants, q_type)

    fsm_ctx = ctx.fsm.context
    new_index = fsm_ctx.current_question_index + 1
    new_score = fsm_ctx.quiz_score + (1 if result["correct"] else 0)

    if not result["correct"] and expected:
        ctx.fsm.context.session_mistakes.append(expected)

    ctx.fsm.transition(
        AgentState.QUIZ,
        quiz_score=new_score,
        current_question_index=new_index,
    )
    questions = fsm_ctx.quiz_questions
    next_q_type = questions[new_index].type if new_index < len(questions) else None
    await ctx.publish_state({
        "type": "score", "score": new_score, "index": new_index,
        "total": fsm_ctx.quiz_total, "questionType": next_q_type,
    })
    if new_index >= len(questions):
        final_score = f"{new_score}/{fsm_ctx.quiz_total}"
        await _save_progress(
            {
                "lessonId": fsm_ctx.current_lesson_id or "",
                "score": new_score,
                "total": fsm_ctx.quiz_total,
                "weakAreas": fsm_ctx.session_mistakes,
            },
            ctx,
        )
        return {
            "correct": result["correct"],
            "score": result["score"],
            "feedback": result["feedback"],
            "quizComplete": True,
            "finalScore": final_score,
            "summary": f"Quiz complete! You scored {final_score}.",
        }

    next_q = questions[new_index]
    return {
        "correct": result["correct"],
        "score": result["score"],
        "feedback": result["feedback"],
        "quizComplete": False,
        "nextQuestion": {
            "id": next_q.id,
            "type": next_q.type,
            "prompt": next_q.prompt,
            "expectedAnswer": next_q.expectedAnswer,
            "acceptedVariants": next_q.acceptedVariants,
        },
    }


async def _handle_doubt(args: dict, ctx: ToolContext) -> dict:
    doubt_text = args["doubtText"]
    current_context = args["currentContext"]

    ctx.fsm.transition(AgentState.DOUBT, doubt_resume_context=current_context)
    await ctx.publish_state({"type": "state", "state": "doubt"})

    answer = _lookup_doubt_in_curriculum(doubt_text)
    return {
        "answer": answer or "Let me clarify that for you.",
        "resumeContext": current_context,
    }


def _lookup_doubt_in_curriculum(doubt_text: str) -> Optional[str]:
    doubt_lower = doubt_text.lower()
    for lesson in list_lessons():
        for item in lesson.vocabulary:
            if item.spanish.lower() in doubt_lower or item.english.lower() in doubt_lower:
                return (
                    f"'{item.spanish}' means '{item.english}'. "
                    f"Pronunciation tip: {item.pronunciationTip}."
                    + (f" Example: {item.exampleSentence}" if item.exampleSentence else "")
                )
        for note in lesson.grammarNotes:
            keywords = [w for w in doubt_lower.split() if len(w) > 4]
            if any(k in note.lower() for k in keywords):
                return note
    return None


async def _resume_after_doubt(args: dict, ctx: ToolContext) -> dict:
    resume_ctx = ctx.fsm.context.doubt_resume_context
    ctx.fsm.return_from_doubt()
    await ctx.publish_state({"type": "state", "state": ctx.fsm.current_state.value})
    return {
        "resumedState": ctx.fsm.current_state.value,
        "resumeContext": resume_ctx or "continuing from where we left off",
    }


async def _save_progress(args: dict, ctx: ToolContext) -> dict:
    await long_term.upsert_progress(
        user_id=ctx.user_id,
        lesson_id=args["lessonId"],
        score=args["score"],
        total=args["total"],
        weak_areas=args.get("weakAreas", []),
    )
    return {"saved": True}


async def _get_user_progress(args: dict, ctx: ToolContext) -> dict:
    return await long_term.get_progress(ctx.user_id)


async def _lookup_vocab(args: dict, ctx: ToolContext) -> dict:
    word = args["word"].lower().strip()
    for lesson in list_lessons():
        for item in lesson.vocabulary:
            if item.spanish.lower() == word or item.english.lower() == word:
                return {
                    "found": True,
                    "item": {
                        "spanish": item.spanish,
                        "english": item.english,
                        "pronunciationTip": item.pronunciationTip,
                        "gender": item.gender,
                        "exampleSentence": item.exampleSentence,
                    },
                    "lesson": lesson.title,
                }
    return {"found": False}


async def _start_roleplay(args: dict, ctx: ToolContext) -> dict:
    scenario_id = args["scenarioId"]
    scenario = get_roleplay_scenario(scenario_id)
    if scenario is None:
        return {"error": f"Scenario '{scenario_id}' not found"}

    ctx.fsm.transition(
        AgentState.ROLEPLAY,
        current_roleplay_id=scenario.id,
        current_roleplay_title=scenario.title,
        current_roleplay_character_context=scenario.characterContext,
    )
    await ctx.publish_state({
        "type": "state", "state": "roleplay",
        "scenarioTitle": scenario.title, "scenarioId": scenario.id,
    })

    return {
        "scenarioTitle": scenario.title,
        "description": scenario.description,
        "characterContext": scenario.characterContext,
        "openingLine": scenario.openingLine,
        "openingHint": scenario.openingHint,
        "targetVocab": scenario.targetVocab,
        "instruction": "Stay in character. Say the opening line now to begin the scene.",
    }


async def _end_roleplay(args: dict, ctx: ToolContext) -> dict:
    title = ctx.fsm.context.current_roleplay_title or "the roleplay"
    ctx.fsm.transition(
        AgentState.IDLE,
        current_roleplay_id=None,
        current_roleplay_title=None,
        current_roleplay_character_context=None,
    )
    await ctx.publish_state({"type": "state", "state": "idle"})
    return {
        "ended": True,
        "summary": f"Great practice on '{title}'! What would you like to do next — continue a lesson, take a quiz, or try another roleplay?",
    }
