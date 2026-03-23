"""Utilidades compartidas para prompts del LLM."""

LANGUAGE_NAMES: dict[str, str] = {"en": "English", "es": "Spanish", "ja": "Japanese"}


def localize_prompt(prompt: str, language: str, *, json_mode: bool = False) -> str:
    """Anade una instruccion de idioma al final del system prompt.

    Para ``"en"`` devuelve el prompt sin cambios (zero-cost).
    """
    if language == "en":
        return prompt

    lang_name = LANGUAGE_NAMES.get(language, "English")

    if json_mode:
        instruction = (
            f"\n\nIMPORTANT: Write ALL human-readable text (title, description, "
            f"suggested_questions, suggested_actions, evidence labels and values, "
            f"issues, escalation_flags) in {lang_name}. "
            f"Keep JSON keys, severity values (high/medium/low), category values, "
            f"evidence type values (data_point/document_excerpt/rule_reference), "
            f"entity codes, currency codes, and account codes in English."
        )
    else:
        instruction = f"\n\nIMPORTANT: Write the entire response in {lang_name}."

    return prompt + instruction
