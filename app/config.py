from dataclasses import dataclass, field


@dataclass
class Settings:
    app_name: str = "Voice Chat Backend"
    app_version: str = "0.1.0"
    log_level: str = "INFO"

    allowed_origins: list[str] = field(
        default_factory=lambda: [
            "http://127.0.0.1:8000",
            "http://localhost:8000",
        ]
    )

    llama_server_url: str = "http://127.0.0.1:8080"
    llama_cpp_server_url: str = "http://127.0.0.1:8080"

    model_name: str = "lfm3-omni-2b"
    model_id: str = "LFM3-Omni-2B"

    temperature: float = 0.7
    max_tokens: int = 512

    request_timeout_seconds: int = 120

    max_upload_mb: int = 10
    max_upload_bytes: int = 10 * 1024 * 1024

    max_audio_seconds: int = 20
    silence_timeout_seconds: float = 1.5

    max_history_turns: int = 10


settings = Settings()


def get_settings() -> Settings:
    return settings