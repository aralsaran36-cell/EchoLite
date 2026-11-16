# EchoLite Test Results

All backend core tests passed.

## Test summary

| Test file | Tests | Status |
|---|---:|---|
| `test_config.py` | 4 | Passed |
| `test_errors.py` | 5 | Passed |
| `test_logging.py` | 4 | Passed |
| `test_session_store.py` | 5 | Passed |
| `test_schemas.py` | 5 | Passed |
| `test_audio.py` | 6 | Passed |
| `test_vad.py` | 9 | Passed |
| `test_model_adapter.py` | 2 | Passed |
| `test_health.py` | 1 | Passed |
| `test_turn_validation.py` | 3 | Passed |

## Total

```text
44 passed
```

## Notes

- LFM3 adapter tests use mocked HTTP calls.
- Audio tests require FFmpeg.
- Turn validation tests do not call the real LFM3 server.