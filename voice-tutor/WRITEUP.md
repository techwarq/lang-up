# Sofia — Technical Write-Up

## 1. What I Built

Sofia is a voice-first Spanish tutor that teaches English-speaking beginners through natural conversation. The learner never types or taps — they just speak. Sofia teaches structured lessons, runs adaptive quizzes, roleplays real-world scenarios, and handles doubts mid-lesson, all through voice.

**AI tools used in development:** Claude Code (Anthropic) assisted with implementation throughout. Every architectural decision, trade-off, and line of code was reviewed and understood before committing.

---

## 2. Architecture

### 2.1 Stack choices

| Layer | Choice | Why |
|---|---|---|
| Orchestration | **Pipecat 1.3** | Maximum control over the in-process pipeline. LiveKit would be better for WebRTC scaling/telephony; for a single-user prototype where every frame matters, Pipecat's explicit processor chain is the right abstraction. |
| LLM | **Gemini 2.5 Flash** | Fast first-token latency, strong function calling, 1M context window for long sessions. Tool calling is the spine of the agent. |
| STT | **Deepgram nova-3 (multilingual)** | Streaming WebSocket API, handles code-switching (English + Spanish in the same utterance) without a language hint, ~200ms latency. |
| TTS | **Gemini TTS (gemini-2.5-flash-preview-tts, streaming)** | Only service tested that produces native Spanish pronunciation. See §3 for the latency trade-off. |
| VAD | **Silero VAD** | Lightweight, accurate, barge-in works within ~300ms of user speech onset. |
| Grader | **Claude Haiku** | Fast, cheap semantic evaluation for quiz answers that don't match exact strings. |
| Persistence | **SQLite (aiosqlite)** | Per-user progress, scores, weak areas. No ops overhead for a prototype. |

### 2.2 Pipeline

```
Browser (AudioWorklet → raw 16kHz PCM)
  │
  ▼ WebSocket (ws://localhost:8765)
WebsocketServerTransport
  │
  ├── input() → SileroVADProcessor → DeepgramSTTService
  │                                        │
  │                              UserTranscriptObserver  ← publishes transcript JSON
  │                                        │
  │                              LLMUserAggregator
  │                                        │
  │                              GoogleLLMService (Gemini 2.5 Flash)
  │                               │   function calls → tool_handlers.dispatch()
  │                               │   → FSM.transition() + SQLite writes
  │                               │
  │                             GeminiTTSService (streaming)
  │                                        │
  │                             AgentTranscriptObserver ← publishes transcript + latency JSON
  │                                        │
  ├── output() ◄──────────────────────────┘
  │
  ▼ WebSocket (24kHz WAV chunks + JSON messages)
Browser (Web Audio API scheduled playback)
```

### 2.3 State machine

The agent runs a five-state FSM: `IDLE → TEACHING → QUIZ → DOUBT → ROLEPLAY`.

- **Why FSM over free-form prompting?** The LLM alone cannot reliably track "which step am I on" across a multi-turn lesson without hallucinating. A deterministic FSM owns state; the LLM owns language. The system prompt is rebuilt from FSM state on every tool call so Sofia always knows exactly where she is.
- **DOUBT** saves `previous_state` and restores it on `resume_after_doubt()` — the LLM never has to track this itself.
- **ROLEPLAY** is orthogonal — it swaps Sofia's persona but doesn't break the lesson state.

### 2.4 Separation of concerns

```
transport/    WebSocket I/O, audio framing (serializer.py)
pipeline/     Processor chain, observer pattern for transcripts
agent/        FSM (fsm.py), prompts (prompts.py), tools (tools.py)
curriculum/   Lessons, quiz questions, roleplay scenarios (curriculum/)
memory/       Short-term (session turns), long-term (SQLite)
evaluation/   Semantic grader (grader.py), harness (harness.py)
```

No hardcoded personality deep in business logic — all agent behaviour lives in `prompts.py` and is parameterised by FSM state + learner history.

---

## 3. Latency

### Measured numbers (P50, local machine)

| Segment | Measured |
|---|---|
| STT (Deepgram nova-3) | ~200 ms |
| LLM first token (Gemini 2.5 Flash) | ~600 ms |
| TTS first audio chunk (Gemini streaming) | ~1 800 ms |
| **End-to-end (end-of-speech → first audio)** | **~2 600 ms** |

The target was 1 500 ms. We exceed it by ~1 100 ms, entirely in TTS.

### The TTS trade-off

Deepgram Aura (`aura-2-luna-en`) hits ~1 800 ms end-to-end but produces an English accent on Spanish words. For a pronunciation tutor this is a non-starter — the learner would learn to mispronounce Spanish.

Gemini TTS (`gemini-2.5-flash-preview-tts`, `Kore` voice) produces native Spanish pronunciation and streams chunks as they are synthesised. Switching from `generate_content` (blocking, one blob) to `generate_content_stream` cuts the perceived latency — the first audio chunk arrives earlier, even if total generation time is the same.

**Honest assessment:** 2.6s is noticeable. In production the fix would be to use a dedicated multilingual TTS service (e.g. Azure Neural TTS with `es-ES-AlvaroNeural`, which streams at ~400ms TTFB) and keep Gemini only for phoneme-rich Spanish segments. Given the 48-hour scope, the Gemini quality/latency trade-off was the right call.

### Barge-in

Silero VAD detects voice onset within ~80ms. The pipeline cancels the current TTS response within ~300ms. This is within spec.

---

## 4. Pedagogical Design

### Lesson structure
Each lesson follows: **Objective → Explanation → Example → Practice → Check-for-understanding** — the same progression Duolingo uses internally. Steps are defined in `curriculum/spanish.py` with explicit `agentScript`, `type`, and `expectsUserResponse` fields. The LLM follows the script but is never locked into verbatim reading — it adapts wording based on context.

### English-first (Duolingo-style)
Sofia always introduces concepts in English first, then gives the Spanish with phonetic spelling: *"The word for 'hello' is 'hola' — say it OH-lah."* This is enforced in the system prompt with positive/negative examples. The phonetic hints also compensate for TTS accent on Spanish words.

### Adaptive teaching
- **Per-session:** `session_mistakes` accumulates incorrect quiz answers. The system prompt includes them so Sofia references them by name when they come up again.
- **Cross-session:** `past_weak_areas` is loaded from SQLite at startup and injected into the system prompt. Sofia's greeting changes for returning learners: she names the weak items and promises to revisit them.

### Doubt handling
The learner can interrupt any time. The FSM saves `previous_state` → transitions to `DOUBT` → the LLM answers → `resume_after_doubt()` restores the prior state. The LLM is instructed to end every doubt response by calling the tool (not by deciding itself when to return).

---

## 5. Quiz Engine

Three question types:
1. **Translation EN→ES** — learner says the Spanish
2. **Translation ES→EN (listening comprehension)** — Sofia speaks the Spanish phrase; learner translates
3. **Spoken response** — open-ended (e.g. "order something politely in Spanish")

Grading is two-tier:
1. **Local normalisation** — lowercase, strip punctuation, check against expected + accepted variants. No LLM call needed for exact/near-exact matches (~60% of answers).
2. **Claude Haiku semantic fallback** — for paraphrases and partial answers. Lenient on minor misspellings (spoken responses), strict on wrong vocabulary and gender (`el`/`la`).

---

## 6. Code-Switching

Spanish learners naturally mix languages: *"How do I say buenos días again?"* Deepgram nova-3 with `language=multi` transcribes both languages in a single utterance without requiring a language hint. The raw transcript is passed to the LLM unchanged — code-switching is handled at the semantic level, not the transcript level.

For TTS, the style prompt instructs Gemini: *"When the text contains Spanish words, pronounce them with authentic Spanish pronunciation. English words should sound natural and clear."* This produces a bilingual voice that sounds different for Spanish vs English segments.

---

## 7. Reliability & Observability

- **STT/TTS/LLM failures** are caught per-turn; Gemini TTS retries with exponential backoff on 429s.
- **WebSocket reconnects** reset the conversation context cleanly without accumulating stale history.
- **Per-turn debug log** visible in the UI (bottom bar) and in the backend terminal — shows state transitions, tool calls, and latency.
- **SQLite** is written at quiz completion and on `save_progress()` tool call — progress survives crashes.

---

## 8. Known Limitations

| Limitation | Why / Trade-off |
|---|---|
| Latency ~2.6s (target 1.5s) | Gemini TTS quality over speed; fixable with Azure Neural TTS |
| No phoneme-level pronunciation scoring | Requires Azure Speech SDK or forced aligner — out of 48h scope |
| Single-user (`user_id = "user-001"`) | Auth is out of scope per the brief |
| One WebSocket client at a time | Pipecat's `WebsocketServerTransport` is single-connection by design |
| Gemini TTS is a preview API | May change or rate-limit without notice |

---

## 9. What I'd Build Next

1. **Azure Neural TTS** for `es-ES` — brings latency under 1s while preserving pronunciation quality
2. **Phoneme-level pronunciation scoring** — Azure Speech Pronunciation Assessment gives per-phoneme accuracy so feedback can be *"your /r/ in 'gracias' needs more roll"* not just *"try again"*
3. **Spaced repetition (SM-2)** — schedule weak-area vocabulary for review across sessions
4. **Multi-user auth** — NextAuth + per-user SQLite rows
5. **Streaming evaluation** — begin grading before the user finishes speaking using partial STT transcripts

---

## 10. Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    Browser (Next.js)                     │
│  AudioWorklet ──► raw 16kHz PCM ──► WebSocket send       │
│  WebSocket recv ──► WAV chunks ──► Web Audio API         │
│  JSON messages ──► React state ──► UI (FSM badge, score) │
└────────────────────────┬────────────────────────────────┘
                         │ ws://localhost:8765
┌────────────────────────▼────────────────────────────────┐
│               Pipecat Pipeline (Python)                  │
│                                                          │
│  WebsocketServerTransport                                │
│       │                                                  │
│  SileroVADProcessor ──► (barge-in cancels downstream)    │
│       │                                                  │
│  DeepgramSTTService (nova-3, multilingual, streaming)    │
│       │                                                  │
│  UserTranscriptObserver ──► publish JSON to browser      │
│       │                                                  │
│  LLMUserAggregator                                       │
│       │                                                  │
│  GoogleLLMService (Gemini 2.5 Flash)                     │
│       │  tool calls                                      │
│       ▼                                                  │
│  ┌────────────────────────────────────────┐              │
│  │           Agent Core                   │              │
│  │  FSM (IDLE/TEACHING/QUIZ/DOUBT/        │              │
│  │        ROLEPLAY)                       │              │
│  │  11 tools: start_lesson,               │              │
│  │    advance_lesson_step, start_quiz,    │              │
│  │    grade_answer, handle_doubt,         │              │
│  │    resume_after_doubt, save_progress,  │              │
│  │    get_user_progress, lookup_vocab,    │              │
│  │    start_roleplay, end_roleplay        │              │
│  │                                        │              │
│  │  Curriculum: 3 lessons + 3 roleplay    │              │
│  │  Memory: ShortTermMemory (session)     │              │
│  │          SQLite (cross-session)        │              │
│  │  Grader: Claude Haiku (semantic)       │              │
│  └────────────────────────────────────────┘              │
│       │                                                  │
│  GeminiTTSService (streaming, multilingual)              │
│       │                                                  │
│  AgentTranscriptObserver ──► publish JSON to browser     │
│       │                                                  │
│  WebsocketServerTransport output                         │
│       │ 24kHz WAV chunks + JSON                          │
└───────┴─────────────────────────────────────────────────┘
                         │
                    Browser plays audio
```
