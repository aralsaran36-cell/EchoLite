from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.core.errors import ModelServerError
from app.services.translate import SeamlessTranslator, detect_source_lang


def _fake_translator(decoded: str = " What is the state animal? ") -> SeamlessTranslator:
    translator = SeamlessTranslator.__new__(SeamlessTranslator)
    translator.target_lang = "eng"

    fake_tokens = MagicMock()
    fake_tokens.tolist.return_value = [1, 2, 3]

    translator.processor = MagicMock()
    translator.processor.return_value = {"input_ids": 1}
    translator.processor.decode.return_value = decoded

    translator.model = MagicMock()
    translator.model.generate.return_value = SimpleNamespace(
        sequences=[fake_tokens]
    )

    return translator


def test_detect_tamil_script():
    assert detect_source_lang("தமிழ்நாட்டின் தேசிய விலங்கு எது?") == "tam"


def test_detect_hindi_script():
    assert detect_source_lang("पाइथन क्या है") == "hin"


def test_detect_english_is_none():
    assert detect_source_lang("what is python") is None


def test_detect_tanglish_is_none():
    assert detect_source_lang("python na enna") is None


def test_detect_mixed_tamil_dominant():
    assert detect_source_lang("python என்றால் என்ன") == "tam"


def test_translate_tamil_success():
    translator = _fake_translator(" What is the state animal? ")

    text = translator.translate("தமிழ்நாட்டின் தேசிய விலங்கு எது?")

    assert text == "What is the state animal?"
    translator.model.generate.assert_called_once()
    assert translator.model.generate.call_args.kwargs["tgt_lang"] == "eng"
    assert translator.processor.call_args.kwargs["src_lang"] == "tam"


def test_translate_english_skips_model():
    translator = _fake_translator()

    text = translator.translate("  what is python  ")

    assert text == "what is python"
    translator.model.generate.assert_not_called()


def test_translate_empty_text():
    translator = _fake_translator()

    assert translator.translate("   ") == ""
    translator.model.generate.assert_not_called()


def test_translate_empty_output_returns_original():
    translator = _fake_translator("   ")

    assert translator.translate("பைதான் என்றால் என்ன?") == "பைதான் என்றால் என்ன?"


def test_translate_model_failure():
    translator = _fake_translator()
    translator.model.generate.side_effect = RuntimeError("boom")

    with pytest.raises(ModelServerError):
        translator.translate("பைதான் என்றால் என்ன?")
