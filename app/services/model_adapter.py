import httpx

from app.core.errors import ModelServerError


class LFM3Adapter:
    """Adapter for communicating with the local LFM3-Omni-2B server."""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    async def process_audio(
        self,
        audio_bytes: bytes,
        history: list[dict],
    ) -> dict:
        """Send audio to LFM3 and return text and audio response."""

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/v1/audio/transcriptions",
                    files={
                        "file": (
                            "input.wav",
                            audio_bytes,
                            "audio/wav",
                        )
                    },
                )

                response.raise_for_status()
                result = response.json()

            return {
                "user_transcript": result.get("text", ""),
                "assistant_text": result.get("text", ""),
                "audio_bytes": b"",
                "audio_format": "wav",
            }

        except httpx.HTTPError as exc:
            raise ModelServerError(
                "Could not reach the LFM3 voice model server."
            ) from exc