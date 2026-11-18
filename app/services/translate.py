import torch
from transformers import AutoProcessor, SeamlessM4Tv2ForTextToText

from app.core.errors import ModelServerError

TRANSLATE_MODEL_ID = "facebook/seamless-m4t-v2-large"
TARGET_LANG = "eng"
MAX_NEW_TOKENS = 256

# (start, end, Seamless language code), Unicode script ranges
SCRIPT_RANGES = [
    (0x0B80, 0x0BFF, "tam"),
    (0x0900, 0x097F, "hin"),
    (0x0C00, 0x0C7F, "tel"),
    (0x0C80, 0x0CFF, "kan"),
    (0x0D00, 0x0D7F, "mal"),
    (0x0980, 0x09FF, "ben"),
    (0x0A80, 0x0AFF, "guj"),
    (0x0A00, 0x0A7F, "pan"),
    (0x0600, 0x06FF, "arb"),
    (0x0400, 0x04FF, "rus"),
    (0x3040, 0x30FF, "jpn"),
    (0xAC00, 0xD7AF, "kor"),
    (0x4E00, 0x9FFF, "cmn"),
]


def detect_source_lang(text: str) -> str | None:
    """Return a Seamless language code from the dominant non-Latin script.

    Returns None for Latin-script text (English, Tanglish, French...), because
    the script alone cannot tell those languages apart.
    """
    counts: dict[str, int] = {}

    for char in text:
        code = ord(char)

        for start, end, lang in SCRIPT_RANGES:
            if start <= code <= end:
                counts[lang] = counts.get(lang, 0) + 1
                break

    if not counts:
        return None

    return max(counts, key=counts.get)


class SeamlessTranslator:
    """Text (any supported script) to English text."""

    def __init__(
        self,
        model_id: str = TRANSLATE_MODEL_ID,
        target_lang: str = TARGET_LANG,
    ):
        self.target_lang = target_lang
        self.processor = AutoProcessor.from_pretrained(model_id)
        self.model = SeamlessM4Tv2ForTextToText.from_pretrained(model_id)
        self.model.eval()

    def translate(self, text: str) -> str:
        text = text.strip()
        src_lang = detect_source_lang(text)

        if not text or src_lang is None:
            return text

        try:
            inputs = self.processor(
                text=text,
                src_lang=src_lang,
                return_tensors="pt",
            )

            with torch.inference_mode():
                output = self.model.generate(
                    **inputs,
                    tgt_lang=self.target_lang,
                    max_new_tokens=MAX_NEW_TOKENS,
                )

            if hasattr(output, "sequences"):
                output = output.sequences
            elif isinstance(output, (tuple, list)):
                output = output[0]

            translated = self.processor.decode(
                output[0].tolist(),
                skip_special_tokens=True,
            )
        except Exception as exc:
            raise ModelServerError("Text translation failed.") from exc

        return translated.strip() or text
