from __future__ import annotations
import os
import time
from typing import Callable, Awaitable

from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineTask, PipelineParams
from pipecat.transports.websocket.server import WebsocketServerTransport, WebsocketServerParams
from pipecat.services.deepgram.stt import DeepgramSTTService
from tts_gemini import GeminiTTSService, _DEFAULT_STYLE
from pipecat.services.google.llm import GoogleLLMService
from serializer import RawFrameSerializer
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.processors.audio.vad_processor import VADProcessor
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import LLMContextAggregatorPair
from pipecat.adapters.schemas.function_schema import FunctionSchema
from pipecat.adapters.schemas.tools_schema import ToolsSchema
from pipecat.frames.frames import (
    Frame, LLMContextFrame, OutputTransportMessageFrame,
    OutputTransportMessageUrgentFrame, TranscriptionFrame, TTSTextFrame,
)
from pipecat.processors.frame_processor import FrameProcessor, FrameDirection
from pipecat.services.llm_service import FunctionCallParams

from fsm import StateMachine, AgentState
from memory.short_term import ShortTermMemory
from prompts import get_system_prompt
import tools as tool_handlers
from tools import ToolContext, TOOL_DEFINITIONS


class UserTranscriptObserver(FrameProcessor):
    """Intercepts TranscriptionFrame (STT output) before the LLM aggregator consumes it."""

    def __init__(self, publish_fn: Callable[[dict], Awaitable[None]], turn_start_ref: list):
        super().__init__()
        self._publish = publish_fn
        self._turn_start_ref = turn_start_ref  # mutable list[float] shared with AgentObserver

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)
        if isinstance(frame, TranscriptionFrame):
            self._turn_start_ref[0] = time.time()
            await self._publish({"type": "transcript", "speaker": "user", "text": frame.text})
        await self.push_frame(frame, direction)


class AgentTranscriptObserver(FrameProcessor):
    """Intercepts TTSTextFrame after TTS generates it, before it reaches the output transport."""

    def __init__(self, publish_fn: Callable[[dict], Awaitable[None]], turn_start_ref: list):
        super().__init__()
        self._publish = publish_fn
        self._turn_start_ref = turn_start_ref

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)
        if isinstance(frame, TTSTextFrame) and frame.text.strip():
            latency_ms = int((time.time() - self._turn_start_ref[0]) * 1000) if self._turn_start_ref[0] else 0
            await self._publish({"type": "transcript", "speaker": "agent", "text": frame.text})
            if latency_ms > 0:
                await self._publish({"type": "latency", "totalMs": latency_ms})
                self._turn_start_ref[0] = 0.0
        await self.push_frame(frame, direction)


def _build_greeting(ctx) -> str:
    if ctx.past_total_sessions == 0:
        return (
            "Greet the learner warmly in English. Introduce yourself as Sofia their Spanish tutor. "
            "Tell them you'll always explain things in English first, then give them the Spanish. "
            "Ask which lesson they'd like to start with — greetings, numbers, or the restaurant — or if they want to jump straight into a quiz."
        )
    # Returning learner — Sofia knows their history
    parts = ["Welcome back the learner in English. Tell them you remember them."]
    if ctx.past_lessons_completed:
        parts.append(f"Mention they've already worked on: {', '.join(ctx.past_lessons_completed)}.")
    if ctx.past_weak_areas:
        areas = ", ".join(ctx.past_weak_areas[:4])
        parts.append(
            f"Tell them you noticed they found these tricky last time: {areas}. "
            "Promise to focus on those today."
        )
    parts.append("Ask what they want to do: continue a lesson, take a quiz, or try a roleplay conversation.")
    return " ".join(parts)


def _build_tools_schema() -> ToolsSchema:
    schemas = []
    for tool in TOOL_DEFINITIONS:
        props = tool["input_schema"].get("properties", {})
        req = tool["input_schema"].get("required", [])
        schemas.append(
            FunctionSchema(
                name=tool["name"],
                description=tool["description"],
                properties=props,
                required=req,
            )
        )
    return ToolsSchema(standard_tools=schemas)


async def create_task_and_runner(
    fsm: StateMachine,
    short_term: ShortTermMemory,
    user_id: str,
    session_id: str,
) -> tuple[PipelineTask, PipelineRunner, WebsocketServerTransport]:
    transport = WebsocketServerTransport(
        host=os.getenv("WS_HOST", "0.0.0.0"),
        port=int(os.getenv("WS_PORT", "8765")),
        params=WebsocketServerParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            add_wav_header=True,
            audio_in_sample_rate=16000,
            audio_out_sample_rate=24000,
            serializer=RawFrameSerializer(),
        ),
    )

    stt = DeepgramSTTService(
        api_key=os.environ["DEEPGRAM_API_KEY"],
        settings=DeepgramSTTService.Settings(
            model="nova-3",
            language="multi",
        ),
    )

    llm = GoogleLLMService(
        api_key=os.environ["GEMINI_API_KEY"],
        settings=GoogleLLMService.Settings(model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash")),
    )

    tts = GeminiTTSService(
        api_key=os.environ["GEMINI_API_KEY"],
        model=os.getenv("GEMINI_TTS_MODEL", "gemini-2.5-flash-preview-tts"),
        voice=os.getenv("GEMINI_TTS_VOICE", "Kore"),
        style_prompt=os.getenv("GEMINI_TTS_STYLE", _DEFAULT_STYLE),
    )

    vad = VADProcessor(vad_analyzer=SileroVADAnalyzer())

    system_prompt = get_system_prompt(AgentState.IDLE, fsm.context)
    context = LLMContext(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": _build_greeting(fsm.context)},
        ],
        tools=_build_tools_schema(),
    )
    context_pair = LLMContextAggregatorPair(context)

    # task is assigned below; publish_state only called at runtime so the closure is safe
    task: PipelineTask  # forward reference for the closure

    async def publish_state(msg: dict) -> None:
        await task.queue_frames([OutputTransportMessageUrgentFrame(message=msg)])

    turn_start_ref: list = [0.0]
    user_observer = UserTranscriptObserver(publish_state, turn_start_ref)
    agent_observer = AgentTranscriptObserver(publish_state, turn_start_ref)

    pipeline = Pipeline(
        [
            transport.input(),
            vad,
            stt,
            user_observer,
            context_pair.user(),
            llm,
            tts,
            agent_observer,
            transport.output(),
            context_pair.assistant(),
        ]
    )

    runner = PipelineRunner(handle_sigint=True)
    task = PipelineTask(
        pipeline,
        params=PipelineParams(),
        idle_timeout_secs=None,
    )

    tool_ctx = ToolContext(
        fsm=fsm,
        short_term=short_term,
        user_id=user_id,
        session_id=session_id,
        publish_state=publish_state,
    )

    async def on_tool_call(params: FunctionCallParams) -> None:
        result = await tool_handlers.dispatch(params.function_name, dict(params.arguments), tool_ctx)
        new_prompt = get_system_prompt(fsm.current_state, fsm.context)
        if context.messages and context.messages[0].get("role") == "system":
            context.messages[0]["content"] = new_prompt
        await params.result_callback(result)

    llm.register_function(None, on_tool_call)

    @transport.event_handler("on_client_connected")
    async def on_client_connected(transport_obj, client):
        context.messages.clear()
        context.messages.append({"role": "system", "content": get_system_prompt(AgentState.IDLE, fsm.context)})
        context.messages.append({"role": "user", "content": _build_greeting(fsm.context)})
        await task.queue_frames([LLMContextFrame(context=context)])

    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport_obj, client):
        pass

    return task, runner, transport
