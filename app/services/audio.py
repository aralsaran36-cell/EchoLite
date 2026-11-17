import io
import shutil
import subprocess
import tempfile
import wave
from pathlib import Path

from app.core.errors import AudioValidationError


ALLOWED_EXTENSIONS = {".wav", ".mp3", ".m4a", ".mp4", ".ogg", ".webm", ".flac"}
ALLOWED_MIME_TYPES = {
    "audio/wav",
    "audio/x-wav",
    "audio/mpeg",
    "audio/mp4",
    "audio/x-m4a",
    "video/mp4",
    "audio/ogg",
    "audio/webm",
    "video/webm",
    "audio/flac",
}

FFMPEG_TIMEOUT_SECONDS = 30


def validate_audio(
    filename: str,
    content_type: str,
    audio_bytes: bytes,
    max_upload_mb: int,
) -> bytes:
    if not audio_bytes:
        raise AudioValidationError("Audio file is empty")

    max_bytes = max_upload_mb * 1024 * 1024

    if len(audio_bytes) > max_bytes:
        raise AudioValidationError(
            f"Audio file is too large. Maximum size is {max_upload_mb} MB"
        )

    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise AudioValidationError(
            f"Unsupported audio format: {extension}"
        )

    base_type = content_type.split(";")[0].strip().lower()

    if base_type not in ALLOWED_MIME_TYPES:
        raise AudioValidationError(
            f"Unsupported content type: {content_type}"
        )

    return audio_bytes


def _wav_duration_seconds(wav_bytes: bytes) -> float:
    with wave.open(io.BytesIO(wav_bytes), "rb") as wav_file:
        return wav_file.getnframes() / float(wav_file.getframerate())


def convert_to_wav(
    audio_bytes: bytes,
    input_extension: str = ".webm",
    max_seconds: float | None = None,
) -> bytes:
    ffmpeg = shutil.which("ffmpeg")

    if ffmpeg is None:
        raise AudioValidationError(
            "FFmpeg is not installed on this system"
        )

    with tempfile.TemporaryDirectory() as temp_dir:
        input_path = Path(temp_dir) / f"input{input_extension}"
        output_path = Path(temp_dir) / "output.wav"

        input_path.write_bytes(audio_bytes)

        try:
            result = subprocess.run(
                [
                    ffmpeg,
                    "-y",
                    "-i",
                    str(input_path),
                    "-ar",
                    "16000",
                    "-ac",
                    "1",
                    str(output_path),
                ],
                capture_output=True,
                check=False,
                timeout=FFMPEG_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired:
            raise AudioValidationError("Audio conversion timed out")

        if result.returncode != 0:
            raise AudioValidationError(
                "Could not convert audio to WAV"
            )

        wav_bytes = output_path.read_bytes()

    if max_seconds is not None:
        try:
            duration = _wav_duration_seconds(wav_bytes)
        except (wave.Error, EOFError):
            raise AudioValidationError("Converted audio is not valid")

        if duration > max_seconds:
            raise AudioValidationError(
                f"Audio is too long. Maximum is {int(max_seconds)} seconds"
            )

    return wav_bytes