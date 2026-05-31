from __future__ import annotations
import json

from pipecat.frames.frames import (
    Frame,
    InputAudioRawFrame,
    InputTransportMessageFrame,
    OutputAudioRawFrame,
    OutputTransportMessageFrame,
    OutputTransportMessageUrgentFrame,
)
from pipecat.serializers.base_serializer import FrameSerializer


class RawFrameSerializer(FrameSerializer):
    """Serializer that sends audio as raw bytes and JSON messages as text strings.

    The frontend sends raw 16kHz mono PCM audio and expects to receive:
    - Binary frames: WAV audio bytes (transport already adds the WAV header)
    - Text frames: JSON-encoded message dicts
    """

    def __init__(self):
        super().__init__(FrameSerializer.InputParams(ignore_rtvi_messages=True))

    async def serialize(self, frame: Frame) -> str | bytes | None:
        if isinstance(frame, OutputAudioRawFrame):
            return frame.audio
        if isinstance(frame, (OutputTransportMessageFrame, OutputTransportMessageUrgentFrame)):
            if self.should_ignore_frame(frame):
                return None
            return json.dumps(frame.message)
        return None

    async def deserialize(self, data: str | bytes) -> Frame | None:
        if isinstance(data, bytes):
            return InputAudioRawFrame(
                audio=data,
                sample_rate=16000,
                num_channels=1,
            )
        if isinstance(data, str):
            try:
                msg = json.loads(data)
                return InputTransportMessageFrame(message=msg)
            except Exception:
                return None
        return None
