"""Tests for fce_enhanced.editor."""

import flet as ft
import flet_code_editor as fce

from fce_enhanced.editor import (
    DEFAULT_CODE,
    EditorHandle,
    EnhancedCodeEditor,
    _language_display_name,
    _line_to_offset,
    _offset_to_line_col,
    _title_parts,
)

# --- Pure helpers ---


def test_offset_to_line_col_start():
    assert _offset_to_line_col("hello\nworld", 0) == (1, 1)


def test_offset_to_line_col_second_line():
    text = "hello\nworld"
    # offset 6 is the "w" on line 2
    assert _offset_to_line_col(text, 6) == (2, 1)


def test_offset_to_line_col_mid_line():
    assert _offset_to_line_col("abcdef", 3) == (1, 4)


def test_offset_to_line_col_clamps_negative():
    assert _offset_to_line_col("abc", -5) == (1, 1)


def test_line_to_offset_first_line():
    assert _line_to_offset("a\nb\nc", 1) == 0


def test_line_to_offset_third_line():
    # "a\nb\nc" -> line 3 starts after "a\nb\n" = 4 chars
    assert _line_to_offset("a\nb\nc", 3) == 4


def test_line_col_offset_roundtrip():
    text = "first line\nsecond line\nthird"
    offset = _line_to_offset(text, 2)
    assert _offset_to_line_col(text, offset) == (2, 1)


def test_language_display_name():
    assert _language_display_name(fce.CodeLanguage.PYTHON) == "Python"


def test_title_parts_untitled():
    assert _title_parts(None) == ("untitled", "untitled")


def test_title_parts_named(tmp_path):
    f = tmp_path / "thing.py"
    display, name = _title_parts(str(f))
    assert name == "thing.py"
    assert display.endswith("thing.py")


# --- EditorHandle ---


def test_handle_defaults_safe():
    h = EditorHandle()
    assert h.value == ""
    assert h.dirty is False
    assert h.current_path is None


def test_handle_reads_getters():
    h = EditorHandle()
    h._get_value = lambda: "abc"
    h._get_dirty = lambda: True
    h._get_path = lambda: "/tmp/x.py"
    assert h.value == "abc"
    assert h.dirty is True
    assert h.current_path == "/tmp/x.py"


# --- Component render ---


def test_renders_full_layout(render_component):
    tree, _ = render_component(EnhancedCodeEditor)
    assert isinstance(tree, ft.Column)
    types = [type(c).__name__ for c in tree.controls]
    # toolbar, divider, title row, editor, status row
    assert types == ["Row", "Divider", "Row", "CodeEditor", "Row"]


def test_editor_uses_default_code(render_component):
    tree, _ = render_component(EnhancedCodeEditor)
    editor = next(c for c in tree.controls if isinstance(c, fce.CodeEditor))
    assert editor.value == DEFAULT_CODE


def test_handle_populated_on_render(render_component):
    handle = EditorHandle()
    render_component(EnhancedCodeEditor, handle=handle)
    assert callable(handle.open_path)
    assert callable(handle.save)
    assert handle.value == DEFAULT_CODE
    assert handle.dirty is False


def test_no_toolbar_when_disabled(render_component):
    tree, _ = render_component(EnhancedCodeEditor, show_toolbar=False)
    assert not any(
        isinstance(c, ft.Row) and any(isinstance(x, ft.IconButton) for x in c.controls)
        for c in tree.controls
    )


def test_no_status_bar_when_disabled(render_component):
    tree, _ = render_component(EnhancedCodeEditor, show_status_bar=False)
    types = [type(c).__name__ for c in tree.controls]
    # toolbar, divider, title row, editor (no trailing status row)
    assert types == ["Row", "Divider", "Row", "CodeEditor"]


def test_expand_propagates_to_root(render_component):
    tree, _ = render_component(EnhancedCodeEditor, expand=True)
    assert tree.expand is True


def test_hooks_stable_across_rerender(render_component):
    """Re-rendering the same component must not change hook count/order."""
    tree, comp = render_component(EnhancedCodeEditor)
    first = len(comp._state.hooks)
    comp._state.hook_cursor = 0
    from flet.components.component import Renderer

    Renderer(comp).render(comp.fn, *comp.args, **comp.kwargs)
    assert len(comp._state.hooks) == first


def test_initial_language_reflected_in_editor(render_component):
    tree, _ = render_component(EnhancedCodeEditor, language=fce.CodeLanguage.JAVASCRIPT)
    editor = next(c for c in tree.controls if isinstance(c, fce.CodeEditor))
    assert editor.language == fce.CodeLanguage.JAVASCRIPT
