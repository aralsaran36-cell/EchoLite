import io
import wave

import numpy as np
import torch
from transformers import AutoProcessor, SeamlessM4Tv2ForSpeechToText

from app.core.errors import AudioValidationError, ModelServerError

ASR_MODEL_ID = "facebook/seamless-m4t-v2-large"
TARGET_LANG = "eng"
SAMPLE_RATE = 16000


def _wav_to_float(wav_bytes: bytes) -> np.ndarray:
    try:
        with wave.open(io.BytesIO(wav_bytes), "rb") as reader:
            if reader.getframerate() != SAMPLE_RATE:
                raise AudioValidationError("Audio must be 16 kHz")
            if reader.getnchannels() != 1:
                raise AudioValidationError("Audio must be mono")
            if reader.getsampwidth() != 2:
                raise AudioValidationError("Audio must be 16-bit")
            frames = reader.readframes(reader.getnframes())
    except (wave.Error, EOFError) as exc:
        raise AudioValidationError("Audio is not a valid WAV") from exc

    samples = np.frombuffer(frames, dtype=np.int16).astype(np.float32)
    return samples / 32768.0


class SeamlessASR:
    """Speech (Tamil, English, Tanglish) to English text."""

    def __init__(
        self,
        model_id: str = ASR_MODEL_ID,
        target_lang: str = TARGET_LANG,
    ):
        self.target_lang = target_lang
        self.processor = AutoProcessor.from_pretrained(model_id)
        self.model = SeamlessM4Tv2ForSpeechToText.from_pretrained(model_id)
        self.model.eval()

    def transcribe(self, wav_bytes: bytes) -> str:
        samples = _wav_to_float(wav_bytes)

        if samples.size == 0:
            raise AudioValidationError("Audio is empty")

        try:
            inputs = self.processor(
                audios=samples,
                sampling_rate=SAMPLE_RATE,
                return_tensors="pt",
            )

            with torch.inference_mode():
                output = self.model.generate(
                    **inputs,
                    tgt_lang=self.target_lang,
                )

            if hasattr(output, "sequences"):
                output = output.sequences
            elif isinstance(output, (tuple, list)):
                output = output[0]

            text = self.processor.decode(
                output[0].tolist(),
                skip_special_tokens=True,
            )
        except AudioValidationError:
            raise
        except Exception as exc:
            raise ModelServerError("Speech recognition failed.") from exc

        return text.strip()
