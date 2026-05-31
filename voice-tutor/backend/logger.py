import time
from dataclasses import dataclass, field
from memory import long_term


@dataclass
class TurnLog:
    session_id: str
    user_speech: str
    agent_state: str
    tools_called: list[str] = field(default_factory=list)
    stt_latency_ms: int = 0
    llm_latency_ms: int = 0
    tts_latency_ms: int = 0
    total_latency_ms: int = 0
    llm_prompt_tokens: int = 0
    llm_completion_tokens: int = 0


class TurnLogger:
    def __init__(self, session_id: str) -> None:
        self._session_id = session_id
        self._turn_index = 0

    async def log(self, entry: TurnLog) -> None:
        idx = self._turn_index
        self._turn_index += 1

        tools_str = "[" + ", ".join(entry.tools_called) + "]" if entry.tools_called else "[]"
        print(
            f"[TURN {idx}] state={entry.agent_state.upper()} | "
            f"STT={entry.stt_latency_ms}ms LLM={entry.llm_latency_ms}ms "
            f"TTS={entry.tts_latency_ms}ms TOTAL={entry.total_latency_ms}ms | "
            f"tools={tools_str}"
        )

        await long_term.log_turn(
            session_id=self._session_id,
            turn_index=idx,
            user_speech=entry.user_speech,
            agent_state=entry.agent_state,
            tools_called=entry.tools_called,
            llm_prompt_tokens=entry.llm_prompt_tokens,
            llm_completion_tokens=entry.llm_completion_tokens,
            stt_latency_ms=entry.stt_latency_ms,
            llm_latency_ms=entry.llm_latency_ms,
            tts_latency_ms=entry.tts_latency_ms,
            total_latency_ms=entry.total_latency_ms,
        )

    @property
    def turn_count(self) -> int:
        return self._turn_index
