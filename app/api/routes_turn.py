import uuid

from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.config import Settings
from app.core.errors import AudioValidationError
from app.core.session_store import SessionStore
from app.dependencies import (
    get_app_settings,
    get_model_adapter,
    get_session_store,
)
from app.schemas.turn import TurnResponse
from app.services.audio import convert_to_wav, validate_audio
from app.services.model_adapter import LFM3Adapter
from app.services.vad import is_speech

router = APIRouter(
    prefix="/turn",
    tags=["Voice Turn"],
)


@router.post("", response_model=TurnResponse)
async def create_turn(
    session_id: str = Form(...),
    file: UploadFile = File(...),
    session_store: SessionStore = Depends(get_session_store),
    model_adapter: LFM3Adapter = Depends(get_model_adapter),
    settings: Settings = Depends(get_app_settings),
):
    audio_bytes = await file.read()

    validated_audio = validate_audio(
        filename=file.filename or "audio.wav",
        content_type=file.content_type or "audio/wav",
        audio_bytes=audio_bytes,
        max_upload_mb=settings.max_upload_mb,
    )

    wav_bytes = convert_to_wav(
        audio_bytes=validated_audio,
        input_extension=".wav",
    )

    history = session_store.get_history(session_id)

    result = await model_adapter.process_audio(
        audio_bytes=wav_bytes,
        history=history,
    )

    session_store.add_turn(
        session_id=session_id,
        user_text=result["user_transcript"],
        assistant_text=result["assistant_text"],
    )

    return TurnResponse(
        session_id=session_id,
        user_transcript=result["user_transcript"],
        assistant_text=result["assistant_text"],
        audio_format=result["audio_format"],
    )