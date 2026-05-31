from dataclasses import dataclass, field
from typing import Optional, Literal


@dataclass
class VocabItem:
    spanish: str
    english: str
    pronunciationTip: str
    gender: Optional[Literal["masculine", "feminine"]] = None
    exampleSentence: Optional[str] = None


@dataclass
class QuizQuestion:
    id: str
    type: Literal["translation_en_es", "translation_es_en", "listening", "spoken_response"]
    prompt: str
    expectedAnswer: str
    acceptedVariants: list[str]
    targetVocab: Optional[str] = None


@dataclass
class LessonStep:
    id: str
    type: Literal["objective", "explanation", "example", "practice", "check"]
    agentScript: str
    expectsUserResponse: bool


@dataclass
class Lesson:
    id: str
    title: str
    objective: str
    vocabulary: list[VocabItem]
    grammarNotes: list[str]
    exampleDialogues: list[dict]
    steps: list[LessonStep]
    quizQuestions: list[QuizQuestion]


@dataclass
class RoleplayScenario:
    id: str
    title: str
    description: str
    characterContext: str   # who Sofia plays and the setting
    openingLine: str        # Sofia's first line in character (Spanish)
    openingHint: str        # English gloss of the opening line
    targetVocab: list[str]
