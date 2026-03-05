"""Tests for fce_enhanced.editor (EnhancedCodeEditor control)."""

from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import flet as ft
import flet_code_editor as fce
import pytest

from fce_enhanced.editor import DEFAULT_CODE, EnhancedCodeEditor
from fce_enhanced.search import SearchReplaceBar
from fce_enhanced.themes import DEFAULT_THEME

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
    # Toolbar is the first control (appbar row with icon buttons)
    toolbar_row = editor.controls[0]
    tooltips = [
        c.tooltip for c in toolbar_row.controls if hasattr(c, "tooltip") and c.tooltip
    ]
    assert any("Open" in t for t in tooltips)
    assert any("Save As" in t for t in tooltips)
    assert any("Close" in t for t in tooltips)
    assert any("Find" in t for t in tooltips)


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
    editor = _make_editor(ruff_on_save=False)
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
            "fce_enhanced.editor.save_file",
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
            "fce_enhanced.editor.save_file",
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
            "fce_enhanced.editor.open_file",
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
            "fce_enhanced.editor.open_file",
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
        event.alt = False

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
        # On non-Mac: Ctrl+H opens find & replace
        with patch("platform.system", return_value="Linux"):
            event = MagicMock(spec=ft.KeyboardEvent)
            event.key = "H"
            event.meta = False
            event.ctrl = True
            event.shift = False
            event.alt = False

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
        event.alt = False

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


# --- File I/O error handling ---


@pytest.mark.asyncio
async def test_do_save_handles_write_error(tmp_path):
    editor = _make_editor(ruff_on_save=False)
    _, p1, p2, p3 = _patch_page(editor)
    try:
        editor._current_path = str(tmp_path / "output.py")
        editor._code_editor.value = "print('hello')"
        editor._mark_dirty()

        with patch("pathlib.Path.write_text", side_effect=PermissionError("denied")):
            result = await editor._do_save()

        assert result is False
        assert editor.dirty is True
    finally:
        _cleanup_patches(p1, p2, p3)


@pytest.mark.asyncio
async def test_do_save_as_write_error_preserves_path():
    """If Save As write fails, _current_path should not change."""
    editor = _make_editor(ruff_on_save=False)
    _, p1, p2, p3 = _patch_page(editor)
    try:
        editor._current_path = "/original/path.py"
        editor._code_editor.value = "content"

        with (
            patch(
                "fce_enhanced.editor.save_file",
                new_callable=AsyncMock,
                return_value="/new/path.py",
            ),
            patch("pathlib.Path.write_text", side_effect=OSError("disk full")),
        ):
            result = await editor._do_save_as()

        assert result is False
        assert editor._current_path == "/original/path.py"
    finally:
        _cleanup_patches(p1, p2, p3)


@pytest.mark.asyncio
async def test_handle_open_permission_error():
    editor = _make_editor()
    _, p1, p2, p3 = _patch_page(editor)
    try:
        with (
            patch(
                "fce_enhanced.editor.open_file",
                new_callable=AsyncMock,
                return_value="/some/file.py",
            ),
            patch(
                "pathlib.Path.read_text",
                side_effect=PermissionError("access denied"),
            ),
        ):
            await editor._handle_open(None)

        # Should show a snackbar error, not crash
        snackbars = [s for s in editor.page.overlay if isinstance(s, ft.SnackBar)]
        assert len(snackbars) == 1
        assert "access denied" in snackbars[0].content.value
        assert editor._current_path is None
    finally:
        _cleanup_patches(p1, p2, p3)


# --- Ruff on save ---


def _mock_ruff_process(returncode=0, stderr=b""):
    """Create a mock subprocess that returns immediately."""
    proc = MagicMock()
    proc.returncode = returncode
    proc.communicate = AsyncMock(return_value=(b"", stderr))
    return proc


@pytest.mark.asyncio
async def test_ruff_runs_on_python_save(tmp_path):
    editor = _make_editor(ruff_on_save=True)
    _, p1, p2, p3 = _patch_page(editor)
    try:
        filepath = tmp_path / "test.py"
        filepath.write_text("x=1\n", encoding="utf-8")
        editor._current_path = str(filepath)
        editor._code_editor.value = "x=1\n"
        editor._mark_dirty()

        mock_proc = _mock_ruff_process()
        with (
            patch("shutil.which", return_value="/usr/bin/ruff"),
            patch(
                "asyncio.create_subprocess_exec",
                new_callable=AsyncMock,
                return_value=mock_proc,
            ) as mock_exec,
        ):
            await editor._do_save()
            # Should have called ruff check --fix and ruff format
            assert mock_exec.call_count == 2
            args_list = [call.args for call in mock_exec.call_args_list]
            assert args_list[0] == ("/usr/bin/ruff", "check", "--fix", str(filepath))
            assert args_list[1] == ("/usr/bin/ruff", "format", str(filepath))
    finally:
        _cleanup_patches(p1, p2, p3)


@pytest.mark.asyncio
async def test_ruff_skips_non_python_files(tmp_path):
    editor = _make_editor(ruff_on_save=True)
    _, p1, p2, p3 = _patch_page(editor)
    try:
        filepath = tmp_path / "test.js"
        filepath.write_text("let x = 1;\n", encoding="utf-8")
        editor._current_path = str(filepath)
        editor._code_editor.value = "let x = 1;\n"

        with (
            patch("shutil.which", return_value="/usr/bin/ruff"),
            patch(
                "asyncio.create_subprocess_exec", new_callable=AsyncMock
            ) as mock_exec,
        ):
            await editor._run_ruff(str(filepath))
            mock_exec.assert_not_called()
    finally:
        _cleanup_patches(p1, p2, p3)


@pytest.mark.asyncio
async def test_ruff_skips_when_disabled(tmp_path):
    editor = _make_editor(ruff_on_save=False)
    _, p1, p2, p3 = _patch_page(editor)
    try:
        filepath = tmp_path / "test.py"
        filepath.write_text("x=1\n", encoding="utf-8")

        with (
            patch("shutil.which", return_value="/usr/bin/ruff"),
            patch(
                "asyncio.create_subprocess_exec", new_callable=AsyncMock
            ) as mock_exec,
        ):
            await editor._run_ruff(str(filepath))
            mock_exec.assert_not_called()
    finally:
        _cleanup_patches(p1, p2, p3)


@pytest.mark.asyncio
async def test_ruff_skips_when_not_installed(tmp_path):
    editor = _make_editor(ruff_on_save=True)
    _, p1, p2, p3 = _patch_page(editor)
    try:
        filepath = tmp_path / "test.py"
        filepath.write_text("x=1\n", encoding="utf-8")

        with (
            patch("shutil.which", return_value=None),
            patch(
                "asyncio.create_subprocess_exec", new_callable=AsyncMock
            ) as mock_exec,
        ):
            await editor._run_ruff(str(filepath))
            mock_exec.assert_not_called()
    finally:
        _cleanup_patches(p1, p2, p3)


@pytest.mark.asyncio
async def test_ruff_updates_editor_content(tmp_path):
    editor = _make_editor(ruff_on_save=True)
    _, p1, p2, p3 = _patch_page(editor)
    try:
        filepath = tmp_path / "test.py"
        editor._current_path = str(filepath)
        editor._code_editor.value = "x=1\n"
        filepath.write_text("x=1\n", encoding="utf-8")

        mock_proc = _mock_ruff_process()
        call_count = 0

        async def write_formatted(*args, **kwargs):
            """Simulate ruff reformatting the file on the format call."""
            nonlocal call_count
            call_count += 1
            if call_count == 2:  # ruff format is the second call
                filepath.write_text("x = 1\n", encoding="utf-8")
            return mock_proc

        with (
            patch("shutil.which", return_value="/usr/bin/ruff"),
            patch(
                "asyncio.create_subprocess_exec",
                side_effect=write_formatted,
            ),
        ):
            await editor._run_ruff(str(filepath))
            assert editor._code_editor.value == "x = 1\n"
            assert editor._last_saved_content == "x = 1\n"
    finally:
        _cleanup_patches(p1, p2, p3)


@pytest.mark.asyncio
async def test_ruff_check_failure_does_not_block_format(tmp_path):
    """ruff check exits non-zero for unfixable violations — format should still run."""
    editor = _make_editor(ruff_on_save=True)
    _, p1, p2, p3 = _patch_page(editor)
    try:
        filepath = tmp_path / "test.py"
        filepath.write_text("x=1\n", encoding="utf-8")

        mock_proc = _mock_ruff_process(returncode=1, stderr=b"lint warnings")
        with (
            patch("shutil.which", return_value="/usr/bin/ruff"),
            patch(
                "asyncio.create_subprocess_exec",
                new_callable=AsyncMock,
                return_value=mock_proc,
            ) as mock_exec,
        ):
            await editor._run_ruff(str(filepath))
            # Both check and format should be called
            assert mock_exec.call_count == 2
    finally:
        _cleanup_patches(p1, p2, p3)


@pytest.mark.asyncio
async def test_ruff_check_warnings_shown_in_snackbar(tmp_path):
    """Remaining lint warnings after --fix are shown to the user."""
    editor = _make_editor(ruff_on_save=True)
    _, p1, p2, p3 = _patch_page(editor)
    try:
        filepath = tmp_path / "test.py"
        filepath.write_text("x=1\n", encoding="utf-8")

        check_output = b"test.py:1:1: F841 Local variable `x` is assigned but never used\nFound 1 error.\n"
        check_proc = _mock_ruff_process(returncode=1, stderr=b"")
        check_proc.communicate = AsyncMock(return_value=(check_output, b""))
        fmt_proc = _mock_ruff_process(returncode=0)

        call_count = 0

        async def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return check_proc if call_count == 1 else fmt_proc

        with (
            patch("shutil.which", return_value="/usr/bin/ruff"),
            patch("asyncio.create_subprocess_exec", side_effect=side_effect),
        ):
            await editor._run_ruff(str(filepath))

        # A snackbar should have been added to the page overlay
        snackbars = [s for s in editor.page.overlay if isinstance(s, ft.SnackBar)]
        assert len(snackbars) == 1
        assert "F841" in snackbars[0].content.value
        assert "Found 1" not in snackbars[0].content.value  # summary filtered out
    finally:
        _cleanup_patches(p1, p2, p3)


@pytest.mark.asyncio
async def test_ruff_format_failure_bails_out(tmp_path):
    """If ruff format fails, we bail and don't reload the file."""
    editor = _make_editor(ruff_on_save=True)
    _, p1, p2, p3 = _patch_page(editor)
    try:
        filepath = tmp_path / "test.py"
        filepath.write_text("x=1\n", encoding="utf-8")
        editor._code_editor.value = "x=1\n"
        editor._last_saved_content = "x=1\n"

        ok_proc = _mock_ruff_process(returncode=0)
        fail_proc = _mock_ruff_process(returncode=1, stderr=b"format error")

        call_count = 0

        async def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return ok_proc if call_count == 1 else fail_proc

        with (
            patch("shutil.which", return_value="/usr/bin/ruff"),
            patch("asyncio.create_subprocess_exec", side_effect=side_effect),
        ):
            await editor._run_ruff(str(filepath))
            # Editor content should be unchanged
            assert editor._code_editor.value == "x=1\n"
    finally:
        _cleanup_patches(p1, p2, p3)


# --- Theme selector ---


def test_palette_button_in_appbar():
    editor = _make_editor()
    appbar = editor.controls[0]  # First row is the appbar
    icons = [btn.icon for btn in appbar.controls if isinstance(btn, ft.IconButton)]
    assert ft.Icons.PALETTE in icons


def test_default_theme_applied():
    editor = _make_editor()
    assert editor._code_editor.code_theme == DEFAULT_THEME
    assert editor._current_theme == DEFAULT_THEME


def test_select_theme_updates_code_editor():
    editor = _make_editor()
    _, p1, p2, p3 = _patch_page(editor)
    try:
        editor._select_theme(fce.CodeTheme.DRACULA)
        assert editor._code_editor.code_theme == fce.CodeTheme.DRACULA
        assert editor._current_theme == fce.CodeTheme.DRACULA
    finally:
        _cleanup_patches(p1, p2, p3)


def test_custom_theme_does_not_set_current_theme():
    custom = fce.CustomCodeTheme(
        keyword=ft.TextStyle(color=ft.Colors.RED),
    )
    editor = _make_editor(code_theme=custom)
    assert editor._current_theme is None


# --- Group 1: Toggle / font size state mutations ---


def test_ruff_on_save_property():
    editor = _make_editor(ruff_on_save=True)
    assert editor.ruff_on_save is True
    editor2 = _make_editor(ruff_on_save=False)
    assert editor2.ruff_on_save is False


def test_toggle_read_only():
    editor = _make_editor()
    _, p1, p2, p3 = _patch_page(editor)
    try:
        assert editor._code_editor.read_only is False
        editor._toggle_read_only()
        assert editor._code_editor.read_only is True
        assert editor._lock_btn.icon == ft.Icons.LOCK
        assert "Unlock" in editor._lock_btn.tooltip

        editor._toggle_read_only()
        assert editor._code_editor.read_only is False
        assert editor._lock_btn.icon == ft.Icons.LOCK_OPEN
    finally:
        _cleanup_patches(p1, p2, p3)


def test_toggle_ruff_on_save():
    editor = _make_editor(ruff_on_save=True)
    _, p1, p2, p3 = _patch_page(editor)
    try:
        editor._toggle_ruff_on_save(None)
        assert editor._ruff_on_save is False
        assert editor._ruff_btn.icon == ft.Icons.AUTO_FIX_OFF
        assert editor._ruff_btn.icon_color == ft.Colors.GREY_600
        assert "OFF" in editor._ruff_btn.tooltip

        editor._toggle_ruff_on_save(None)
        assert editor._ruff_on_save is True
        assert editor._ruff_btn.icon == ft.Icons.AUTO_FIX_HIGH
        assert editor._ruff_btn.icon_color is None
        assert "ON" in editor._ruff_btn.tooltip
    finally:
        _cleanup_patches(p1, p2, p3)


def test_change_font_size_increases():
    editor = _make_editor()
    _, p1, p2, p3 = _patch_page(editor)
    try:
        initial = editor._font_size
        editor._change_font_size(1)
        assert editor._font_size == initial + 1
        assert editor._font_size_label.value == f"{initial + 1}px"
    finally:
        _cleanup_patches(p1, p2, p3)


def test_change_font_size_decreases():
    editor = _make_editor()
    _, p1, p2, p3 = _patch_page(editor)
    try:
        initial = editor._font_size
        editor._change_font_size(-1)
        assert editor._font_size == initial - 1
    finally:
        _cleanup_patches(p1, p2, p3)


def test_change_font_size_clamps_at_min():
    from fce_enhanced.editor import MIN_FONT_SIZE

    editor = _make_editor()
    _, p1, p2, p3 = _patch_page(editor)
    try:
        editor._font_size = MIN_FONT_SIZE
        editor._change_font_size(-1)
        assert editor._font_size == MIN_FONT_SIZE
    finally:
        _cleanup_patches(p1, p2, p3)


def test_change_font_size_clamps_at_max():
    from fce_enhanced.editor import MAX_FONT_SIZE

    editor = _make_editor()
    _, p1, p2, p3 = _patch_page(editor)
    try:
        editor._font_size = MAX_FONT_SIZE
        editor._change_font_size(1)
        assert editor._font_size == MAX_FONT_SIZE
    finally:
        _cleanup_patches(p1, p2, p3)


# --- Group 2: Keyboard shortcut dispatch ---


def _make_key_event(key, *, meta=False, ctrl=False, shift=False, alt=False):
    """Create a mock KeyboardEvent."""
    event = MagicMock(spec=ft.KeyboardEvent)
    event.key = key
    event.meta = meta
    event.ctrl = ctrl
    event.shift = shift
    event.alt = alt
    return event


@pytest.mark.asyncio
async def test_keyboard_save():
    editor = _make_editor()
    _, p1, p2, p3 = _patch_page(editor)
    try:
        with patch.object(editor, "_do_save", new_callable=AsyncMock) as mock:
            await editor._handle_keyboard(_make_key_event("S", meta=True))
            mock.assert_awaited_once()
    finally:
        _cleanup_patches(p1, p2, p3)


@pytest.mark.asyncio
async def test_keyboard_save_as():
    editor = _make_editor()
    _, p1, p2, p3 = _patch_page(editor)
    try:
        with patch.object(editor, "_do_save_as", new_callable=AsyncMock) as mock:
            await editor._handle_keyboard(_make_key_event("S", meta=True, shift=True))
            mock.assert_awaited_once()
    finally:
        _cleanup_patches(p1, p2, p3)


@pytest.mark.asyncio
async def test_keyboard_open():
    editor = _make_editor()
    _, p1, p2, p3 = _patch_page(editor)
    try:
        with patch.object(editor, "_handle_open", new_callable=AsyncMock) as mock:
            await editor._handle_keyboard(_make_key_event("O", meta=True))
            mock.assert_awaited_once()
    finally:
        _cleanup_patches(p1, p2, p3)


@pytest.mark.asyncio
async def test_keyboard_close():
    editor = _make_editor()
    _, p1, p2, p3 = _patch_page(editor)
    try:
        with patch.object(editor, "_handle_close", new_callable=AsyncMock) as mock:
            await editor._handle_keyboard(_make_key_event("W", meta=True))
            mock.assert_awaited_once()
    finally:
        _cleanup_patches(p1, p2, p3)


@pytest.mark.asyncio
async def test_keyboard_goto_line():
    editor = _make_editor()
    _, p1, p2, p3 = _patch_page(editor)
    try:
        with patch.object(editor, "_handle_goto_line", new_callable=AsyncMock) as mock:
            await editor._handle_keyboard(_make_key_event("G", meta=True))
            mock.assert_awaited_once()
    finally:
        _cleanup_patches(p1, p2, p3)


@pytest.mark.asyncio
async def test_keyboard_toggle_read_only():
    editor = _make_editor()
    _, p1, p2, p3 = _patch_page(editor)
    try:
        with patch.object(editor, "_toggle_read_only") as mock:
            await editor._handle_keyboard(_make_key_event("L", meta=True))
            mock.assert_called_once()
    finally:
        _cleanup_patches(p1, p2, p3)


@pytest.mark.asyncio
async def test_keyboard_language():
    editor = _make_editor()
    _, p1, p2, p3 = _patch_page(editor)
    try:
        with patch.object(editor, "_handle_language_click") as mock:
            await editor._handle_keyboard(_make_key_event("L", meta=True, shift=True))
            mock.assert_called_once()
    finally:
        _cleanup_patches(p1, p2, p3)


@pytest.mark.asyncio
async def test_keyboard_font_increase():
    editor = _make_editor()
    _, p1, p2, p3 = _patch_page(editor)
    try:
        with patch.object(editor, "_change_font_size") as mock:
            await editor._handle_keyboard(_make_key_event("EQUAL", meta=True))
            mock.assert_called_once_with(1)
    finally:
        _cleanup_patches(p1, p2, p3)


@pytest.mark.asyncio
async def test_keyboard_font_decrease():
    editor = _make_editor()
    _, p1, p2, p3 = _patch_page(editor)
    try:
        with patch.object(editor, "_change_font_size") as mock:
            await editor._handle_keyboard(_make_key_event("MINUS", meta=True))
            mock.assert_called_once_with(-1)
    finally:
        _cleanup_patches(p1, p2, p3)


@pytest.mark.asyncio
async def test_keyboard_toggle_diff():
    editor = _make_editor()
    _, p1, p2, p3 = _patch_page(editor)
    try:
        with patch.object(editor, "_toggle_diff_pane") as mock:
            await editor._handle_keyboard(_make_key_event("D", meta=True))
            mock.assert_called_once()
    finally:
        _cleanup_patches(p1, p2, p3)


@pytest.mark.asyncio
async def test_keyboard_f1_help():
    editor = _make_editor()
    _, p1, p2, p3 = _patch_page(editor)
    try:
        with patch.object(editor, "_show_help") as mock:
            await editor._handle_keyboard(_make_key_event("F1", meta=False, ctrl=False))
            mock.assert_called_once()
    finally:
        _cleanup_patches(p1, p2, p3)


@pytest.mark.asyncio
async def test_keyboard_command_palette():
    editor = _make_editor()
    _, p1, p2, p3 = _patch_page(editor)
    try:
        with patch.object(
            editor, "_open_command_palette", new_callable=AsyncMock
        ) as mock:
            await editor._handle_keyboard(_make_key_event("P", meta=True, shift=True))
            mock.assert_awaited_once()
    finally:
        _cleanup_patches(p1, p2, p3)


@pytest.mark.asyncio
async def test_keyboard_alt_f_opens_replace_on_mac():
    editor = _make_editor()
    _, p1, p2, p3 = _patch_page(editor)
    focus_patch = patch.object(
        editor._search_bar._search_field, "focus", new_callable=AsyncMock
    )
    focus_patch.start()
    try:
        with patch("platform.system", return_value="Darwin"):
            await editor._handle_keyboard(_make_key_event("F", meta=True, alt=True))
        assert editor._search_bar.is_open is True
        assert editor._search_bar._replace_row.visible is True
    finally:
        focus_patch.stop()
        _cleanup_patches(p1, p2, p3)


@pytest.mark.asyncio
async def test_keyboard_no_meta_ctrl_ignored():
    """Keys without meta/ctrl (except Escape/F1) should be ignored."""
    editor = _make_editor()
    _, p1, p2, p3 = _patch_page(editor)
    try:
        with patch.object(editor, "_do_save", new_callable=AsyncMock) as mock:
            await editor._handle_keyboard(_make_key_event("S"))
            mock.assert_not_awaited()
    finally:
        _cleanup_patches(p1, p2, p3)


# --- Group 3: _line_to_offset, status bar, selection change ---


def test_line_to_offset_first_line():
    assert EnhancedCodeEditor._line_to_offset("hello\nworld\nfoo", 1) == 0


def test_line_to_offset_second_line():
    assert EnhancedCodeEditor._line_to_offset("hello\nworld\nfoo", 2) == 6


def test_line_to_offset_third_line():
    assert EnhancedCodeEditor._line_to_offset("hello\nworld\nfoo", 3) == 12


def test_update_status_bar_default():
    editor = _make_editor()
    editor._update_status_bar()
    assert editor._status_bar.value == "Ln 1, Col 1 | Python"


def test_update_status_bar_with_position():
    editor = _make_editor()
    editor._update_status_bar(line=5, col=10)
    assert "Ln 5, Col 10" in editor._status_bar.value


def test_update_status_bar_with_selection():
    editor = _make_editor()
    editor._update_status_bar(line=1, col=1, selected_text="hello")
    assert "5 chars selected" in editor._status_bar.value


def test_update_status_bar_language_name():
    editor = _make_editor(language=fce.CodeLanguage.JAVASCRIPT)
    editor._update_status_bar()
    assert "Javascript" in editor._status_bar.value


def test_handle_selection_change():
    editor = _make_editor(value="hello\nworld")
    _, p1, p2, p3 = _patch_page(editor)
    try:
        event = MagicMock()
        event.selection.end = 8  # "wor" on second line
        event.selected_text = "wo"
        editor._handle_selection_change(event)
        assert "Ln 2, Col 3" in editor._status_bar.value
        assert "2 chars selected" in editor._status_bar.value
    finally:
        _cleanup_patches(p1, p2, p3)


# --- Group 4: _handle_close (non-dirty), _toggle_diff_pane, _handle_change revert ---


@pytest.mark.asyncio
async def test_handle_close_non_dirty_resets():
    """Close when not dirty should reset without showing a dialog."""
    editor = _make_editor()
    _, p1, p2, p3 = _patch_page(editor)
    try:
        editor._current_path = "/tmp/test.py"
        editor._code_editor.value = "content"
        # Not dirty, so no confirm dialog should be called
        with patch.object(editor, "_confirm_discard") as mock_confirm:
            await editor._handle_close(None)
            mock_confirm.assert_not_called()

        assert editor.current_path is None
        assert editor.value == DEFAULT_CODE
        assert editor.dirty is False
    finally:
        _cleanup_patches(p1, p2, p3)


@pytest.mark.asyncio
async def test_handle_close_closes_diff_pane():
    """Close should also close an open diff pane."""
    editor = _make_editor()
    _, p1, p2, p3 = _patch_page(editor)
    try:
        editor._diff_pane._is_open = True
        await editor._handle_close(None)
        assert editor._diff_pane.is_open is False
        assert editor._diff_btn.icon_color is None
    finally:
        _cleanup_patches(p1, p2, p3)


def test_toggle_diff_pane_open():
    editor = _make_editor()
    _, p1, p2, p3 = _patch_page(editor)
    try:
        assert editor._diff_pane.is_open is False
        editor._toggle_diff_pane()
        assert editor._diff_pane.is_open is True
        assert editor._diff_btn.icon_color == ft.Colors.BLUE
    finally:
        _cleanup_patches(p1, p2, p3)


def test_toggle_diff_pane_close():
    editor = _make_editor()
    _, p1, p2, p3 = _patch_page(editor)
    try:
        editor._diff_pane._is_open = True
        editor._toggle_diff_pane()
        assert editor._diff_pane.is_open is False
        assert editor._diff_btn.icon_color is None
    finally:
        _cleanup_patches(p1, p2, p3)


def test_on_diff_closed_resets_button():
    editor = _make_editor()
    _, p1, p2, p3 = _patch_page(editor)
    try:
        editor._diff_btn.icon_color = ft.Colors.BLUE
        editor._on_diff_closed()
        assert editor._diff_btn.icon_color is None
    finally:
        _cleanup_patches(p1, p2, p3)


def test_handle_change_reverts_to_clean():
    """If content is edited back to match saved content, dirty state should clear."""
    editor = _make_editor(value="original")
    _, p1, p2, p3 = _patch_page(editor)
    try:
        editor._last_saved_content = "original"
        # First make it dirty
        editor._code_editor.value = "modified"
        editor._handle_change(None)
        assert editor.dirty is True

        # Now revert to original
        editor._code_editor.value = "original"
        editor._handle_change(None)
        assert editor.dirty is False
        assert editor._save_btn.disabled is True
    finally:
        _cleanup_patches(p1, p2, p3)


def test_handle_change_recomputes_diff_when_open():
    editor = _make_editor(value="original")
    _, p1, p2, p3 = _patch_page(editor)
    try:
        editor._diff_pane._is_open = True
        with patch.object(editor._diff_pane, "recompute") as mock_recompute:
            editor._code_editor.value = "modified"
            editor._handle_change(None)
            mock_recompute.assert_called_once()
    finally:
        _cleanup_patches(p1, p2, p3)
