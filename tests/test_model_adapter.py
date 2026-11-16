import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import httpx

from app.core.errors import ModelServerError
from app.services.model_adapter import LFM3Adapter


async def test_process_audio_success():
    adapter = LFM3Adapter(
        base_url="http://127.0.0.1:8080",
    )

    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "text": "Hello"
    }

    with patch(
        "app.services.model_adapter.httpx.AsyncClient"
    ) as mock_client_class:
        mock_client = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_class.return_value.__aenter__.return_value = mock_client

        result = await adapter.process_audio(
            audio_bytes=b"fake-audio",
            history=[],
        )

    assert result["user_transcript"] == "Hello"
    assert result["assistant_text"] == "Hello"
    assert result["audio_format"] == "wav"


async def test_process_audio_http_error():
    adapter = LFM3Adapter(
        base_url="http://127.0.0.1:8080",
    )

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