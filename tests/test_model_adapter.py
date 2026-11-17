import io
import wave

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import httpx

from app.core.errors import ModelServerError
from app.services.model_adapter import (
    LFM3Adapter,
    _clean_for_tts,
    _split_sentences,
)


def _chat_response(content: str) -> MagicMock:
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = {
        "choices": [{"message": {"content": content}}]
    }
    return response


def _tts_response(audio: bytes) -> MagicMock:
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.content = audio
    return response


def _wav_bytes(frames: int = 100) -> bytes:
    buffer = io.BytesIO()

    with wave.open(buffer, "wb") as writer:
        writer.setnchannels(1)
        writer.setsampwidth(2)
        writer.setframerate(24000)
        writer.writeframes(b"\x00\x00" * frames)

    return buffer.getvalue()


async def test_process_audio_success():
    adapter = LFM3Adapter(base_url="http://127.0.0.1:8080")

    with patch(
        "app.services.model_adapter.httpx.AsyncClient"
    ) as mock_client_class:
        mock_client = MagicMock()
        mock_client.post = AsyncMock(
            side_effect=[
                _chat_response("What is Java"),
                _chat_response("Java is a programming language."),
                _tts_response(b"fake-wav-audio"),
            ]
        )
        mock_client_class.return_value.__aenter__.return_value = mock_client

        result = await adapter.process_audio(
            audio_bytes=b"fake-audio",
            history=[],
        )

    assert mock_client.post.await_count == 3
    assert result["user_transcript"] == "What is Java"
    assert result["assistant_text"] == "Java is a programming language."
    assert result["audio_bytes"] == b"fake-wav-audio"
    assert result["audio_format"] == "wav"


async def test_process_text_success():
    adapter = LFM3Adapter(base_url="http://127.0.0.1:8080")

    with patch(
        "app.services.model_adapter.httpx.AsyncClient"
    ) as mock_client_class:
        mock_client = MagicMock()
        mock_client.post = AsyncMock(
            side_effect=[
                _chat_response("Excel is a spreadsheet app."),
                _tts_response(b"fake-wav-audio"),
            ]
        )
        mock_client_class.return_value.__aenter__.return_value = mock_client

        result = await adapter.process_text(
            text="What is Excel",
            history=[],
        )

    assert mock_client.post.await_count == 2
    assert result["assistant_text"] == "Excel is a spreadsheet app."
    assert result["audio_bytes"] == b"fake-wav-audio"
    assert result["audio_format"] == "wav"


async def test_process_audio_http_error():
    adapter = LFM3Adapter(base_url="http://127.0.0.1:8080")

    with patch(
        "app.services.model_adapter.httpx.AsyncClient"
    ) as mock_client_class:
        mock_client = MagicMock()
        mock_client.post = AsyncMock(
            side_effect=httpx.HTTPError("Connection failed")
        )
        mock_client_class.return_value.__aenter__.return_value = mock_client

        with pytest.raises(ModelServerError):
            await adapter.process_audio(
                audio_bytes=b"fake-audio",
                history=[],
            )


async def test_process_text_bad_response():
    adapter = LFM3Adapter(base_url="http://127.0.0.1:8080")

    bad_response = MagicMock()
    bad_response.raise_for_status.return_value = None
    bad_response.json.return_value = {"text": "no choices key"}

    with patch(
        "app.services.model_adapter.httpx.AsyncClient"
    ) as mock_client_class:
        mock_client = MagicMock()
        mock_client.post = AsyncMock(return_value=bad_response)
        mock_client_class.return_value.__aenter__.return_value = mock_client

        with pytest.raises(ModelServerError):
            await adapter.process_text(
                text="hello",
                history=[],
            )


async def test_process_text_tts_empty_audio():
    adapter = LFM3Adapter(base_url="http://127.0.0.1:8080")

    with patch(
        "app.services.model_adapter.httpx.AsyncClient"
    ) as mock_client_class:
        mock_client = MagicMock()
        mock_client.post = AsyncMock(
            side_effect=[
                _chat_response("Hello there."),
                _tts_response(b""),
            ]
        )
        mock_client_class.return_value.__aenter__.return_value = mock_client

        with pytest.raises(ModelServerError):
            await adapter.process_text(
                text="hello",
                history=[],
            )


async def test_process_text_tts_http_error():
    adapter = LFM3Adapter(base_url="http://127.0.0.1:8080")

    with patch(
        "app.services.model_adapter.httpx.AsyncClient"
    ) as mock_client_class:
        mock_client = MagicMock()
        mock_client.post = AsyncMock(
            side_effect=[
                _chat_response("Hello there."),
                httpx.HTTPError("TTS failed"),
            ]
        )
        mock_client_class.return_value.__aenter__.return_value = mock_client

        with pytest.raises(ModelServerError):
            await adapter.process_text(
                text="hello",
                history=[],
            )


async def test_process_text_multi_sentence_joins_wav():
    adapter = LFM3Adapter(base_url="http://127.0.0.1:8080")

    with patch(
        "app.services.model_adapter.httpx.AsyncClient"
    ) as mock_client_class:
        mock_client = MagicMock()
        mock_client.post = AsyncMock(
            side_effect=[
                _chat_response("First sentence. Second sentence."),
                _tts_response(_wav_bytes(100)),
                _tts_response(_wav_bytes(100)),
            ]
        )
        mock_client_class.return_value.__aenter__.return_value = mock_client

        result = await adapter.process_text(
            text="hello",
            history=[],
        )

    assert mock_client.post.await_count == 3
    assert result["assistant_text"] == "First sentence. Second sentence."

    with wave.open(io.BytesIO(result["audio_bytes"]), "rb") as joined:
        assert joined.getnframes() == 200
        assert joined.getframerate() == 24000
        assert joined.getnchannels() == 1


def test_clean_for_tts_removes_markdown_and_bullets():
    text = "**Key:**\n- High speed\n- Easy\n\nDone"

    assert _clean_for_tts(text) == "Key: High speed. Easy. Done."


def test_split_sentences():
    parts = _split_sentences("Hello there. How are you? Fine!")

    assert parts == ["Hello there.", "How are you?", "Fine!"]
