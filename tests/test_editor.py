"""Tests for flet_code_editor_enhanced.editor (EnhancedCodeEditor control)."""

from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import flet as ft
import flet_code_editor as fce
import pytest

from flet_code_editor_enhanced.editor import DEFAULT_CODE, EnhancedCodeEditor
from flet_code_editor_enhanced.search import SearchReplaceBar


# --- Helpers ---


def _make_editor(**kwargs) -> EnhancedCodeEditor:
    """Create an EnhancedCodeEditor without mounting it."""
    return EnhancedCodeEditor(**kwargs)


def _patch_page(editor: EnhancedCodeEditor):
    """Patch the page property, update, and focus for testing without a real page."""
    mock_page = MagicMock(spec=ft.Page)
    mock_page.overlay = []

    page_patch = patch.object(
        type(editor), "page", new_callable=PropertyMock, return_value=mock_page
    )
    update_patch = patch.object(editor, "update")
    focus_patch = patch.object(editor._code_editor, "focus", new_callable=AsyncMock)

    page_patch.start()
    update_patch.start()
    focus_patch.start()

    return mock_page, page_patch, update_patch, focus_patch


def _cleanup_patches(*patches):
    for p in patches:
        p.stop()


# --- Constructor defaults ---


def test_default_value():
    editor = _make_editor()
    assert editor.value == DEFAULT_CODE


def test_default_language():
    editor = _make_editor()
    assert editor.language == fce.CodeLanguage.PYTHON


def test_default_not_dirty():
    editor = _make_editor()
    assert editor.dirty is False


def test_default_no_path():
    editor = _make_editor()
    assert editor.current_path is None


def test_custom_value():
    editor = _make_editor(value="hello world")
    assert editor.value == "hello world"


def test_custom_language():
    editor = _make_editor(language=fce.CodeLanguage.JAVASCRIPT)
    assert editor.language == fce.CodeLanguage.JAVASCRIPT


# --- Property setters ---


def test_set_value():
    editor = _make_editor()
    editor.value = "new content"
    assert editor.value == "new content"


def test_set_language():
    editor = _make_editor()
    editor.language = fce.CodeLanguage.RUST
    assert editor.language == fce.CodeLanguage.RUST


# --- code_editor property ---


def test_code_editor_property():
    editor = _make_editor()
    assert isinstance(editor.code_editor, fce.CodeEditor)


# --- Layout options ---


def test_toolbar_shown_by_default():
    editor = _make_editor()
    # Toolbar is the second control (after title bar row)
    toolbar_row = editor.controls[1]
    button_labels = [c.content for c in toolbar_row.controls if hasattr(c, "content")]
    assert "Open" in button_labels
    assert "Save" in button_labels
    assert "Save As" in button_labels
    assert "Close" in button_labels
    assert "Find" in button_labels


def test_toolbar_hidden():
    editor = _make_editor(show_toolbar=False)
    all_labels = []
    for c in editor.controls:
        if isinstance(c, ft.Row):
            for child in c.controls:
                if hasattr(child, "content") and isinstance(child, ft.Button):
                    all_labels.append(child.content)
    assert "Open" not in all_labels


def test_status_bar_hidden():
    editor = _make_editor(show_status_bar=False)
    has_status = False
    for c in editor.controls:
        if isinstance(c, ft.Row):
            for child in c.controls:
                if isinstance(child, ft.Text) and "Ln" in (child.value or ""):
                    has_status = True
    assert not has_status


# --- Dirty state ---


def test_mark_dirty():
    editor = _make_editor()
    mock_page, p1, p2, p3 = _patch_page(editor)
    try:
        editor._mark_dirty()
        assert editor.dirty is True
        assert editor._save_btn.disabled is False
    finally:
        _cleanup_patches(p1, p2, p3)


def test_mark_clean():
    editor = _make_editor()
    mock_page, p1, p2, p3 = _patch_page(editor)
    try:
        editor._mark_dirty()
        editor._mark_clean("content")
        assert editor.dirty is False
        assert editor._save_btn.disabled is True
        assert editor._last_saved_content == "content"
    finally:
        _cleanup_patches(p1, p2, p3)


def test_mark_dirty_only_fires_once():
    editor = _make_editor()
    mock_page, p1, p2, p3 = _patch_page(editor)
    try:
        editor._mark_dirty()
        editor._mark_dirty()
        assert editor.dirty is True
    finally:
        _cleanup_patches(p1, p2, p3)


# --- on_title_change callback ---


def test_title_change_callback_called():
    calls = []

    def on_change(display, name, is_dirty):
        calls.append((display, name, is_dirty))

    editor = _make_editor(on_title_change=on_change)
    _, p1, p2, p3 = _patch_page(editor)
    try:
        editor._mark_dirty()
        assert len(calls) == 1
        assert calls[0] == ("untitled", "untitled", True)
    finally:
        _cleanup_patches(p1, p2, p3)


def test_title_change_with_path():
    calls = []

    def on_change(display, name, is_dirty):
        calls.append((display, name, is_dirty))

    editor = _make_editor(on_title_change=on_change)
    _, p1, p2, p3 = _patch_page(editor)
    try:
        editor._current_path = "/tmp/test.py"
        editor._mark_clean("content")
        assert len(calls) == 1
        assert calls[0][1] == "test.py"
        assert calls[0][2] is False
    finally:
        _cleanup_patches(p1, p2, p3)


# --- Keyboard shortcut registration ---


def test_keyboard_shortcuts_registered_on_mount():
    editor = _make_editor(register_keyboard_shortcuts=True)
    _, p1, p2, p3 = _patch_page(editor)
    try:
        editor.did_mount()
        mock_page = editor.page
        assert mock_page.on_keyboard_event == editor._handle_keyboard
    finally:
        _cleanup_patches(p1, p2, p3)


def test_keyboard_shortcuts_not_registered_when_disabled():
    editor = _make_editor(register_keyboard_shortcuts=False)
    _, p1, p2, p3 = _patch_page(editor)
    try:
        editor.did_mount()
        mock_page = editor.page
        assert mock_page.on_keyboard_event != editor._handle_keyboard
    finally:
        _cleanup_patches(p1, p2, p3)


def test_keyboard_shortcuts_cleaned_up_on_unmount():
    editor = _make_editor(register_keyboard_shortcuts=True)
    _, p1, p2, p3 = _patch_page(editor)
    try:
        editor.did_mount()
        editor.will_unmount()
        mock_page = editor.page
        assert mock_page.on_keyboard_event is None
    finally:
        _cleanup_patches(p1, p2, p3)


# --- _offset_to_line_col ---


def test_offset_to_line_col_start():
    line, col = EnhancedCodeEditor._offset_to_line_col("hello\nworld", 0)
    assert line == 1
    assert col == 1


def test_offset_to_line_col_second_line():
    line, col = EnhancedCodeEditor._offset_to_line_col("hello\nworld", 8)
    assert line == 2
    assert col == 3


def test_offset_to_line_col_end_of_first_line():
    line, col = EnhancedCodeEditor._offset_to_line_col("hello\nworld", 5)
    assert line == 1
    assert col == 6


# --- Save to file ---


@pytest.mark.asyncio
async def test_do_save_writes_file(tmp_path):
    editor = _make_editor()
    _, p1, p2, p3 = _patch_page(editor)
    try:
        filepath = str(tmp_path / "output.py")
        editor._current_path = filepath
        editor._code_editor.value = "print('saved')"
        editor._mark_dirty()

        result = await editor._do_save()

        assert result is True
        assert editor.dirty is False
        assert (tmp_path / "output.py").read_text() == "print('saved')"
    finally:
        _cleanup_patches(p1, p2, p3)


@pytest.mark.asyncio
async def test_do_save_no_path_triggers_save_as():
    editor = _make_editor()
    _, p1, p2, p3 = _patch_page(editor)
    try:
        editor._current_path = None

        with patch.object(
            editor, "_do_save_as", new_callable=AsyncMock, return_value=False
        ) as mock_save_as:
            result = await editor._do_save()
            mock_save_as.assert_awaited_once()
            assert result is False
    finally:
        _cleanup_patches(p1, p2, p3)


# --- Save As ---


@pytest.mark.asyncio
async def test_do_save_as_writes_to_chosen_path(tmp_path):
    editor = _make_editor()
    _, p1, p2, p3 = _patch_page(editor)
    try:
        editor._code_editor.value = "new content"
        filepath = str(tmp_path / "saved.py")

        with patch(
            "flet_code_editor_enhanced.editor.save_file",
            new_callable=AsyncMock,
            return_value=filepath,
        ):
            result = await editor._do_save_as()

        assert result is True
        assert editor.current_path == filepath
        assert editor.dirty is False
        assert (tmp_path / "saved.py").read_text() == "new content"
    finally:
        _cleanup_patches(p1, p2, p3)


@pytest.mark.asyncio
async def test_do_save_as_cancelled():
    editor = _make_editor()
    _, p1, p2, p3 = _patch_page(editor)
    try:
        with patch(
            "flet_code_editor_enhanced.editor.save_file",
            new_callable=AsyncMock,
            return_value=None,
        ):
            result = await editor._do_save_as()

        assert result is False
    finally:
        _cleanup_patches(p1, p2, p3)


# --- Open file ---


@pytest.mark.asyncio
async def test_handle_open_loads_file(tmp_py_file):
    editor = _make_editor()
    _, p1, p2, p3 = _patch_page(editor)
    try:
        with patch(
            "flet_code_editor_enhanced.editor.open_file",
            new_callable=AsyncMock,
            return_value=str(tmp_py_file),
        ):
            await editor._handle_open(None)

        assert editor.current_path == str(tmp_py_file)
        assert editor.value == "print('hello')\n"
        assert editor.language == fce.CodeLanguage.PYTHON
        assert editor.dirty is False
    finally:
        _cleanup_patches(p1, p2, p3)


@pytest.mark.asyncio
async def test_handle_open_cancelled():
    editor = _make_editor()
    _, p1, p2, p3 = _patch_page(editor)
    try:
        editor._code_editor.value = "original"

        with patch(
            "flet_code_editor_enhanced.editor.open_file",
            new_callable=AsyncMock,
            return_value=None,
        ):
            await editor._handle_open(None)

        assert editor.value == "original"
    finally:
        _cleanup_patches(p1, p2, p3)


# --- Close ---


@pytest.mark.asyncio
async def test_handle_close_resets_state():
    editor = _make_editor()
    _, p1, p2, p3 = _patch_page(editor)
    try:
        editor._current_path = "/tmp/test.py"
        editor._code_editor.value = "some content"

        await editor._handle_close(None)

        assert editor.current_path is None
        assert editor.dirty is False
        assert editor.value == DEFAULT_CODE
        assert editor.language == fce.CodeLanguage.PYTHON
    finally:
        _cleanup_patches(p1, p2, p3)


# --- Search bar integration ---


def test_search_bar_exists():
    editor = _make_editor()
    assert isinstance(editor.search_bar, SearchReplaceBar)


def test_search_bar_in_layout():
    editor = _make_editor()
    assert editor._search_bar in editor.controls


def test_search_bar_initially_hidden():
    editor = _make_editor()
    assert editor._search_bar.is_open is False
    assert editor._search_bar.controls == []


def test_search_bar_available_without_toolbar():
    editor = _make_editor(show_toolbar=False)
    assert isinstance(editor.search_bar, SearchReplaceBar)
    assert editor._search_bar in editor.controls


@pytest.mark.asyncio
async def test_ctrl_f_opens_search():
    editor = _make_editor()
    _, p1, p2, p3 = _patch_page(editor)
    focus_patch = patch.object(
        editor._search_bar._search_field, "focus", new_callable=AsyncMock
    )
    focus_patch.start()
    try:
        event = MagicMock(spec=ft.KeyboardEvent)
        event.key = "F"
        event.meta = True
        event.ctrl = False
        event.shift = False

        await editor._handle_keyboard(event)

        assert editor._search_bar.is_open is True
        assert editor._search_bar._replace_row.visible is False
    finally:
        focus_patch.stop()
        _cleanup_patches(p1, p2, p3)


@pytest.mark.asyncio
async def test_ctrl_h_opens_search_with_replace():
    editor = _make_editor()
    _, p1, p2, p3 = _patch_page(editor)
    focus_patch = patch.object(
        editor._search_bar._search_field, "focus", new_callable=AsyncMock
    )
    focus_patch.start()
    try:
        event = MagicMock(spec=ft.KeyboardEvent)
        event.key = "H"
        event.meta = True
        event.ctrl = False
        event.shift = False

        await editor._handle_keyboard(event)

        assert editor._search_bar.is_open is True
        assert editor._search_bar._replace_row.visible is True
    finally:
        focus_patch.stop()
        _cleanup_patches(p1, p2, p3)


@pytest.mark.asyncio
async def test_escape_closes_search():
    editor = _make_editor()
    _, p1, p2, p3 = _patch_page(editor)
    try:
        editor._search_bar.open()

        event = MagicMock(spec=ft.KeyboardEvent)
        event.key = "Escape"
        event.meta = False
        event.ctrl = False
        event.shift = False

        await editor._handle_keyboard(event)

        assert editor._search_bar.is_open is False
    finally:
        _cleanup_patches(p1, p2, p3)


def test_handle_change_recomputes_search():
    editor = _make_editor(value="hello world hello")
    _, p1, p2, p3 = _patch_page(editor)
    try:
        editor._search_bar.open()
        editor._search_bar._search_query = "hello"
        editor._search_bar.recompute()
        assert len(editor._search_bar._match_positions) == 2

        # Simulate text change via _handle_change
        editor._code_editor.value = "hello world"
        editor._handle_change(None)
        assert len(editor._search_bar._match_positions) == 1
    finally:
        _cleanup_patches(p1, p2, p3)
