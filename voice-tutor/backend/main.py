import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

from fsm import StateMachine
from memory.short_term import ShortTermMemory
from memory import long_term
from logger import TurnLogger
from pipeline import create_task_and_runner


async def run() -> None:
    user_id = "user-001"

    await long_term.ensure_user(user_id)
    session_id = await long_term.create_session(user_id)

    # Load historical progress BEFORE building the FSM so the prompt reflects it
    past = await long_term.get_progress(user_id)

    fsm = StateMachine()
    fsm.context.past_lessons_completed = past.get("lessonsCompleted", [])
    fsm.context.past_weak_areas = past.get("weakAreas", [])
    fsm.context.past_total_sessions = past.get("totalSessions", 0)

    short_term = ShortTermMemory()
    logger = TurnLogger(session_id)

    print(f"Starting voice tutor — session {session_id}")
    print(f"Listening on ws://{os.getenv('WS_HOST', '0.0.0.0')}:{os.getenv('WS_PORT', '8765')}")

    task, runner, transport = await create_task_and_runner(
        fsm, short_term, user_id, session_id
    )

    try:
        await runner.add_workers(task)
        await runner.run()
    finally:
        await long_term.end_session(session_id, logger.turn_count)
        from db.client import close_db
        await close_db()
        print(f"Session {session_id} ended — {logger.turn_count} turns logged")


if __name__ == "__main__":
    asyncio.run(run())
