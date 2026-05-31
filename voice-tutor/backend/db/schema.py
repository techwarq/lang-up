CREATE_USERS = """
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    created_at INTEGER NOT NULL
)"""

CREATE_SESSIONS = """
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    started_at INTEGER NOT NULL,
    ended_at INTEGER,
    total_turns INTEGER DEFAULT 0
)"""

CREATE_USER_PROGRESS = """
CREATE TABLE IF NOT EXISTS user_progress (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    lesson_id TEXT NOT NULL,
    completed_at INTEGER NOT NULL,
    score INTEGER NOT NULL,
    total INTEGER NOT NULL,
    weak_areas TEXT NOT NULL DEFAULT '[]',
    UNIQUE(user_id, lesson_id)
)"""

CREATE_TURN_LOGS = """
CREATE TABLE IF NOT EXISTS turn_logs (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    turn_index INTEGER NOT NULL,
    timestamp INTEGER NOT NULL,
    user_speech TEXT,
    agent_state TEXT,
    tools_called TEXT DEFAULT '[]',
    llm_prompt_tokens INTEGER DEFAULT 0,
    llm_completion_tokens INTEGER DEFAULT 0,
    stt_latency_ms INTEGER DEFAULT 0,
    llm_latency_ms INTEGER DEFAULT 0,
    tts_latency_ms INTEGER DEFAULT 0,
    total_latency_ms INTEGER DEFAULT 0
)"""

ALL_TABLES = [CREATE_USERS, CREATE_SESSIONS, CREATE_USER_PROGRESS, CREATE_TURN_LOGS]
