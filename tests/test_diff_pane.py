"""Tests for fce_enhanced.diff_pane."""

import flet as ft
import flet_code_editor as fce

from fce_enhanced.diff_pane import DiffPane, compute_unified_diff

# --- compute_unified_diff (pure function) ---


def test_no_changes():
    diff_text, added, removed = compute_unified_diff("hello\n", "hello\n")
    assert diff_text == ""
    assert added == 0
    assert removed == 0


def test_additions():
    diff_text, added, removed = compute_unified_diff("line1\n", "line1\nnew line\n")
    assert added > 0
    assert removed == 0
    assert "+new line" in diff_text


def test_deletions():
    diff_text, added, removed = compute_unified_diff("line1\nline2\n", "line1\n")
    assert removed > 0
    assert added == 0
    assert "-line2" in diff_text


def test_modifications():
    diff_text, added, removed = compute_unified_diff("old line\n", "new line\n")
    assert added > 0
    assert removed > 0
    assert "-old line" in diff_text
    assert "+new line" in diff_text


def test_empty_to_content():
    _diff_text, added, removed = compute_unified_diff("", "hello\n")
    assert added > 0
    assert removed == 0


def test_content_to_empty():
    _diff_text, added, removed = compute_unified_diff("hello\n", "")
    assert removed > 0
    assert added == 0


# --- DiffPane (component render) ---


def _diff_editor(tree: ft.Column) -> fce.CodeEditor:
    container = tree.controls[-1]
    return container.content


def test_renders_header_divider_container(render_component):
    tree, _ = render_component(
        DiffPane, original_text="hello\n", current_text="hello\n"
    )
    assert isinstance(tree, ft.Column)
    assert [type(c).__name__ for c in tree.controls] == ["Row", "Divider", "Container"]


def test_no_changes_stats(render_component):
    tree, _ = render_component(
        DiffPane, original_text="hello\n", current_text="hello\n"
    )
    stats = tree.controls[0].controls[2]
    assert stats.value == "No changes"


def test_change_stats(render_component):
    tree, _ = render_component(
        DiffPane, original_text="a\nb\nc\n", current_text="a\nx\ny\nz\n"
    )
    stats = tree.controls[0].controls[2].value
    assert stats.startswith("+")
    assert "/ -" in stats


def test_diff_editor_is_readonly_diff_language(render_component):
    tree, _ = render_component(DiffPane, original_text="a\n", current_text="b\n")
    editor = _diff_editor(tree)
    assert editor.read_only is True
    assert editor.language == fce.CodeLanguage.DIFF
    assert "-a" in editor.value
    assert "+b" in editor.value
