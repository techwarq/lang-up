from __future__ import annotations
import time
from collections import defaultdict


class RateLimiter:
    def __init__(
        self,
        max_concurrent_per_ip: int = 3,
        max_per_hour_per_ip: int = 10,
        max_turns_per_session: int = 300,
    ):
        self._concurrent: dict[str, int] = defaultdict(int)
        self._hourly: dict[str, list[float]] = defaultdict(list)
        self._session_turns: dict[str, int] = defaultdict(int)
        self._max_concurrent = max_concurrent_per_ip
        self._max_per_hour = max_per_hour_per_ip
        self._max_turns = max_turns_per_session

    def check_connection(self, ip: str) -> tuple[bool, str]:
        now = time.time()
        cutoff = now - 3600
        self._hourly[ip] = [t for t in self._hourly[ip] if t > cutoff]
        if self._concurrent[ip] >= self._max_concurrent:
            return False, f"Too many concurrent sessions from your IP (max {self._max_concurrent})"
        if len(self._hourly[ip]) >= self._max_per_hour:
            return False, f"Hourly session limit reached (max {self._max_per_hour}/hour)"
        return True, ""

    def on_connect(self, ip: str) -> None:
        self._concurrent[ip] += 1
        self._hourly[ip].append(time.time())

    def on_disconnect(self, ip: str) -> None:
        self._concurrent[ip] = max(0, self._concurrent[ip] - 1)

    def check_turn(self, session_id: str) -> tuple[bool, str]:
        if self._session_turns[session_id] >= self._max_turns:
            return False, f"Session turn limit reached ({self._max_turns} turns max)"
        return True, ""

    def increment_turn(self, session_id: str) -> None:
        self._session_turns[session_id] += 1

    def cleanup_session(self, session_id: str) -> None:
        self._session_turns.pop(session_id, None)


_limiter = RateLimiter()


def get_rate_limiter() -> RateLimiter:
    return _limiter
