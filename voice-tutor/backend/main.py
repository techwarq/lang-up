import asyncio
import os
from aiohttp import web
from dotenv import load_dotenv

load_dotenv()

from fsm import StateMachine
from memory.short_term import ShortTermMemory
from memory import long_term
from logger import TurnLogger
from pipeline import create_task_and_runner


async def _health_server() -> None:
    async def health(_: web.Request) -> web.Response:
        return web.Response(text="ok")

    app = web.Application()
    app.router.add_get("/", health)
    app.router.add_get("/health", health)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", "8080"))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"Health server on :{port}")


async def run() -> None:
    user_id = "user-001"

    await long_term.ensure_user(user_id)
    session_id = await long_term.create_session(user_id)

    fsm = StateMachine()
    short_term = ShortTermMemory()
    logger = TurnLogger(session_id)

    ws_port = int(os.getenv("WS_PORT", "8765"))
    print(f"Starting voice tutor — session {session_id}")
    print(f"WebSocket on :{ws_port}")

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


async def main() -> None:
    await asyncio.gather(_health_server(), run())


if __name__ == "__main__":
    asyncio.run(main())
