import sys
import time
from pathlib import Path

from app.services.asr import SeamlessASR


def main():
    paths = sys.argv[1:]

    if not paths:
        print("Usage: python probe_seamless.py /tmp/en.wav /tmp/ta.wav /tmp/tg.wav")
        return

    t = time.time()
    asr = SeamlessASR()
    print(f"MODEL LOAD {time.time() - t:.1f}s")

    for path in paths:
        wav_bytes = Path(path).read_bytes()
        t = time.time()
        text = asr.transcribe(wav_bytes)
        print(f"{path} | {time.time() - t:.1f}s | {text}")


if __name__ == "__main__":
    main()
