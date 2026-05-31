import pytest
from curriculum.spanish import LESSONS, list_lessons, LESSON_GREETINGS, LESSON_NUMBERS, LESSON_RESTAURANT
from curriculum.types import Lesson, VocabItem, QuizQuestion, LessonStep


def test_all_three_lessons_exist():
    assert "lesson-greetings" in LESSONS
    assert "lesson-numbers" in LESSONS
    assert "lesson-restaurant" in LESSONS


def test_list_lessons_returns_all_three():
    assert len(list_lessons()) == 3


@pytest.mark.parametrize("lesson", [LESSON_GREETINGS, LESSON_NUMBERS, LESSON_RESTAURANT])
def test_each_lesson_has_minimum_5_quiz_questions(lesson: Lesson):
    assert len(lesson.quizQuestions) >= 5, f"{lesson.id} has fewer than 5 quiz questions"


@pytest.mark.parametrize("lesson", [LESSON_GREETINGS, LESSON_NUMBERS, LESSON_RESTAURANT])
def test_each_lesson_vocabulary_has_pronunciation_tips(lesson: Lesson):
    for item in lesson.vocabulary:
        assert item.pronunciationTip, f"{lesson.id}: vocab item '{item.spanish}' missing pronunciationTip"


@pytest.mark.parametrize("lesson", [LESSON_GREETINGS, LESSON_NUMBERS, LESSON_RESTAURANT])
def test_each_lesson_has_required_step_types(lesson: Lesson):
    step_types = {step.type for step in lesson.steps}
    assert "objective" in step_types, f"{lesson.id} missing 'objective' step"
    assert "check" in step_types, f"{lesson.id} missing 'check' step"


@pytest.mark.parametrize("lesson", [LESSON_GREETINGS, LESSON_NUMBERS, LESSON_RESTAURANT])
def test_no_duplicate_question_ids_within_lesson(lesson: Lesson):
    ids = [q.id for q in lesson.quizQuestions]
    assert len(ids) == len(set(ids)), f"{lesson.id} has duplicate question IDs"


@pytest.mark.parametrize("lesson", [LESSON_GREETINGS, LESSON_NUMBERS, LESSON_RESTAURANT])
def test_vocab_items_have_required_fields(lesson: Lesson):
    for item in lesson.vocabulary:
        assert item.spanish, f"{lesson.id}: missing 'spanish' in vocab item"
        assert item.english, f"{lesson.id}: missing 'english' in vocab item"
        assert item.pronunciationTip, f"{lesson.id}: missing 'pronunciationTip' in vocab item"


@pytest.mark.parametrize("lesson", [LESSON_GREETINGS, LESSON_NUMBERS, LESSON_RESTAURANT])
def test_quiz_questions_have_required_fields(lesson: Lesson):
    for q in lesson.quizQuestions:
        assert q.id
        assert q.prompt
        assert q.expectedAnswer
        assert isinstance(q.acceptedVariants, list)


@pytest.mark.parametrize("lesson", [LESSON_GREETINGS, LESSON_NUMBERS, LESSON_RESTAURANT])
def test_lesson_steps_have_agent_script(lesson: Lesson):
    for step in lesson.steps:
        assert step.agentScript, f"{lesson.id}: step '{step.id}' has empty agentScript"


def test_lesson_greetings_has_correct_id():
    assert LESSON_GREETINGS.id == "lesson-greetings"


def test_lesson_numbers_has_correct_id():
    assert LESSON_NUMBERS.id == "lesson-numbers"


def test_lesson_restaurant_has_correct_id():
    assert LESSON_RESTAURANT.id == "lesson-restaurant"


def test_restaurant_lesson_has_minimum_quiz_questions():
    assert len(LESSON_RESTAURANT.quizQuestions) >= 6
