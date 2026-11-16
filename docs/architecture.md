# EchoLite Architecture

EchoLite follows a layered FastAPI architecture.

## Layers

| Layer | Responsibility |
|---|---|
| API | HTTP routes and request handling |
| Schemas | Request and response models |
| Services | Audio, VAD, and model integration |
| Core | Config, errors, logging, session store |
| Static | Browser UI |

## Request flow

```text
Browser
  -> FastAPI /turn
  -> Audio validation
  -> WAV conversion
  -> Session history
  -> LFM3 adapter
  -> Local LFM3 server
  -> Response
  -> Browser
```

## Files

| File | Responsibility |
|---|---|
| `app/main.py` | FastAPI app and startup |
| `app/config.py` | Settings |
| `app/dependencies.py` | Dependency injection |
| `app/api/routes_health.py` | Health endpoint |
| `app/api/routes_turn.py` | Voice turn endpoint |
| `app/core/errors.py` | Custom errors |
| `app/core/logging.py` | Logging |
| `app/core/session_store.py` | Conversation history |
| `app/schemas/turn.py` | API schemas |
| `app/services/audio.py` | Audio validation and conversion |
| `app/services/vad.py` | Voice activity detection |
| `app/services/model_adapter.py` | LFM3 integration |