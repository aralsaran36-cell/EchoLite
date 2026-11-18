import asyncio
import base64
import logging
import time
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.config import Settings, get_settings
from app.core.errors import AudioValidationError, ModelServerError
from app.core.logging import get_logger
from app.core.session_store import SessionStore
from app.dependencies import (
    get_app_settings,
    get_asr,
    get_model_adapter,
    get_session_store,
    get_translator,
)
from app.schemas.turn import TextTurnRequest, TurnResponse
from app.services.audio import convert_to_wav, validate_audio
from app.services.model_adapter import LFM3Adapter

logger: logging.Logger = get_logger(__name__, get_settings())

router = APIRouter(
    prefix="/turn",
    tags=["Voice Turn"],
)

CONTENT_TYPE_EXTENSIONS = {
    "audio/wav": ".wav",
    "audio/x-wav": ".wav",
    "audio/webm": ".webm",
    "audio/mp4": ".mp4",
    "audio/mpeg": ".mp3",
    "audio/ogg": ".ogg",
}


def _input_extension(filename: str | None, content_type: str | None) -> str:
    suffix = Path(filename or "").suffix.lower()
    if suffix:
        return suffix
    base_type = (content_type or "").split(";")[0].strip().lower()
    return CONTENT_TYPE_EXTENSIONS.get(base_type, ".wav")


def _elapsed_ms(started: float) -> int:
    return int((time.perf_counter() - started) * 1000)


def _encode_audio(audio_bytes: bytes | None) -> str | None:
    if not audio_bytes:
        return None
    return base64.b64encode(audio_bytes).decode("ascii")


@router.post("", response_model=TurnResponse)
async def create_turn(
    session_id: str = Form(...),
    file: UploadFile = File(...),
    session_store: SessionStore = Depends(get_session_store),
    model_adapter: LFM3Adapter = Depends(get_model_adapter),
    asr=Depends(get_asr),
    settings: Settings = Depends(get_app_settings),
):
    started = time.perf_counter()

    audio_bytes = await file.read()

    validated_audio = await asyncio.to_thread(
        validate_audio,
        file.filename or "audio.wav",
        file.content_type or "audio/wav",
        audio_bytes,
        settings.max_upload_mb,
    )

    wav_bytes = await asyncio.to_thread(
        convert_to_wav,
        validated_audio,
        _input_extension(file.filename, file.content_type),
        settings.max_audio_seconds,
    )

    history = session_store.get_history(session_id)

    try:
        transcript = await asyncio.to_thread(asr.transcribe, wav_bytes)

        if not transcript:
            raise AudioValidationError("No speech understood. Please try again.")

        result = await model_adapter.process_audio(
            transcript=transcript,
            history=history,
        )
    except ModelServerError:
        logger.exception("Model call failed")
        raise HTTPException(
            status_code=502,
            detail="Model server error. Please try again.",
        )

    session_store.add_turn(
        session_id=session_id,
        user_text=result["user_transcript"],
        assistant_text=result["assistant_text"],
    )

    latency_ms = _elapsed_ms(started)
    logger.info("Voice turn finished in %d ms", latency_ms)

    return TurnResponse(
        session_id=session_id,
        user_transcript=result["user_transcript"],
        assistant_text=result["assistant_text"],
        audio_format=result.get("audio_format", "wav"),
        audio_base64=_encode_audio(result.get("audio_bytes")),
        latency_ms=latency_ms,
    )


@router.post("/text", response_model=TurnResponse)
async def create_text_turn(
    body: TextTurnRequest,
    session_store: SessionStore = Depends(get_session_store),
    model_adapter: LFM3Adapter = Depends(get_model_adapter),
    translator=Depends(get_translator),
):
    started = time.perf_counter()

    history = session_store.get_history(body.session_id)

    try:
        english_text = await asyncio.to_thread(translator.translate, body.text)

        result = await model_adapter.process_text(
            text=english_text,
            history=history,
        )
    except ModelServerError:
        logger.exception("Model call failed")
        raise HTTPException(
            status_code=502,
            detail="Model server error. Please try again.",
        )

    session_store.add_turn(
        session_id=body.session_id,
        user_text=english_text,
        assistant_text=result["assistant_text"],
    )

    latency_ms = _elapsed_ms(started)
    logger.info("Text turn finished in %d ms", latency_ms)

    return TurnResponse(
        session_id=body.session_id,
        user_transcript=body.text,
        assistant_text=result["assistant_text"],
        audio_format=result.get("audio_format", "wav"),
        audio_base64=_encode_audio(result.get("audio_bytes")),
        latency_ms=latency_ms,
    )
