"use client";

import { useCallback, useEffect, useRef, useState } from "react";

type Status = "disconnected" | "connecting" | "connected";
type AgentState = "idle" | "teaching" | "quiz" | "doubt" | "roleplay";

interface Bubble {
  id: number;
  speaker: "user" | "agent";
  text: string;
  isDoubt?: boolean;
}

interface VocabEntry { word: string; translation: string; }

interface Stats {
  latencyMs: number;
  turns: number;
  quizScore: string;
  lastStt: string;
}

const LESSON_TITLES: Record<string, string> = {
  "lesson-greetings": "Greetings & Introductions",
  "lesson-numbers": "Numbers & Basic Shopping",
  "lesson-restaurant": "At a Restaurant",
};

const LESSON_VOCAB: Record<string, VocabEntry[]> = {
  "lesson-greetings": [
    { word: "hola", translation: "hello" },
    { word: "buenos días", translation: "good morning" },
    { word: "me llamo", translation: "my name is" },
    { word: "estoy bien", translation: "I'm well" },
    { word: "hasta luego", translation: "see you later" },
  ],
  "lesson-numbers": [
    { word: "¿cuánto cuesta?", translation: "how much?" },
    { word: "quisiera", translation: "I'd like" },
    { word: "por favor", translation: "please" },
    { word: "gracias", translation: "thank you" },
    { word: "de nada", translation: "you're welcome" },
  ],
  "lesson-restaurant": [
    { word: "quisiera", translation: "I'd like" },
    { word: "la cuenta", translation: "the bill" },
    { word: "¿qué recomienda?", translation: "what do you recommend?" },
    { word: "sin / con", translation: "without / with" },
    { word: "¡buen provecho!", translation: "enjoy your meal!" },
  ],
};

const ROLEPLAY_VOCAB: Record<string, VocabEntry[]> = {
  "roleplay-restaurant": [
    { word: "quisiera", translation: "I'd like" },
    { word: "la cuenta", translation: "the bill" },
    { word: "¿qué recomienda?", translation: "recommend?" },
    { word: "sin", translation: "without" },
  ],
  "roleplay-market": [
    { word: "¿cuánto cuesta?", translation: "how much?" },
    { word: "quisiera", translation: "I'd like" },
    { word: "de nada", translation: "you're welcome" },
    { word: "por favor", translation: "please" },
  ],
  "roleplay-greeting": [
    { word: "me llamo", translation: "my name is" },
    { word: "mucho gusto", translation: "nice to meet you" },
    { word: "¿cómo estás?", translation: "how are you?" },
    { word: "hasta luego", translation: "see you later" },
  ],
};

const ROLEPLAY_SCENARIOS = [
  { id: "roleplay-restaurant", label: "At the Restaurant", icon: "ti-chef-hat" },
  { id: "roleplay-market",     label: "At the Market",     icon: "ti-shopping-bag" },
  { id: "roleplay-greeting",   label: "Meeting Someone",   icon: "ti-users" },
];

const NUM_BARS = 30;

export default function Page() {
  const [status, setStatus] = useState<Status>("disconnected");
  const [agentState, setAgentState] = useState<AgentState>("idle");
  const [lessonId, setLessonId] = useState<string | null>(null);
  const [scenarioId, setScenarioId] = useState<string | null>(null);
  const [scenarioTitle, setScenarioTitle] = useState<string | null>(null);
  const [questionType, setQuestionType] = useState<string | null>(null);
  const [bubbles, setBubbles] = useState<Bubble[]>([]);
  const [stats, setStats] = useState<Stats>({ latencyMs: 0, turns: 0, quizScore: "—", lastStt: "" });
  const [progress, setProgress] = useState(0);
  const [dbg, setDbg] = useState<string[]>([]);
  const log = (msg: string) => { console.log("[DBG]", msg); setDbg(p => [...p.slice(-6), msg]); };

  const wsRef = useRef<WebSocket | null>(null);
  const recordCtxRef = useRef<AudioContext | null>(null);
  const playCtxRef = useRef<AudioContext | null>(null);
  const nextPlayTimeRef = useRef<number>(0);
  const streamRef = useRef<MediaStream | null>(null);
  const chatEndRef = useRef<HTMLDivElement | null>(null);
  const barRefs = useRef<HTMLDivElement[]>([]);
  const animRef = useRef<number>(0);
  const idRef = useRef(0);
  const listeningRef = useRef(false);
  const agentStateRef = useRef<AgentState>("idle");

  useEffect(() => { agentStateRef.current = agentState; }, [agentState]);

  const addBubble = useCallback((speaker: "user" | "agent", text: string, isDoubt = false) => {
    setBubbles(prev => [...prev.slice(-24), { id: idRef.current++, speaker, text, isDoubt }]);
  }, []);

  const scheduleAudioChunk = useCallback((buf: ArrayBuffer) => {
    if (!playCtxRef.current || playCtxRef.current.state === "closed") {
      playCtxRef.current = new AudioContext();
      nextPlayTimeRef.current = 0;
    }
    const ctx = playCtxRef.current;
    ctx.resume().then(() => {
      ctx.decodeAudioData(buf.slice(0)).then(decoded => {
        const source = ctx.createBufferSource();
        source.buffer = decoded;
        source.connect(ctx.destination);
        const now = ctx.currentTime;
        const startAt = Math.max(now + 0.005, nextPlayTimeRef.current);
        source.start(startAt);
        nextPlayTimeRef.current = startAt + decoded.duration;
      }).catch(e => log(`decode error: ${e}`));
    });
  }, []);

  const handleServerMsg = useCallback((msg: Record<string, unknown>) => {
    const type = msg.type as string;
    if (type === "state") {
      const s = msg.state as AgentState;
      log(`state → ${s}${msg.lessonId ? ` (${msg.lessonId})` : ""}${msg.scenarioId ? ` [${msg.scenarioId}]` : ""}`);
      setAgentState(s);
      if (s === "roleplay") {
        setScenarioTitle((msg.scenarioTitle as string) ?? null);
        setScenarioId((msg.scenarioId as string) ?? null);
        setQuestionType(null);
      } else if (s === "quiz") {
        setQuestionType((msg.questionType as string) ?? null);
        setScenarioTitle(null);
        setScenarioId(null);
        if (msg.lessonId) setLessonId(msg.lessonId as string);
      } else if (s === "teaching") {
        setQuestionType(null);
        setScenarioTitle(null);
        setScenarioId(null);
        if (msg.lessonId) setLessonId(msg.lessonId as string);
      } else if (s === "doubt") {
        // keep existing lessonId / scenarioId
      } else if (s === "idle") {
        setQuestionType(null);
        setScenarioTitle(null);
        setScenarioId(null);
      }
    } else if (type === "score") {
      const sc = msg.score as number;
      const tot = msg.total as number;
      const idx = msg.index as number;
      setStats(p => ({ ...p, quizScore: `${sc} / ${tot}` }));
      setProgress(tot > 0 ? Math.round((idx / tot) * 100) : 0);
      if (msg.questionType !== undefined) {
        setQuestionType(msg.questionType as string | null);
      }
    } else if (type === "transcript") {
      const speaker = msg.speaker as "user" | "agent";
      const text = msg.text as string;
      const isDoubt = agentStateRef.current === "doubt" && speaker === "agent";
      addBubble(speaker, text, isDoubt);
      if (speaker === "user") {
        setStats(p => ({ ...p, lastStt: text, turns: p.turns + 1 }));
      }
    } else if (type === "latency") {
      setStats(p => ({ ...p, latencyMs: msg.totalMs as number }));
    }
  }, [addBubble]);

  // Waveform animation
  const animateWave = useCallback(() => {
    const t = Date.now();
    barRefs.current.forEach((b, i) => {
      if (!b) return;
      const h = listeningRef.current
        ? 4 + Math.abs(Math.sin(t / 220 + i * 0.45)) * 22
        : 4;
      b.style.height = h + "px";
      b.className = "wave-bar" + (listeningRef.current ? " active" : "");
    });
    animRef.current = requestAnimationFrame(animateWave);
  }, []);

  useEffect(() => {
    animRef.current = requestAnimationFrame(animateWave);
    return () => cancelAnimationFrame(animRef.current);
  }, [animateWave]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [bubbles]);

  const connect = useCallback(async () => {
    if (status !== "disconnected") return;
    setStatus("connecting");
    try { await fetch("/api/ping"); } catch { /* non-fatal */ }
    const wsUrl = process.env.NEXT_PUBLIC_BACKEND_WS_URL ?? "ws://localhost:8765";
    const ws = new WebSocket(wsUrl);
    ws.binaryType = "arraybuffer";
    wsRef.current = ws;

    ws.onopen = async () => {
      log("ws opened");
      setStatus("connected");
      listeningRef.current = true;
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          audio: { channelCount: 1, echoCancellation: true, noiseSuppression: true },
        });
        streamRef.current = stream;
        const ctx = new AudioContext({ sampleRate: 16000 });
        recordCtxRef.current = ctx;
        await ctx.audioWorklet.addModule("/audio-processor.js");
        const source = ctx.createMediaStreamSource(stream);
        const worklet = new AudioWorkletNode(ctx, "audio-processor");
        worklet.port.onmessage = (e: MessageEvent<ArrayBuffer>) => {
          if (ws.readyState === WebSocket.OPEN) ws.send(e.data);
        };
        source.connect(worklet);
        log("mic ready");
      } catch (err) {
        console.error("Mic setup failed:", err);
        alert(`Mic setup failed: ${err instanceof Error ? err.message : err}`);
        ws.close();
      }
    };

    ws.onmessage = (event: MessageEvent) => {
      if (event.data instanceof ArrayBuffer) {
        scheduleAudioChunk(event.data);
      } else if (typeof event.data === "string") {
        try { handleServerMsg(JSON.parse(event.data)); } catch { /* ignore */ }
      }
    };

    ws.onclose = () => {
      listeningRef.current = false;
      setStatus("disconnected");
      streamRef.current?.getTracks().forEach(t => t.stop());
      recordCtxRef.current?.close().catch(() => {});
      recordCtxRef.current = null;
      playCtxRef.current?.close().catch(() => {});
      playCtxRef.current = null;
      nextPlayTimeRef.current = 0;
    };
    ws.onerror = () => ws.close();
  }, [status, handleServerMsg, scheduleAudioChunk]);

  const disconnect = useCallback(() => {
    listeningRef.current = false;
    wsRef.current?.close();
  }, []);

  // Derived display values
  const headerTitle = agentState === "roleplay" && scenarioTitle
    ? scenarioTitle
    : lessonId ? (LESSON_TITLES[lessonId] ?? lessonId)
    : "Connect to start";

  const headerSub = agentState === "idle"
    ? "Say 'teach me greetings' or 'quiz me'"
    : agentState === "roleplay" && scenarioTitle
    ? `Roleplay · ${scenarioTitle}`
    : agentState === "quiz"
    ? `Quiz · ${lessonId ?? "—"} · ${stats.quizScore}`
    : agentState === "teaching"
    ? `Lesson · ${lessonId ?? "—"}`
    : agentState === "doubt"
    ? "Doubt — Sofia is answering your question"
    : agentState;

  const vocab: VocabEntry[] = agentState === "roleplay" && scenarioId
    ? (ROLEPLAY_VOCAB[scenarioId] ?? [])
    : lessonId ? (LESSON_VOCAB[lessonId] ?? [])
    : [];

  const progressPct = agentState === "quiz" ? progress : agentState === "teaching" ? 40 : 0;
  const isListening = agentState === "quiz" && questionType === "listening";

  const activeMode = agentState === "quiz" ? "Quiz"
    : agentState === "roleplay" ? "Roleplay"
    : agentState === "doubt" ? "Doubt"
    : "Lesson";

  const modeIcon: Record<AgentState, string> = {
    idle: "ti-microphone", teaching: "ti-book-2", quiz: "ti-list-check",
    doubt: "ti-help-circle", roleplay: "ti-messages",
  };

  return (
    <div className="app">
      {/* Sidebar */}
      <div className="sidebar">
        <div className="sidebar-logo">
          <div className="name">🇪🇸 LinguaVoice</div>
          <small>Spanish · Beginner</small>
        </div>

        <span className="nav-section">Modes</span>
        {(["Lesson", "Quiz", "Roleplay", "Doubt"] as const).map(m => (
          <div key={m} className={`nav-item${activeMode === m ? " active" : ""}`}>
            <i className={`ti ${m === "Lesson" ? "ti-book-2" : m === "Quiz" ? "ti-list-check" : m === "Roleplay" ? "ti-messages" : "ti-help-circle"}`} />
            {m}
          </div>
        ))}

        <span className="nav-section">Curriculum</span>
        {[
          { id: "lesson-greetings",  label: "Greetings" },
          { id: "lesson-numbers",    label: "Numbers" },
          { id: "lesson-restaurant", label: "Restaurant" },
        ].map(c => {
          const isCurrent = c.id === lessonId && agentState !== "roleplay";
          return (
            <div key={c.id} className={`curriculum-item${isCurrent ? " current" : ""}`}>
              <i className={`ti ${isCurrent ? "ti-player-play" : "ti-circle"}`} />
              {c.label}
            </div>
          );
        })}

        <span className="nav-section">Roleplay</span>
        {ROLEPLAY_SCENARIOS.map(s => {
          const isCurrent = s.id === scenarioId;
          return (
            <div key={s.id} className={`curriculum-item${isCurrent ? " current" : ""}`}>
              <i className={`ti ${s.icon}`} />
              {s.label}
            </div>
          );
        })}

        <div className="progress-card">
          <div className="progress-label">Session progress</div>
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: `${progressPct}%` }} />
          </div>
          <div className="progress-stats">
            <span>{progressPct}% done</span>
            <span>{stats.turns > 0 ? `+${stats.turns * 2} XP` : "0 XP"}</span>
          </div>
        </div>
      </div>

      {/* Main */}
      <div className="main">
        <div className="topbar">
          <div>
            <div className="lesson-title">{headerTitle}</div>
            <div className="lesson-sub">{headerSub}</div>
          </div>
          <div className="mode-chips">
            {["Teaching", "Quiz", "Roleplay"].map(m => (
              <div
                key={m}
                className={`chip${
                  (m === "Teaching" && agentState === "teaching") ||
                  (m === "Quiz" && agentState === "quiz") ||
                  (m === "Roleplay" && agentState === "roleplay")
                    ? " active" : ""
                }`}
              >
                {m}
              </div>
            ))}
          </div>
        </div>

        <div className="content-area">
          {/* Roleplay banner */}
          {agentState === "roleplay" && scenarioTitle && (
            <div className="roleplay-banner">
              <i className="ti ti-messages" />
              <div>
                <div className="roleplay-banner-title">Roleplay: {scenarioTitle}</div>
                <div className="roleplay-banner-sub">Respond in Spanish — Sofia will correct gently and keep the scene going. Say &ldquo;stop&rdquo; to exit.</div>
              </div>
            </div>
          )}

          {/* Listening comprehension indicator */}
          {isListening && (
            <div className="listening-indicator">
              <i className="ti ti-headphones" />
              <span>Listening question — Sofia will say the Spanish phrase. Translate what you hear.</span>
            </div>
          )}

          {bubbles.length === 0 && agentState !== "roleplay" && (
            <div className="empty-state">
              {status === "disconnected"
                ? "Click the mic to connect and start speaking"
                : status === "connecting"
                ? "Connecting…"
                : "Listening — say something to start"}
            </div>
          )}

          {bubbles.length > 0 && (
            <div className="timestamp">
              {new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
            </div>
          )}

          {bubbles.map(b => {
            if (b.isDoubt) {
              return (
                <div key={b.id} className="doubt-banner">
                  <i className="ti ti-alert-circle" style={{ fontSize: 15 }} />
                  <span>{b.text || "Doubt detected — resuming after answer"}</span>
                </div>
              );
            }
            return (
              <div key={b.id} className={`bubble ${b.speaker}`}>
                {b.speaker === "agent" && (
                  <div className="lang-tag">
                    {agentState === "roleplay" ? "Sofia · in character" : agentState === "doubt" ? "Sofia · EN (doubt)" : "Sofia · EN + ES"}
                  </div>
                )}
                {b.text}
              </div>
            );
          })}
          <div ref={chatEndRef} />
        </div>

        {dbg.length > 0 && (
          <div style={{ background: "#111", color: "#0f0", fontFamily: "monospace", fontSize: 11, padding: "6px 12px", borderTop: "1px solid #333" }}>
            {dbg.map((d, i) => <div key={i}>{d}</div>)}
          </div>
        )}

        <div className="voice-bar">
          <button
            className={`mic-btn${status === "connected" ? " listening" : status === "connecting" ? " connecting" : ""}`}
            onClick={status === "disconnected" ? connect : disconnect}
            aria-label={status === "connected" ? "Stop session" : "Start session"}
          >
            <i className={`ti ${status === "connected" ? "ti-microphone" : status === "connecting" ? "ti-loader-2" : "ti-microphone-off"}`} />
          </button>

          <div className="waveform">
            {Array.from({ length: NUM_BARS }).map((_, i) => (
              <div
                key={i}
                className="wave-bar"
                ref={el => { if (el) barRefs.current[i] = el; }}
              />
            ))}
          </div>

          <div className="voice-hint">
            {status === "connected"
              ? agentState === "roleplay"
                ? "Speak Spanish — interrupt anytime"
                : "Say \"quiz me\" or interrupt anytime"
              : status === "connecting"
              ? "Connecting to voice server…"
              : "Click mic to start"}
          </div>
        </div>
      </div>

      {/* Right panel */}
      <div className="right-panel">
        <div>
          <div className="panel-section">
            {agentState === "roleplay" ? "Roleplay vocab" : "Session vocab"}
          </div>
          {vocab.length === 0
            ? <div className="transcript-box" style={{ color: "var(--text-tertiary)" }}>Start a lesson to see vocab</div>
            : vocab.map(v => (
              <div key={v.word} className="vocab-pill">
                {v.word} <span>{v.translation}</span>
              </div>
            ))
          }
        </div>

        <div>
          <div className="panel-section">Turn stats</div>
          <div className="stat-row">
            Latency{" "}
            <strong>
              {stats.latencyMs > 0 ? (
                <><span className={`latency-dot${stats.latencyMs > 1500 ? " warn" : ""}`} />{stats.latencyMs} ms</>
              ) : "—"}
            </strong>
          </div>
          <div className="stat-row">Turns <strong>{stats.turns}</strong></div>
          <div className="stat-row">Quiz score <strong>{stats.quizScore}</strong></div>
        </div>

        <div>
          <div className="panel-section">Last spoken</div>
          <div className="transcript-box">
            {stats.lastStt
              ? <><span className="raw">&ldquo;{stats.lastStt}&rdquo;</span><br /><span style={{ color: "var(--text-tertiary)", fontSize: 10 }}>→ detected</span></>
              : <span style={{ color: "var(--text-tertiary)" }}>Nothing yet</span>
            }
          </div>
        </div>

        <div>
          <div className="panel-section">Agent state</div>
          <div className="transcript-box" style={{ color: "var(--text-primary)", display: "flex", alignItems: "center", gap: 6 }}>
            <i className={`ti ${modeIcon[agentState]}`} style={{ fontSize: 13 }} />
            {agentState.charAt(0).toUpperCase() + agentState.slice(1)}
            {isListening && <span style={{ marginLeft: 4, fontSize: 11, color: "var(--teal-600)" }}>· Listening</span>}
          </div>
        </div>
      </div>
    </div>
  );
}
