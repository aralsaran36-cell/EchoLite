import io
import wave
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.core.errors import AudioValidationError, ModelServerError
from app.services.asr import SeamlessASR, _wav_to_float


def _wav(
    frames: int = 1600,
    rate: int = 16000,
    channels: int = 1,
) -> bytes:
    buffer = io.BytesIO()

    with wave.open(buffer, "wb") as writer:
        writer.setnchannels(channels)
        writer.setsampwidth(2)
        writer.setframerate(rate)
        writer.writeframes(b"\x00\x40" * frames * channels)

    return buffer.getvalue()


def _fake_asr(decoded: str = " What is Java ") -> SeamlessASR:
    asr = SeamlessASR.__new__(SeamlessASR)
    asr.target_lang = "eng"

    fake_tokens = MagicMock()
    fake_tokens.tolist.return_value = [1, 2, 3]

    asr.processor = MagicMock()
    asr.processor.return_value = {"input_features": 1}
    asr.processor.decode.return_value = decoded

    asr.model = MagicMock()
    asr.model.generate.return_value = SimpleNamespace(sequences=[fake_tokens])

    return asr


def test_wav_to_float_valid():
    samples = _wav_to_float(_wav(frames=1600))

    assert samples.shape[0] == 1600
    assert samples.dtype.name == "float32"
    assert abs(samples[0] - 0.5) < 0.01


def test_wav_to_float_wrong_sample_rate():
    with pytest.raises(AudioValidationError):
        _wav_to_float(_wav(rate=8000))


def test_wav_to_float_stereo_rejected():
    with pytest.raises(AudioValidationError):
        _wav_to_float(_wav(channels=2))


def test_wav_to_float_invalid_wav():
    with pytest.raises(AudioValidationError):
        _wav_to_float(b"not-a-wav-file")


def test_transcribe_success():
    asr = _fake_asr(" What is Java ")

    text = asr.transcribe(_wav())

    assert text == "What is Java"
    asr.model.generate.assert_called_once()
    assert asr.model.generate.call_args.kwargs["tgt_lang"] == "eng"


def test_transcribe_empty_audio():
    asr = _fake_asr()

    with pytest.raises(AudioValidationError):
        asr.transcribe(_wav(frames=0))


def test_transcribe_model_failure():
    asr = _fake_asr()
    asr.model.generate.side_effect = RuntimeError("boom")

    with pytest.raises(ModelServerError):
        asr.transcribe(_wav())
