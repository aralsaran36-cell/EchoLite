import pytest


class FakeASR:
    """Test double for SeamlessASR. Never loads the real model."""

    def __init__(self, *args, **kwargs):
        pass

    def transcribe(self, wav_bytes: bytes) -> str:
        return "fake transcript"
    
class FakeTranslator:
    """Test double for SeamlessTranslator. Never loads the real model."""

    def __init__(self, *args, **kwargs):
        pass

    def translate(self, text: str) -> str:
        return text

@pytest.fixture(autouse=True)
def fake_asr_model(monkeypatch):
        monkeypatch.setattr("app.services.asr.SeamlessASR", FakeASR)
        monkeypatch.setattr(
        "app.services.translate.SeamlessTranslator", FakeTranslator
    )