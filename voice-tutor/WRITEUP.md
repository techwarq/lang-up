# Sofia — Technical Write-Up

**AI tools used:** Claude Code assisted throughout. Every decision below is mine and I can defend each one.

---

## Why this approach

I wanted to build something that could actually teach a language, not just chat about one. The difference matters. A chatbot can discuss Spanish grammar forever without the learner ever getting a rep in. Real teaching is structured: introduce, demonstrate, make them say it, give specific feedback, move on. So the first decision was to anchor everything in a curriculum and a state machine, then give the LLM language — not control.

That one decision shaped the entire architecture.

---

## Pipecat, not LiveKit

The brief asks me to defend this choice. Here's the honest version:

LiveKit is the right call if you're building multi-room WebRTC infrastructure — conferencing, telephony, anything where you need server-side media routing at scale. For this project, I have one user, one pipeline, and I want to see every frame. Pipecat's processor chain is transparent in a way LiveKit's SDK isn't — I can insert an observer anywhere in the graph and inspect exactly what's flowing. That transparency paid off twice during debugging (see §6).

The downside of Pipecat is that it's moving fast. The jump from 0.0.36 to 1.3.0 broke things silently (more on that below). LiveKit's APIs are more stable. That's the actual trade-off.

---

## Architecture

The pipeline is a linear chain of processors:

```
Browser mic (AudioWorklet, 16kHz PCM)
  → WebSocket
  → Silero VAD          — detects speech onset/end
  → Deepgram STT        — streams partial → final transcripts
  → UserObserver        — publishes transcript to browser as JSON
  → LLM Aggregator      — collects turn, builds context frame
  → Gemini 2.5 Flash    — LLM; calls tools instead of guessing state
  → Gemini TTS          — streams 24kHz audio chunks
  → AgentObserver       — publishes transcript + latency to browser
  → WebSocket output
  → Browser (Web Audio API scheduled playback)
```

One WebSocket carries everything: binary audio in both directions, plus JSON metadata (state changes, transcripts, latency, quiz scores) as urgent frames that jump the queue ahead of audio.

The `RawFrameSerializer` is a custom 6-line class that tells Pipecat's transport to treat binary messages as raw audio frames and string messages as JSON. Without it, Pipecat expects RTVI protocol frames, which our browser doesn't speak.

### State machine

The agent has five states: `IDLE`, `TEACHING`, `QUIZ`, `DOUBT`, `ROLEPLAY`.

I could have let the LLM track state in the conversation history. I didn't because I've seen what happens — the LLM eventually loses the thread of "which lesson step am I on" in a long session and starts guessing. With an FSM, the state is deterministic and I rebuild the system prompt from it on every tool call. The LLM knows exactly where it is because the prompt tells it where it is, not because it's inferring from history.

`DOUBT` is the one interesting state. When the learner asks a question mid-lesson, the FSM snapshots `previous_state` and transitions to `DOUBT`. After Sofia answers, she calls `resume_after_doubt()` and the FSM restores the snapshot. The LLM doesn't need to track this — it just follows instructions and calls the tool.

### The tool spine

There are 11 tools. The important ones:

- `start_lesson(lessonId)` — transitions FSM, loads curriculum step 0
- `advance_lesson_step()` — moves through the script; FSM owns the index
- `start_quiz(lessonId)` — loads questions, transitions to QUIZ
- `grade_answer(answer, questionId)` — this is the load-bearing one (see §4)
- `handle_doubt()` / `resume_after_doubt()` — state snapshot/restore
- `save_progress(score, weakAreas)` — writes to SQLite

The rule: the LLM is responsible for *what to say*, not *what state things are in*. State belongs to the FSM. Progress belongs to SQLite. Language belongs to the LLM.

---

## Memory

Two layers:

**Session (in-memory):** `ShortTermMemory` holds vocabulary introduced this session and mistakes made this session. Both get injected into the system prompt so Sofia can say "you got the verb ending wrong earlier, let's watch that."

**Cross-session (SQLite):** At session start, I load the user's completed lessons, weak areas (derived from quiz mistakes across all sessions), and session count. Sofia's greeting changes based on this. First session: warm intro, explains the format. Returning learner: "you found *ser/estar* tricky last time, let's work on that today."

The schema is four tables: `users` (profile), `sessions`, `user_progress` (lesson scores + weak areas), `turn_logs` (per-turn latency + tools called). Small enough for SQLite. No ops overhead. Progress survives crashes because it's written at quiz completion, not at session end.

---

## The grader

This was the most deliberate design decision.

The obvious approach: ask the LLM to grade answers. I didn't do this for two reasons. First, it's slow — a Gemini round-trip for every answer adds 600ms+ to what should be instant feedback. Second, LLMs hallucinate grades. In testing, Claude 3 Sonnet passed a clearly wrong answer ("buenos dios" for "buenos días") because it decided the intent was right. A tutor that passes wrong pronunciation is not a tutor.

The grader is two-tier:

1. **Local check:** normalise case and punctuation, check against expected answer + accepted variants. If it matches, grade immediately. This handles ~60% of answers with zero latency and zero cost.

2. **Claude Haiku fallback:** for answers that don't match locally — paraphrases, partial answers, misspellings. The prompt is strict: wrong vocabulary fails regardless of intent. `el`/`la` gender errors fail. But minor transcription artifacts ("buenos dias" without the accent) pass.

The harness in `evaluation/harness.py` has 16 test cases. All 42 tests pass.

---

## Latency

Honest numbers (P50, MacBook Pro, good connection):

| Segment | Time |
|---|---|
| Deepgram STT (streaming, end-of-utterance) | ~200ms |
| Gemini 2.5 Flash first token | ~600ms |
| Gemini TTS first audio chunk | ~1 800ms |
| **End-to-end** | **~2 600ms** |

Target was 1 500ms. The gap is entirely TTS.

I tried Deepgram Aura first. It hits ~400ms TTFB but produces a flat American accent on Spanish words. For a pronunciation tutor, teaching learners to say "OH-lah" in an American accent is worse than having latency. So I switched to Gemini TTS, which produces native Spanish pronunciation, and mitigated the latency by streaming — the first chunk arrives before synthesis is complete, so perceived latency is lower than the total generation time.

The right long-term fix is Azure Neural TTS with `es-ES-AlvaroNeural` — it streams at ~400ms TTFB and the Spanish pronunciation is native quality. I didn't use it because I'd already hit my API key budget and it needs a separate Azure account. In production this is a one-line swap.

**Barge-in:** Silero VAD detects speech onset within ~80ms. The pipeline cancels the active TTS response. This is within spec and it works — I tested it by interrupting Sofia mid-sentence.

---

## Two bugs worth describing

**Bug 1: Gemini TTS chirping**

Every streamed chunk from `generate_content_stream` includes a 44-byte WAV header, not just the first one. I was only stripping the header from the first chunk. The browser's Web Audio API tried to decode raw PCM as WAV on every subsequent chunk and produced a chirp on each boundary. The fix is one line — check for `b"RIFF"` magic bytes on every chunk, not just the first. Cost me three hours.

**Bug 2: Pipecat 1.3.0 RTVIProcessor**

Upgrading from Pipecat 0.0.36 to 1.3.0, the LLM stopped responding even though STT was working. The pipeline links showed `RTVIProcessor` being inserted between `PipelineTask` and the pipeline. In 1.3.0, `PipelineTask` auto-injects an RTVI protocol processor that holds the pipeline in a waiting state until it receives an RTVI handshake frame. Our browser sends raw binary audio, never the handshake. The fix: `enable_rtvi=False` in `PipelineTask`. One parameter. Six hours to find it because there's no warning in the logs — the pipeline just silently waits.

Both bugs are the kind that documentation doesn't cover. You find them by reading source code.

---

## What I'd build next

**Immediate (would do if I had another day):**
- Wire per-turn latency to SQLite properly so you can query "why was turn 14 slow?" (the schema and logger exist; the call sites in the pipeline don't)
- Azure Neural TTS — brings latency under 1s, preserves pronunciation quality

**Meaningful improvements:**
- Phoneme-level pronunciation scoring via Azure Speech Assessment — gives per-phoneme accuracy so feedback is "your *r* in *gracias* needs more roll" not "try again"
- Spaced repetition (SM-2 algorithm) on weak areas across sessions — right now weak areas accumulate but aren't scheduled for review
- Streaming grading — start evaluating before the user finishes speaking using partial STT transcripts

**What I'd rethink:**
- Gemini TTS as the primary voice service — the quality is great but it's a preview API, rate limits are unpredictable, and the streaming behavior changed once during development
- SQLite is fine for one user. For multi-user with concurrent sessions it needs to become Postgres

---

## Known limitations

- **2.6s latency** — real, documented above, fixable
- **Single-user server** — Pipecat's WS transport is one connection by design; multi-user needs a process-per-session model or a different transport
- **Spanish-only curriculum** — French/German/Portuguese are supported via dynamic LLM generation but there's no structured quiz engine for them
- **Turn logger not fully wired** — the schema and logger class exist and write to SQLite, but the call sites in the pipeline observers don't invoke them yet; latency shows in the UI in real-time but isn't persisted per-turn
