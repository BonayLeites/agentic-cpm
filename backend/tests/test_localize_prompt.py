"""Tests para la funcion localize_prompt()."""

from app.llm.prompts import localize_prompt


def test_english_returns_unchanged():
    prompt = "You are a financial analyst."
    assert localize_prompt(prompt, "en") is prompt
    assert localize_prompt(prompt, "en", json_mode=True) is prompt


def test_spanish_json_mode():
    prompt = "Respond in JSON format."
    result = localize_prompt(prompt, "es", json_mode=True)
    assert result.startswith(prompt)
    assert "Spanish" in result
    assert "title, description" in result
    assert "Keep JSON keys" in result


def test_spanish_narrative_mode():
    prompt = "Write a summary."
    result = localize_prompt(prompt, "es")
    assert result.startswith(prompt)
    assert "Write the entire response in Spanish" in result


def test_japanese_json_mode():
    prompt = "Respond in JSON."
    result = localize_prompt(prompt, "ja", json_mode=True)
    assert "Japanese" in result
    assert "severity values (high/medium/low)" in result


def test_japanese_narrative_mode():
    prompt = "Write a summary."
    result = localize_prompt(prompt, "ja")
    assert "Write the entire response in Japanese" in result


def test_unknown_language_falls_back_to_english():
    prompt = "Some prompt."
    # Idioma desconocido cae a English (sin cambios reales, pero no rompe)
    result = localize_prompt(prompt, "fr")
    assert "English" in result
