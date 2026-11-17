# EchoLite Architecture

EchoLite follows a layered FastAPI architecture. The browser handles mic capture, silence detection (VAD) and playback. The backend handles validation, conversion, history and the local LFM3 model server.

## Layers

| Layer | Responsibility |
|---|---|
| API | HTTP routes and request handling |
| Schemas | Request and response models |
| Services | Audio, VAD, and model integration |
| Core | Config, errors, logging, session store |
| Static | Browser UI (mic, VAD, playback, chat) |

## Voice turn flow

```text
Browser (mic + VAD, silence threshold)
  -> POST /turn (session_id, audio file)
  -> Audio validation
  -> WAV conversion (FFmpeg, 16 kHz mono)
  -> Session history
  -> LFM3 adapter: ASR (user transcript)
  -> LFM3 adapter: reply text (with history)
  -> LFM3 adapter: POST /tts (reply speech, WAV)
  -> Save turn (text only)
  -> Response (text + audio_base64 + latency_ms)
  -> Browser plays audio, then listens again
```

## Text turn flow

```text
Browser (text input)
  -> POST /turn/text (session_id, text)
  -> Session history
  -> LFM3 adapter: reply text (with history)
  -> LFM3 adapter: POST /tts (reply speech, WAV)
  -> Save turn (text only)
  -> Response (text + audio_base64 + latency_ms)
  -> Browser shows text and plays audio
```

## Files

| File | Responsibility |
|---|---|
| `app/main.py` | FastAPI app and startup |
| `app/config.py` | Settings |
| `app/dependencies.py` | Dependency injection |
| `app/api/routes_health.py` | Health endpoint |
| `app/api/routes_turn.py` | Voice turn (`/turn`) and text turn (`/turn/text`) endpoints |
| `app/core/errors.py` | Custom errors |
| `app/core/logging.py` | Logging |
| `app/core/session_store.py` | Conversation history (in memory, text only) |
| `app/schemas/turn.py` | API schemas |
| `app/services/audio.py` | Audio validation and conversion |
| `app/services/vad.py` | Server-side RMS functions (not used in the flow) |
| `app/services/model_adapter.py` | LFM3 chat, ASR and TTS integration |
| `app/static/index.html` | UI layout |
| `app/static/css/style.css` | UI styles and states |
| `app/static/js/app.js` | UI states, chat, retry, errors |
| `app/static/js/recorder.js` | Mic recording |
| `app/static/js/vad.js` | Silence detection |
| `app/static/js/player.js` | Reply playback, stop, replay |
