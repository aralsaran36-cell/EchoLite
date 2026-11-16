import pytest
from pydantic import ValidationError

from app.schemas.turn import TurnResponse


def test_valid_turn_response():
    response = TurnResponse(
        session_id="s1",
        user_transcript="Hello",
        assistant_text="Hi",
        audio_format="wav",
    )

    assert response.session_id == "s1"
    assert response.user_transcript == "Hello"
    assert response.assistant_text == "Hi"
    assert response.audio_format == "wav"


def test_missing_session_id():
    with pytest.raises(ValidationError):
        TurnResponse(
            user_transcript="Hello",
            assistant_text="Hi",
            audio_format="wav",
        )


def test_empty_session_id():
    with pytest.raises(ValidationError):
        TurnResponse(
            session_id="",
            user_transcript="Hello",
            assistant_text="Hi",
            audio_format="wav",
        )


def test_missing_optional_fields_use_defaults():
    response = TurnResponse(
        session_id="s1",
    )

    assert response.user_transcript == ""
    assert response.assistant_text == ""
    assert response.audio_format == "wav"


def test_response_serializes_to_dict():
    response = TurnResponse(
        session_id="s1",
        user_transcript="Hello",
        assistant_text="Hi",
        audio_format="wav",
    )

    data = response.model_dump()

    assert data["session_id"] == "s1"
    assert data["user_transcript"] == "Hello"
    assert data["assistant_text"] == "Hi"
    assert data["audio_format"] == "wav"