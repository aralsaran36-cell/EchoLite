from dataclasses import dataclass


@dataclass
class Settings:
    llama_server_url: str = "http://127.0.0.1:8080"
    model_name: str = "lfm3-omni-2b"

    temperature: float = 0.7
    max_tokens: int = 512

    request_timeout_seconds: int = 120

    max_upload_mb: int = 10
    max_upload_bytes: int = 10 * 1024 * 1024

    max_audio_seconds: int = 20
    silence_timeout_seconds: float = 1.5

    max_history_turns: int = 10


settings = Settings()