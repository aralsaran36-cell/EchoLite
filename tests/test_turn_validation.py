import io

from fastapi.testclient import TestClient

from app.main import create_app


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


def test_turn_requires_session_id_and_file():
    app = create_app()

    with TestClient(app) as client:
        response = client.post("/turn")

    assert response.status_code == 422


def test_turn_rejects_invalid_audio_extension():
    app = create_app()

    with TestClient(app) as client:
        response = client.post(
            "/turn",
            data={"session_id": "s1"},
            files={
                "file": (
                    "test.txt",
                    b"not audio",
                    "text/plain",
                )
            },
        )

    assert response.status_code == 400


def test_turn_rejects_oversize_audio():
    app = create_app()

    large_audio = b"x" * (11 * 1024 * 1024)

    with TestClient(app) as client:
        response = client.post(
            "/turn",
            data={"session_id": "s1"},
            files={
                "file": (
                    "test.wav",
                    large_audio,
                    "audio/wav",
                )
            },
        )

    assert response.status_code == 400