from app.config import Settings


def test_default_settings():
    settings = Settings()

    assert settings.app_name == "Voice Chat Backend"
    assert settings.app_version == "0.1.0"
    assert settings.model_id == "LFM3-Omni-2B"
    assert settings.llama_cpp_server_url == "http://127.0.0.1:8080"


def test_positive_limits():
    settings = Settings()

    assert settings.max_upload_mb > 0
    assert settings.request_timeout_seconds > 0
    assert settings.max_history_turns > 0


def test_allowed_origins_not_empty():
    settings = Settings()

    assert len(settings.allowed_origins) > 0


def test_settings_can_be_created():
    settings = Settings()

    assert isinstance(settings, Settings)