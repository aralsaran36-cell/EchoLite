import pytest

from app.core.errors import (
    AppError,
    AudioValidationError,
    ModelServerError,
)


def test_audio_validation_error_is_app_error():
    assert issubclass(AudioValidationError, AppError)


def test_model_server_error_is_app_error():
    assert issubclass(ModelServerError, AppError)


def test_audio_validation_error_can_be_raised():
    with pytest.raises(AudioValidationError):
        raise AudioValidationError("Invalid audio")


def test_model_server_error_can_be_raised():
    with pytest.raises(ModelServerError):
        raise ModelServerError("Model unavailable")


def test_error_message_is_preserved():
    error = AudioValidationError("WAV file required")

    assert str(error) == "WAV file required"