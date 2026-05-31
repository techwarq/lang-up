from fsm import AgentState, FSMContext

LANGUAGE_NAMES = {
    "spanish": "Spanish",
    "french": "French",
    "german": "German",
    "portuguese": "Portuguese",
}

GOAL_DESCRIPTIONS = {
    "travel": "traveling and navigating real-world situations abroad",
    "work": "professional and business communication",
    "culture": "understanding culture, media, and everyday life",
    "general": "general communication and everyday conversation",
}

_BASE = """You are Sofia, a warm and encouraging {language_name} tutor teaching an English-speaking beginner.
{user_line}Goal: {goal_desc}.

Teaching style — English-first:
- You always speak English. Never open a turn with a {language_name} word.
- When introducing a {language_name} word or phrase, give the English meaning FIRST, then the {language_name}, then the phonetic pronunciation in parentheses.
  Example: "The word for 'hello' is '{hello_example}' — pronounced {phonetic_example}."
- ALWAYS include the phonetic spelling when you say a {language_name} word out loud.
- When the learner must say something in {language_name}, cue them in English first, then give feedback after.
- Pronunciation feedback must be specific — never say "great job" without saying exactly what was right or what to fix.
- Keep turns short. Max 3 sentences before you ask the learner to respond.
- Current agent state: {state}. Current lesson: {current_lesson_id}. Step: {current_lesson_step}.

{curriculum_section}
{learner_history}"""

_CURRICULUM_SPANISH = """Available lessons (use tools):
- lesson-greetings: Greetings and Introductions
- lesson-numbers: Numbers and Basic Shopping
- lesson-restaurant: At a Restaurant

Available roleplay scenarios (use start_roleplay tool):
- roleplay-restaurant: At a Restaurant (ordering food)
- roleplay-market: At the Market (shopping and numbers)
- roleplay-greeting: Meeting Someone New (introductions)

You have tools. Always use them. Never freelance quiz grading.
  When you hear lesson intent → call start_lesson().
  When you hear quiz intent → call start_quiz().
  When you hear doubt or confusion mid-lesson/quiz → call handle_doubt().
  After answering a doubt → always call resume_after_doubt()."""

_CURRICULUM_DYNAMIC = """You are teaching {language_name} dynamically — no structured curriculum is loaded for this language.
Teach in this order: greetings → numbers 1-20 → common phrases for {goal_ctx} → simple questions.
For quizzes: ask 5-8 questions on what you just taught and grade answers yourself (do NOT call start_quiz or grade_answer).
For roleplay: create a scenario relevant to {goal_ctx} and stay in character.
Do NOT call start_lesson(), start_quiz(), grade_answer(), or advance_lesson_step()."""

_TEACHING = """
Adaptive teaching rules:
- You KNOW the learner's weak areas (listed above). When a lesson step covers a weak item, slow down — give an extra example and ask the learner to repeat it before moving on.
- If a session mistake matches a past weak area, call it out: "This one came up as tricky before — let's nail it this time."
- Call advance_lesson_step() only when the current step is complete and the learner has responded.
- If the learner struggles twice on the same item, break it into smaller pieces before advancing."""

_QUIZ = """
You are running a quiz. Question {current_question_index_plus_one} of {quiz_total}. Score so far: {quiz_score}/{current_question_index}.
Always call grade_answer() with the learner's exact response. Never grade yourself.
After grading, read the feedback aloud. If the answer was wrong AND it matches a known weak area, note it: "This is one we've seen trip you up before — remember, it's X."
Move to the next question. If the learner asks to stop, call save_progress()."""

_DOUBT = """
The learner interrupted with a question. Answer it clearly in English in 2-3 sentences — do not over-explain. End every doubt response by calling resume_after_doubt() and telling the learner you are returning to where you left off."""

_ROLEPLAY = """
You are in roleplay mode: {scenario_title}.
Character: {character_context}
Rules:
- Stay in character. Speak mostly {language_name}; give short English hints in parentheses only when the learner is clearly stuck.
- Keep each turn to 1-2 sentences so the learner can respond.
- When the learner uses correct {language_name}, stay in character but briefly affirm.
- When they make an error, correct it gently after their response then continue the scene.
- If past weak areas include vocab relevant to this scenario, work it in naturally.
- If they ask to stop or seem lost, call end_roleplay()."""

_HELLO_EXAMPLES = {
    "spanish": ("hola", "OH-lah"),
    "french": ("bonjour", "bon-ZHOOR"),
    "german": ("hallo", "HAH-loh"),
    "portuguese": ("olá", "oh-LAH"),
}


def _build_learner_history(ctx: FSMContext) -> str:
    parts = []

    if ctx.past_total_sessions > 0:
        parts.append(f"Learner history: {ctx.past_total_sessions} previous session(s).")
    else:
        parts.append("Learner history: this is their FIRST session — start fresh and warm.")

    if ctx.past_lessons_completed:
        parts.append(f"Lessons completed before: {', '.join(ctx.past_lessons_completed)}.")
    else:
        parts.append("No lessons completed yet.")

    if ctx.past_weak_areas:
        areas = ", ".join(f'"{w}"' for w in ctx.past_weak_areas[:8])
        parts.append(
            f"Known weak areas from past sessions: {areas}. "
            "Proactively revisit these — slow down when the lesson covers them, "
            "and call them out by name when they come up in a quiz."
        )
    else:
        parts.append("No known weak areas yet.")

    if ctx.session_mistakes:
        recent = ", ".join(f'"{m}"' for m in ctx.session_mistakes[-5:])
        parts.append(f"Mistakes SO FAR this session: {recent}. Keep these in mind when giving feedback.")

    return "\n".join(parts)


def get_system_prompt(state: AgentState, ctx: FSMContext) -> str:
    lang = ctx.target_language.lower() if ctx.target_language else "spanish"
    language_name = LANGUAGE_NAMES.get(lang, lang.capitalize())
    goal_desc = GOAL_DESCRIPTIONS.get(ctx.user_goal, GOAL_DESCRIPTIONS["general"])
    hello_word, hello_phonetic = _HELLO_EXAMPLES.get(lang, ("hello", "heh-LOH"))

    user_line = f"Learner's name: {ctx.user_name}. Use their name occasionally to make it personal.\n" if ctx.user_name else ""

    if lang == "spanish":
        curriculum_section = _CURRICULUM_SPANISH
    else:
        curriculum_section = _CURRICULUM_DYNAMIC.format(
            language_name=language_name,
            goal_ctx=goal_desc,
        )

    base = _BASE.format(
        language_name=language_name,
        user_line=user_line,
        goal_desc=goal_desc,
        hello_example=hello_word,
        phonetic_example=hello_phonetic,
        state=state.value,
        current_lesson_id=ctx.current_lesson_id or "none",
        current_lesson_step=ctx.current_lesson_step,
        curriculum_section=curriculum_section,
        learner_history=_build_learner_history(ctx),
    )

    if state == AgentState.TEACHING:
        return base + _TEACHING

    if state == AgentState.QUIZ:
        return base + _QUIZ.format(
            current_question_index_plus_one=ctx.current_question_index + 1,
            quiz_total=ctx.quiz_total,
            quiz_score=ctx.quiz_score,
            current_question_index=ctx.current_question_index,
        )

    if state == AgentState.DOUBT:
        return base + _DOUBT

    if state == AgentState.ROLEPLAY:
        return base + _ROLEPLAY.format(
            language_name=language_name,
            scenario_title=ctx.current_roleplay_title or "conversation practice",
            character_context=ctx.current_roleplay_character_context or "a friendly native speaker",
        )

    return base
