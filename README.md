# EchoLite

Browser voice assistant that runs on your own machine. You speak, it detects the end of your speech, and replies with text and voice. The model is LiquidAI LFM3-Omni-2B, served locally by llama.cpp. No third-party cloud.

Rule: raw audio is never stored. Only the text of each turn is kept in memory for the session.

## Features

* Voice tab and Text tab. Both give a text reply plus a voice reply.
* One mic area that changes by state: Idle, Listening, Thinking, Speaking (with Stop).
* Silence detection (client-side energy based). Threshold dropdown: 0.8 / 1.2 / 1.5 / 2.0 s.
* After the reply finishes playing, it listens again automatically.
* Chat bubbles ("You:" / "AI:"), replay icon and latency label on every AI message.
* Red error banner with Retry for three cases: microphone denied, network lost, model server error.
* Server flow: validate audio, convert to 16 kHz mono WAV with FFmpeg, add history, ask the model, text to speech, return text and audio.
* Reply text is cleaned (markdown and bullets removed) and split into sentences before text to speech, then the WAV parts are joined.
* Latency (total time) is returned with each reply.

## Requirements

* Python 3.11+ (developed on 3.12)
* FFmpeg on PATH
* llama.cpp with `llama-server` on PATH
* Model: `LiquidAI/LFM3-Omni-2B-GGUF:Q4_K_M` (downloaded by llama-server on first run)

## Setup

```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Settings are in `app/config.py` (model server URL, upload limit, max audio seconds, history turns).

## Run

Start the model server (terminal 1):

```
llama-server -hf LiquidAI/LFM3-Omni-2B-GGUF:Q4_K_M --reasoning off --port 8080 -c 8192
```

Start the app (terminal 2):

```
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Check:

```
curl http://127.0.0.1:8000/health
```

`model_loaded` and `ffmpeg_available` should both be `true`. Open http://127.0.0.1:8000

## Endpoints

* `GET /` : UI
* `GET /health` : app, model server and FFmpeg status
* `POST /turn` : voice turn (multipart: `session_id`, `file`)
* `POST /turn/text` : text turn (JSON: `session_id`, `text`)

Both turn endpoints return `assistant_text`, `audio_base64` (WAV), `audio_format` and `latency_ms`.

## Test

```
pytest -q
```

## Structure

* `app/api/` : routes (health, turn)
* `app/core/` : errors, logging, session store
* `app/schemas/` : request and response models
* `app/services/` : audio (validate, FFmpeg), model adapter (chat, ASR, TTS), vad
* `app/static/` : index.html, css/style.css, js (app, recorder, vad, player)
* `app/main.py` : app entry point
* `docs/` : architecture, model feasibility, test results
* `tests/`

## Privacy

* Raw audio is not saved. Temporary files used for FFmpeg conversion are deleted right after.
* Conversation history is in memory only (text), trimmed to the last `max_history_turns` turns, and lost when the server stops.
* The microphone is not opened until you tap the mic.

## Known limits

* English only for now. Tamil and Tanglish are untested on this model.
* The small model can give wrong facts and sometimes ignores the "short plain reply" instruction.
* CPU only (Intel Mac): replies can take many seconds. Text to speech is the slowest step.
* Audio input in llama.cpp is marked experimental.
* Silence detection is energy based, so background noise can affect it. Silero VAD is not implemented.
* Phone microphone needs HTTPS (except localhost). Not set up yet.
* Only total latency is measured. Per-stage latency is planned.
* In-memory sessions: no database, no session expiry.

## Attribution

Model: LiquidAI LFM3-Omni-2B. Runtime: llama.cpp.
