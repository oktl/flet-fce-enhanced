"""Tests for fce_enhanced.languages."""

import flet_code_editor as fce

from fce_enhanced.languages import EXTENSION_TO_LANGUAGE, language_for_path


def test_language_for_path_python():
    assert language_for_path("/tmp/script.py") == fce.CodeLanguage.PYTHON


def test_language_for_path_javascript():
    assert language_for_path("/tmp/app.js") == fce.CodeLanguage.JAVASCRIPT


def test_language_for_path_unknown():
    assert language_for_path("/tmp/data.xyz") == fce.CodeLanguage.PLAINTEXT


def test_language_for_path_none():
    assert language_for_path(None) == fce.CodeLanguage.PLAINTEXT


def test_language_for_path_case_insensitive():
    assert language_for_path("/tmp/Script.PY") == fce.CodeLanguage.PYTHON


def test_extension_map_values_are_valid():
    for ext, lang in EXTENSION_TO_LANGUAGE.items():
        assert isinstance(lang, fce.CodeLanguage), (
            f"Extension {ext!r} maps to {lang!r} which is not a CodeLanguage member"
        )
