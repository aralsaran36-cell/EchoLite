import base64
import io
import os
import time
import uuid
import wave
from pathlib import Path

import requests
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from config import settings

app = FastAPI(title="EchoLite")

STATIC_DIR = Path(__file__).parent / "static"
AUDIO_DIR = Path(__file__).parent / "generated_audio"
AUDIO_DIR.mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

sessions = {}


@app.get("/")
def home():
    return FileResponse(STATIC_DIR / "index.html")


def build_messages(session_id: str, user_content, output_mode: str):
    history = sessions.setdefault(session_id, [])

    system_prompt = (
        "You are EchoLite, a helpful voice assistant. "
        "Keep answers short, clear, and conversational."
    )

    if output_mode == "voice":
        system_prompt += " Respond with interleaved text and audio."
    else:
        system_prompt += " Respond with text."

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_content})

    return messages


def call_llama(messages: list):
    response = requests.post(
        f"{settings.llama_server_url}/v1/chat/completions",
        json={
            "model": settings.model_name,
            "messages": messages,
            "temperature": settings.temperature,
            "max_tokens": settings.max_tokens,
            "stream": False
        },
        timeout=settings.request_timeout_seconds
    )

    response.raise_for_status()
    return response.json()


def extract_response(payload: dict):
    choice = payload["choices"][0]
    message = choice["message"]
    return message.get("content", ""), message.get("audio")


def save_audio(audio_data, turn_id: str):
    if not audio_data:
        return None

    if isinstance(audio_data, dict):
        audio_b64 = audio_data.get("data")
        audio_format = audio_data.get("format", "wav")
    else:
        audio_b64 = audio_data
        audio_format = "wav"

    if not audio_b64:
        return None

    audio_bytes = base64.b64decode(audio_b64)
    extension = "wav" if audio_format == "wav" else audio_format
    filename = f"{turn_id}.{extension}"
    path = AUDIO_DIR / filename
    path.write_bytes(audio_bytes)

    return f"/audio/{filename}"


def update_history(session_id: str, user_content, assistant_text: str):
    history = sessions.setdefault(session_id, [])
    history.append({"role": "user", "content": user_content})
    history.append({"role": "assistant", "content": assistant_text})

    max_turns = settings.max_history_turns * 2

    if len(history) > max_turns:
        sessions[session_id] = history[-max_turns:]


@app.post("/turn")
async def turn(
    session_id: str = Form(...),
    text: str = Form(""),
    audio: UploadFile | None = File(None)
):
    turn_id = str(uuid.uuid4())

    try:
        if audio and audio.filename:
            audio_bytes = await audio.read()

            if len(audio_bytes) > settings.max_upload_bytes:
                return JSONResponse(
                    status_code=413,
                    content={"detail": "Audio file is too large."}
                )

            audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")

            user_content = [{
                "type": "input_audio",
                "input_audio": {
                    "data": audio_b64,
                    "format": "wav"
                }
            }]

            messages = build_messages(session_id, user_content, "voice")
        elif text.strip():
            user_content = text.strip()
            messages = build_messages(session_id, user_content, "text")
        else:
            return JSONResponse(
                status_code=400,
                content={"detail": "Provide text or audio."}
            )

        payload = call_llama(messages)
        assistant_text, audio_data = extract_response(payload)
        audio_url = save_audio(audio_data, turn_id)

        update_history(session_id, user_content, assistant_text)

        return {
            "session_id": session_id,
            "turn_id": turn_id,
            "assistant_text": assistant_text,
            "audio_available": bool(audio_url),
            "audio_url": audio_url
        }

    except requests.RequestException as error:
        return JSONResponse(
            status_code=502,
            content={"detail": f"LLM server error: {error}"}
        )
    except Exception as error:
        return JSONResponse(
            status_code=500,
            content={"detail": f"Internal error: {error}"}
        )


@app.get("/audio/{filename}")
def get_audio(filename: str):
    path = AUDIO_DIR / filename

    if not path.exists():
        return JSONResponse(status_code=404, content={"detail": "Audio not found"})

    return FileResponse(path)