from fastapi.testclient import TestClient

from app.main import create_app


def test_health_endpoint():
    app = create_app()

    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["app"] == "Voice Chat Backend"
    assert data["model_id"] == "LFM3-Omni-2B"
    assert "ffmpeg_available" in data