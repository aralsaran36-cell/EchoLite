from pydantic import BaseModel, Field


class TurnMetadata(BaseModel):
    session_id: str = Field(..., min_length=1)
    user_transcript: str = ""
    assistant_text: str = ""
    audio_format: str = "wav"


class TextTurnRequest(BaseModel):
    session_id: str = Field(..., min_length=1)
    text: str = Field(..., min_length=1, max_length=2000)


class TurnResponse(BaseModel):
    session_id: str = Field(..., min_length=1)
    user_transcript: str = ""
    assistant_text: str = ""
    audio_format: str = "wav"
    audio_base64: str | None = None
    latency_ms: int | None = None