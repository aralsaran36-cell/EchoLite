# LFM3-Omni-2B Feasibility

EchoLite is designed to work with a local LFM3-Omni-2B server.

## Current approach

The backend sends WAV audio to the model server through HTTP.

The model server is expected to provide:

- Speech recognition
- Text generation
- Speech response generation

## Current adapter

`app/services/model_adapter.py` currently uses a placeholder endpoint:

```text
POST /v1/audio/transcriptions
```

## Required next step

Replace the placeholder endpoint with the actual LFM3 server endpoint.

## Constraints

- The backend expects WAV audio.
- Audio is converted to 16 kHz mono WAV.
- The model server must be reachable at the configured URL.
- The adapter must return transcript and assistant response.