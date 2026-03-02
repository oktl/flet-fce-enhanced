"""Tests for fce_enhanced.themes module."""

import flet_code_editor as fce

from fce_enhanced.themes import DEFAULT_THEME, THEMES, theme_display_name


def test_themes_dict_is_non_empty():
    assert len(THEMES) > 0


def test_themes_values_are_codetheme_instances():
    for name, val in THEMES.items():
        assert isinstance(val, fce.CodeTheme), f"{name} is not a CodeTheme"


def test_themes_sorted_alphabetically():
    keys = list(THEMES.keys())
    assert keys == sorted(keys)


def test_dragula_excluded():
    assert "Dragula" not in THEMES


def test_dracula_included():
    assert "Dracula" in THEMES


def test_default_theme_is_valid():
    assert isinstance(DEFAULT_THEME, fce.CodeTheme)
    assert DEFAULT_THEME in THEMES.values()


def test_theme_display_name_known():
    assert theme_display_name(fce.CodeTheme.ATOM_ONE_DARK) == "Atom One Dark"


def test_theme_display_name_all_themes():
    for display_name, theme_val in THEMES.items():
        assert theme_display_name(theme_val) == display_name
