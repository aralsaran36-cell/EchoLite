# EchoLite

EchoLite is a local voice-chat backend built with FastAPI.

It accepts audio from the browser, validates and converts it to WAV,
maintains conversation history, sends audio to a local LFM3-Omni-2B
server, and returns the assistant response.

## Features

- Browser microphone recording
- Audio upload through `/turn`
- WAV conversion using FFmpeg
- Basic voice activity detection
- In-memory session history
- FastAPI-based REST API
- Local LFM3 model adapter
- Health check endpoint

## Requirements

- Python 3.12+
- FFmpeg installed on the system
- A local LFM3-Omni-2B server

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Environment

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

## Run

```bash
uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000/static/index.html
```

## Run tests

```bash
pytest -v
```

## API

### Health

```text
GET /health
```

### Voice turn

```text
POST /turn
```

Form fields:

- `session_id`
- `file`