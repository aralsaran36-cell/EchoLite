import io
import re
import wave

import httpx

from app.core.errors import ModelServerError

SYSTEM_PROMPT = (
    "You are a friendly voice assistant. Always reply in English, "
    "whatever language the user writes in. Reply in plain conversational text, "
    "the way a person talks. Do not use markdown, asterisks, bullet points, "
    "numbered lists, headings or emojis. Keep answers short, 2 to 3 sentences."
)


def _clean_for_tts(text: str) -> str:
    text = re.sub(r"[*#`_>]", "", text)
    lines = []

    for line in text.splitlines():
        line = re.sub(r"^\s*(?:[-•]|\d+\.)\s+", "", line).strip()

        if not line:
            continue

        if line[-1] not in ".!?:":
            line += "."

        lines.append(line)

    return " ".join(lines)


def _split_sentences(text: str) -> list[str]:
    return [p.strip() for p in re.split(r"(?<=[.!?:])\s+", text) if p.strip()]


def _join_wavs(chunks: list[bytes]) -> bytes:
    if len(chunks) == 1:
        return chunks[0]

    try:
        out = io.BytesIO()
        writer = None

        for chunk in chunks:
            with wave.open(io.BytesIO(chunk), "rb") as reader:
                if writer is None:
                    writer = wave.open(out, "wb")
                    writer.setparams(reader.getparams())
                writer.writeframes(reader.readframes(reader.getnframes()))

        writer.close()
        return out.getvalue()
    except (wave.Error, EOFError) as exc:
        raise ModelServerError("Could not join speech audio.") from exc


class LFM3Adapter:
    """Adapter for communicating with the local LFM3-Omni-2B server."""

    def __init__(self, base_url: str, timeout_seconds: float = 120):
        self.base_url = base_url.rstrip("/")
        self.timeout = httpx.Timeout(timeout_seconds)

    async def _chat(
        self,
        messages: list[dict],
        max_tokens: int = 520,
        use_system_prompt: bool = True,
        temperature: float = 0.7,
    ) -> str:
        if use_system_prompt:
            messages = [{"role": "system", "content": SYSTEM_PROMPT}, *messages]

        payload = {
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "frequency_penalty": 0.5,
            "repeat_penalty": 1.15,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/v1/chat/completions",
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()

            return data["choices"][0]["message"]["content"].strip()

        except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as exc:
            raise ModelServerError(
                "Could not get a valid reply from the LFM3 model server."
            ) from exc

    async def _tts(self, text: str) -> bytes:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/tts",
                    json={"input": text},
                )
                response.raise_for_status()
                audio = response.content
        except httpx.HTTPError as exc:
            raise ModelServerError(
                "Could not get speech audio from the LFM3 model server."
            ) from exc

        if not audio:
            raise ModelServerError("The LFM3 model server returned empty audio.")

        return audio

    async def _speak(self, text: str) -> bytes:
        sentences = _split_sentences(_clean_for_tts(text)) or [text.strip()]
        chunks = [await self._tts(sentence) for sentence in sentences]
        return _join_wavs(chunks)

    async def process_text(self, text: str, history: list[dict]) -> dict:
        messages = [*history, {"role": "user", "content": text}]
        reply = await self._chat(messages)
        audio = await self._speak(reply)

        return {
            "assistant_text": reply,
            "audio_bytes": audio,
            "audio_format": "wav",
        }

    async def process_audio(
        self,
        transcript: str,
        history: list[dict],
    ) -> dict:
         reply = await self._chat([*history, {"role": "user", "content": transcript}])
         audio = await self._speak(reply)

         return {
            "user_transcript": transcript,
            "assistant_text": reply,
            "audio_bytes": audio,
            "audio_format": "wav",
        }
