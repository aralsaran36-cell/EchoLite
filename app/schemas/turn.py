from pydantic import BaseModel, Field


class TurnMetadata(BaseModel):
    session_id: str = Field(..., min_length=1)
    user_transcript: str = ""
    assistant_text: str = ""
    audio_format: str = "wav"


class TurnResponse(BaseModel):
    session_id: str = Field(..., min_length=1)
    user_transcript: str = ""
    assistant_text: str = ""
    audio_format: str = "wav"