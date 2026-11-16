import numpy as np


def calculate_rms(samples: list[int]) -> float:
    if not samples:
        return 0.0

    arr = np.array(samples, dtype=np.float32)

    return float(np.sqrt(np.mean(np.square(arr))))


def is_speech(
    samples: list[int],
    threshold: float = 500.0,
) -> bool:
    rms = calculate_rms(samples)

    return rms >= threshold


def detect_speech_segments(
    samples: list[int],
    sample_rate: int = 16000,
    frame_duration_ms: int = 30,
    threshold: float = 500.0,
) -> list[tuple[int, int]]:
    if not samples:
        return []

    frame_size = int(sample_rate * frame_duration_ms / 1000)

    segments = []
    start = None

    for i in range(0, len(samples), frame_size):
        frame = samples[i : i + frame_size]

        if is_speech(frame, threshold):
            if start is None:
                start = i
        else:
            if start is not None:
                segments.append((start, i))
                start = None

    if start is not None:
        segments.append((start, len(samples)))

    return segments