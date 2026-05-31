from enum import Enum
from dataclasses import dataclass, field
from typing import Optional

from curriculum.types import QuizQuestion


class AgentState(str, Enum):
    IDLE = "idle"
    TEACHING = "teaching"
    QUIZ = "quiz"
    DOUBT = "doubt"
    ROLEPLAY = "roleplay"


@dataclass
class FSMContext:
    state: AgentState = AgentState.IDLE
    previous_state: Optional[AgentState] = None
    current_lesson_id: Optional[str] = None
    current_lesson_step: int = 0
    quiz_score: int = 0
    quiz_total: int = 0
    quiz_questions: list[QuizQuestion] = field(default_factory=list)
    current_question_index: int = 0
    doubt_resume_context: Optional[str] = None
    current_roleplay_id: Optional[str] = None
    current_roleplay_title: Optional[str] = None
    current_roleplay_character_context: Optional[str] = None
    # loaded from DB at session start — never mutated during session
    past_lessons_completed: list[str] = field(default_factory=list)
    past_weak_areas: list[str] = field(default_factory=list)
    past_total_sessions: int = 0
    # accumulated during this session
    session_vocab_introduced: list[str] = field(default_factory=list)
    session_mistakes: list[str] = field(default_factory=list)


class StateMachine:
    def __init__(self) -> None:
        self._ctx = FSMContext()

    def transition(self, new_state: AgentState, **updates: object) -> None:
        if new_state == AgentState.DOUBT:
            self._ctx.previous_state = self._ctx.state
        self._ctx.state = new_state
        for key, value in updates.items():
            if hasattr(self._ctx, key):
                setattr(self._ctx, key, value)

    def return_from_doubt(self) -> None:
        if self._ctx.previous_state is not None:
            self._ctx.state = self._ctx.previous_state
            self._ctx.previous_state = None

    @property
    def context(self) -> FSMContext:
        return self._ctx

    @property
    def current_state(self) -> AgentState:
        return self._ctx.state
