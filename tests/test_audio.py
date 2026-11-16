import io
import shutil

import pytest

from app.core.errors import AudioValidationError
from app.services.audio import validate_audio


def make_wav_bytes() -> bytes:
    buffer = io.BytesIO()

    buffer.write(b"RIFF")
    buffer.write((36).to_bytes(4, "little"))
    buffer.write(b"WAVE")
    buffer.write(b"fmt ")
    buffer.write((16).to_bytes(4, "little"))
    buffer.write((1).to_bytes(2, "little"))
    buffer.write((1).to_bytes(2, "little"))
    buffer.write((16000).to_bytes(4, "little"))
    buffer.write((32000).to_bytes(4, "little"))
    buffer.write((2).to_bytes(2, "little"))
    buffer.write((16).to_bytes(2, "little"))
    buffer.write(b"data")
    buffer.write((0).to_bytes(4, "little"))

    return buffer.getvalue()


def test_valid_wav_is_accepted():
    audio_bytes = make_wav_bytes()

    result = validate_audio(
        filename="test.wav",
        content_type="audio/wav",
        audio_bytes=audio_bytes,
        max_upload_mb=10,
    )

    assert result == audio_bytes


def test_empty_audio_is_rejected():
    with pytest.raises(AudioValidationError):
        validate_audio(
            filename="test.wav",
            content_type="audio/wav",
            audio_bytes=b"",
            max_upload_mb=10,
        )


def test_oversize_audio_is_rejected():
    audio_bytes = b"x" * (11 * 1024 * 1024)

    with pytest.raises(AudioValidationError):
        validate_audio(
            filename="test.wav",
            content_type="audio/wav",
            audio_bytes=audio_bytes,
            max_upload_mb=10,
        )


def test_invalid_extension_is_rejected():
    audio_bytes = make_wav_bytes()

    with pytest.raises(AudioValidationError):
        validate_audio(
            filename="test.txt",
            content_type="audio/wav",
            audio_bytes=audio_bytes,
            max_upload_mb=10,
        )


def test_invalid_mime_type_is_rejected():
    audio_bytes = make_wav_bytes()

    with pytest.raises(AudioValidationError):
        validate_audio(
            filename="test.wav",
            content_type="text/plain",
            audio_bytes=audio_bytes,
            max_upload_mb=10,
        )


def test_ffmpeg_available():
    ffmpeg = shutil.which("ffmpeg")

    if ffmpeg is None:
        pytest.skip("FFmpeg is not installed")

    assert ffmpeg is not None