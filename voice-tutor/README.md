# Sofia — Voice-First Spanish Tutor

A real-time, hands-free Spanish tutor built on Pipecat. Speak into your mic; Sofia teaches, quizzes, roleplays, and answers doubts entirely through voice — no typing required.

## Architecture

```
Browser (Next.js)  ──WebSocket──►  Python Pipecat Server
  AudioWorklet (16kHz PCM out)       WebsocketServerTransport
  WAV playback (24kHz in)            SileroVAD (barge-in)
  FSM state badges                   Deepgram STT nova-3 (multilingual)
  Quiz score / transcript            Gemini 2.5 Flash (LLM + 11 tools)
                                     Gemini TTS (streaming, multilingual)
                                     SQLite via aiosqlite (long-term memory)
```

The Pipecat server runs a single voice pipeline per session. The browser connects directly to `ws://localhost:8765`, sends raw 16 kHz PCM, and receives 24 kHz WAV audio back. JSON messages on the same WebSocket carry FSM state updates (mode badge, quiz score, transcript bubbles).

## Prerequisites

- Node.js 20+
- Python 3.11+
- API keys for:
  - [Deepgram](https://console.deepgram.com) — STT (nova-3 multilingual)
  - [Google AI Studio](https://aistudio.google.com) — Gemini LLM + Gemini TTS
  - [Anthropic](https://console.anthropic.com) — Claude Haiku (quiz grader fallback)

## Setup

```bash
# 1. Clone / enter the project
cd voice-tutor

# 2. Install frontend
npm install

# 3. Install backend
cd backend
pip install -r requirements.txt
cd ..

# 4. Configure environment
cp .env.example .env.local          # frontend env
cp .env.example backend/.env        # backend env
# Fill in your API keys in both files

# 5. SQLite DB is created automatically on first run — no migration needed
```

## Running locally

**Terminal 1 — Python Pipecat backend:**
```bash
cd backend
python main.py
# Listening on ws://0.0.0.0:8765
```

**Terminal 2 — Next.js frontend:**
```bash
npm run dev
# Open http://localhost:3000
```

Click the mic button, wait for Sofia's greeting (~2s), then just speak.

## What to say

| You say | What happens |
|---|---|
| "Teach me greetings" | Starts Lesson 1 — structured teaching steps |
| "Quiz me on numbers" | Starts adaptive quiz for Lesson 2 |
| "Let's roleplay at a restaurant" | Sofia becomes a waiter — practice in context |
| "Wait, why is it 'la mesa' not 'el mesa'?" | DOUBT state — Sofia answers, then resumes |
| "What does 'gracias' mean?" | `lookup_vocab` tool returns definition + tip |
| "How am I doing?" | `get_user_progress` — Sofia reads back history |

## Running tests

```bash
cd backend
pytest tests/ -v                    # 42 unit tests

python evaluation/harness.py        # 16-case grader eval, no LLM calls
```

## Measured latency

| Segment | Measured (P50) |
|---|---|
| STT (Deepgram nova-3 streaming) | ~200 ms |
| LLM first token (Gemini 2.5 Flash) | ~600 ms |
| TTS first audio chunk (Gemini streaming) | ~1 800 ms |
| **End-to-end (speech → first audio)** | **~2 600 ms** |

The bottleneck is Gemini TTS — a trade-off for native Spanish pronunciation. Switching to Deepgram Aura TTS cuts this to ~1 800 ms but produces an English accent on Spanish words, which is unacceptable for a pronunciation-focused tutor. See the write-up for full discussion.

## Cost estimate — 5-minute session

| Service | Usage | Est. cost |
|---|---|---|
| Deepgram nova-3 STT | ~5 min audio | ~$0.02 |
| Gemini 2.5 Flash LLM | ~15 turns × ~800 tokens | ~$0.04 |
| Gemini TTS | ~3 min generated audio | ~$0.05 |
| Claude Haiku (grader) | ~10 quiz answers | ~$0.01 |
| **Total** | | **~$0.12** |

## Known limitations

- Single-user only (`user_id = "user-001"` hardcoded — no auth)
- One client at a time (Pipecat WebSocket transport is single-connection)
- Gemini TTS latency (~2.6s) exceeds the 1.5s target — documented trade-off
- No phoneme-level pronunciation scoring (would need Azure Speech or forced aligner)

## What to build next

- Per-phoneme pronunciation scoring
- Spaced repetition (SM-2) for weak-area vocabulary
- Multi-user auth + hosted deployment
- Streaming answer evaluation (grade before user finishes speaking)
- Telephony via Twilio SIP
