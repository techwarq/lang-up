import json
import time
import uuid
from db.client import get_db


async def ensure_user(user_id: str) -> None:
    db = await get_db()
    await db.execute(
        "INSERT OR IGNORE INTO users (id, created_at) VALUES (?, ?)",
        (user_id, int(time.time())),
    )
    await db.commit()


async def create_session(user_id: str) -> str:
    session_id = str(uuid.uuid4())
    db = await get_db()
    await db.execute(
        "INSERT INTO sessions (id, user_id, started_at) VALUES (?, ?, ?)",
        (session_id, user_id, int(time.time())),
    )
    await db.commit()
    return session_id


async def end_session(session_id: str, total_turns: int) -> None:
    db = await get_db()
    await db.execute(
        "UPDATE sessions SET ended_at = ?, total_turns = ? WHERE id = ?",
        (int(time.time()), total_turns, session_id),
    )
    await db.commit()


async def upsert_progress(
    user_id: str,
    lesson_id: str,
    score: int,
    total: int,
    weak_areas: list[str],
) -> None:
    db = await get_db()
    progress_id = str(uuid.uuid4())
    await db.execute(
        """INSERT INTO user_progress (id, user_id, lesson_id, completed_at, score, total, weak_areas)
           VALUES (?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(user_id, lesson_id) DO UPDATE SET
               completed_at = excluded.completed_at,
               score = excluded.score,
               total = excluded.total,
               weak_areas = excluded.weak_areas""",
        (progress_id, user_id, lesson_id, int(time.time()), score, total, json.dumps(weak_areas)),
    )
    await db.commit()


async def get_progress(user_id: str) -> dict:
    db = await get_db()
    async with db.execute(
        "SELECT lesson_id, score, total, weak_areas FROM user_progress WHERE user_id = ?",
        (user_id,),
    ) as cursor:
        rows = await cursor.fetchall()

    async with db.execute(
        "SELECT COUNT(*) as cnt FROM sessions WHERE user_id = ?",
        (user_id,),
    ) as cursor:
        total_row = await cursor.fetchone()

    lessons_completed = [row["lesson_id"] for row in rows]
    all_weak: list[str] = []
    for row in rows:
        all_weak.extend(json.loads(row["weak_areas"]))

    from curriculum.spanish import LESSONS
    completed_ids = set(lessons_completed)
    all_lesson_ids = list(LESSONS.keys())
    recommended = next((lid for lid in all_lesson_ids if lid not in completed_ids), all_lesson_ids[0])

    return {
        "lessonsCompleted": lessons_completed,
        "weakAreas": list(set(all_weak)),
        "recommendedLesson": recommended,
        "totalSessions": total_row["cnt"] if total_row else 0,
    }


async def log_turn(
    session_id: str,
    turn_index: int,
    user_speech: str,
    agent_state: str,
    tools_called: list[str],
    llm_prompt_tokens: int = 0,
    llm_completion_tokens: int = 0,
    stt_latency_ms: int = 0,
    llm_latency_ms: int = 0,
    tts_latency_ms: int = 0,
    total_latency_ms: int = 0,
) -> None:
    db = await get_db()
    row_id = str(uuid.uuid4())
    await db.execute(
        """INSERT INTO turn_logs
           (id, session_id, turn_index, timestamp, user_speech, agent_state,
            tools_called, llm_prompt_tokens, llm_completion_tokens,
            stt_latency_ms, llm_latency_ms, tts_latency_ms, total_latency_ms)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            row_id, session_id, turn_index, int(time.time()), user_speech, agent_state,
            json.dumps(tools_called), llm_prompt_tokens, llm_completion_tokens,
            stt_latency_ms, llm_latency_ms, tts_latency_ms, total_latency_ms,
        ),
    )
    await db.commit()
