from app.services.vad import (
    calculate_rms,
    detect_speech_segments,
    is_speech,
)


def test_calculate_rms_zero_for_empty():
    assert calculate_rms([]) == 0.0


def test_calculate_rms_zero_for_silence():
    samples = [0] * 100

    assert calculate_rms(samples) == 0.0


def test_calculate_rms_positive_for_speech():
    samples = [1000] * 100

    rms = calculate_rms(samples)

    assert rms > 0


def test_is_speech_true_for_loud_audio():
    samples = [1000] * 100

    assert is_speech(samples, threshold=500.0) is True


def test_is_speech_false_for_silence():
    samples = [0] * 100

    assert is_speech(samples, threshold=500.0) is False


def test_detect_speech_segments_empty():
    assert detect_speech_segments([]) == []


def test_detect_speech_segments_all_silence():
    samples = [0] * 1600

    segments = detect_speech_segments(samples)

    assert segments == []


def test_detect_speech_segments_all_speech():
    samples = [1000] * 1600

    segments = detect_speech_segments(samples)

    assert len(segments) == 1
    assert segments[0][0] == 0
    assert segments[0][1] == 1600


def test_detect_speech_segments_mixed():
    samples = []

    samples.extend([0] * 480)
    samples.extend([1000] * 480)
    samples.extend([0] * 480)

    segments = detect_speech_segments(samples)

    assert len(segments) == 1