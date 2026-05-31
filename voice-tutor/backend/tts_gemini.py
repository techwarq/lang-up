from __future__ import annotations
import asyncio
import os
import re
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from typing import Optional

from loguru import logger
from pipecat.frames.frames import ErrorFrame, Frame, TTSAudioRawFrame
from pipecat.services.tts_service import TTSService
from pipecat.services.settings import TTSSettings

from google import genai
from google.genai import types

GEMINI_TTS_SAMPLE_RATE = 24000

_DEFAULT_STYLE = (
    "Speak in a warm, encouraging teacher's voice. "
    "When the text contains Spanish words or phrases, pronounce them with authentic Spanish pronunciation. "
    "English words should sound natural and clear."
)


@dataclass
class GeminiTTSSettings(TTSSettings):
    model: str = "gemini-2.5-flash-preview-tts"
    voice: str = "Kore"
    style_prompt: str = _DEFAULT_STYLE
    language: None = None


class GeminiTTSService(TTSService):
    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        voice: str = "Kore",
        model: str = "gemini-2.5-flash-preview-tts",
        style_prompt: str = _DEFAULT_STYLE,
        **kwargs,
    ):
        super().__init__(
            sample_rate=GEMINI_TTS_SAMPLE_RATE,
            settings=GeminiTTSSettings(voice=voice, model=model, style_prompt=style_prompt),
            push_start_frame=True,
            push_stop_frames=True,
            **kwargs,
        )
        self._client = genai.Client(api_key=api_key or os.environ["GEMINI_API_KEY"])

    async def run_tts(self, text: str, context_id: str) -> AsyncGenerator[Frame | None, None]:
        logger.debug(f"{self}: Generating TTS [{text}]")
        max_retries = 2
        for attempt in range(max_retries + 1):
            try:
                await self.start_ttfb_metrics()
                prompt = f"{self._settings.style_prompt}\n\nText to say: {text}"

                async for chunk in await self._client.aio.models.generate_content_stream(
                    model=self._settings.model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_modalities=["AUDIO"],
                        speech_config=types.SpeechConfig(
                            voice_config=types.VoiceConfig(
                                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                    voice_name=self._settings.voice,
                                )
                            )
                        ),
                    ),
                ):
                    for candidate in (chunk.candidates or []):
                        for part in (candidate.content.parts if candidate.content else []):
                            if part.inline_data and part.inline_data.data:
                                audio = part.inline_data.data
                                # Each streaming chunk may carry its own WAV header — strip every one
                                if audio[:4] == b"RIFF":
                                    audio = audio[44:]
                                if audio:
                                    yield TTSAudioRawFrame(
                                        audio=audio,
                                        sample_rate=self.sample_rate,
                                        num_channels=1,
                                        context_id=context_id,
                                    )

                await self.stop_ttfb_metrics()
                return  # success

            except Exception as e:
                await self.stop_ttfb_metrics()
                err_str = str(e)
                is_rate_limit = "429" in err_str or "RESOURCE_EXHAUSTED" in err_str
                if is_rate_limit and attempt < max_retries:
                    m = re.search(r'"retryDelay":\s*"(\d+)s"', err_str)
                    delay = int(m.group(1)) if m else 30
                    logger.warning(f"{self}: Rate limited — waiting {delay}s (attempt {attempt+1}/{max_retries})")
                    await asyncio.sleep(delay)
                    continue
                logger.error(f"{self}: Gemini TTS error: {e}")
                yield ErrorFrame(error=f"Gemini TTS error: {e}")
                return
