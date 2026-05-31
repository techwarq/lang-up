import pytest
from fsm import StateMachine, AgentState, FSMContext
from curriculum.types import QuizQuestion


def make_question(qid: str) -> QuizQuestion:
    return QuizQuestion(
        id=qid,
        type="translation_en_es",
        prompt="Translate: hello",
        expectedAnswer="hola",
        acceptedVariants=["hola"],
    )


def test_initial_state_is_idle():
    sm = StateMachine()
    assert sm.current_state == AgentState.IDLE


def test_transition_idle_to_teaching():
    sm = StateMachine()
    sm.transition(AgentState.TEACHING, current_lesson_id="lesson-greetings")
    assert sm.current_state == AgentState.TEACHING
    assert sm.context.current_lesson_id == "lesson-greetings"


def test_transition_to_doubt_saves_previous_state():
    sm = StateMachine()
    sm.transition(AgentState.TEACHING, current_lesson_id="lesson-greetings")
    sm.transition(AgentState.DOUBT, doubt_resume_context="mid lesson step 2")
    assert sm.current_state == AgentState.DOUBT
    assert sm.context.previous_state == AgentState.TEACHING


def test_return_from_doubt_restores_previous():
    sm = StateMachine()
    sm.transition(AgentState.QUIZ)
    sm.transition(AgentState.DOUBT)
    sm.return_from_doubt()
    assert sm.current_state == AgentState.QUIZ
    assert sm.context.previous_state is None


def test_return_from_doubt_when_no_previous_does_not_crash():
    sm = StateMachine()
    sm.return_from_doubt()
    assert sm.current_state == AgentState.IDLE


def test_multiple_transitions_are_correct():
    sm = StateMachine()
    sm.transition(AgentState.TEACHING, current_lesson_id="lesson-numbers")
    sm.transition(AgentState.QUIZ, quiz_score=0, quiz_total=5)
    sm.transition(AgentState.DOUBT)
    sm.return_from_doubt()
    assert sm.current_state == AgentState.QUIZ
    assert sm.context.quiz_total == 5


def test_transition_updates_fsm_context_fields():
    sm = StateMachine()
    questions = [make_question("q1"), make_question("q2")]
    sm.transition(
        AgentState.QUIZ,
        current_lesson_id="lesson-greetings",
        quiz_questions=questions,
        quiz_score=0,
        quiz_total=2,
        current_question_index=0,
    )
    ctx = sm.context
    assert ctx.quiz_total == 2
    assert len(ctx.quiz_questions) == 2
    assert ctx.current_lesson_id == "lesson-greetings"


def test_doubt_from_quiz_resumes_quiz():
    sm = StateMachine()
    sm.transition(AgentState.QUIZ, quiz_score=1, quiz_total=3)
    sm.transition(AgentState.DOUBT, doubt_resume_context="question 2")
    assert sm.context.previous_state == AgentState.QUIZ
    sm.return_from_doubt()
    assert sm.current_state == AgentState.QUIZ
    assert sm.context.quiz_score == 1
