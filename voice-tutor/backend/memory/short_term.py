from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, List, Optional


@dataclass
class TurnRecord:
    turn_index: int
    user_speech: str
    agent_response: str
    tools_called: list[str] = field(default_factory=list)


class ShortTermMemory:
    """Session-scoped in-memory context. Cleared on disconnect."""

    def __init__(self) -> None:
        self._turns: list[TurnRecord] = []
        self._facts: dict[str, Any] = {}

    def add_turn(self, user_speech: str, agent_response: str, tools_called: Optional[List[str]] = None) -> TurnRecord:
        record = TurnRecord(
            turn_index=len(self._turns),
            user_speech=user_speech,
            agent_response=agent_response,
            tools_called=tools_called or [],
        )
        self._turns.append(record)
        return record

    def set_fact(self, key: str, value: Any) -> None:
        self._facts[key] = value

    def get_fact(self, key: str, default: Any = None) -> Any:
        return self._facts.get(key, default)

    def recent_turns(self, n: int = 5) -> list[TurnRecord]:
        return self._turns[-n:]

    @property
    def turn_count(self) -> int:
        return len(self._turns)
