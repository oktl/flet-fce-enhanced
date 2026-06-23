"""Enhanced CodeEditor with file I/O, search/replace, and syntax highlighting.

Built on the CodeEditor control from Flet docs
https://docs.flet.dev/codeeditor/ with a full-featured toolbar including
file operations, find/replace, go-to-line, font sizing, read-only toggle,
ruff on-save toggle, diff view on toggle, language and theme selectors,
command palette, and help.

This module uses Flet's declarative API (``@ft.component`` + ``use_state``).
The editor is a component function; external callers drive it through an
:class:`EditorHandle` passed as the ``handle`` prop (e.g. ``handle.open_path``).

UI dialogs (theme/language pickers, go-to-line, command palette,
confirm-discard, and help) are defined in ``dialogs.py``. A toggleable unified
diff view is provided by ``DiffPane`` from ``diff_pane.py``.
"""

from __future__ import annotations

import asyncio
from contextlib import suppress
from dataclasses import dataclass, field
from pathlib import Path
import platform
import shutil
import sys
from typing import Any

import flet as ft
import flet_code_editor as fce
from loguru import logger

from fce_enhanced.dialogs import (
    confirm_discard,
    confirm_revert,
    goto_line_dialog,
    open_command_palette,
    show_help_dialog,
    show_language_dialog,
    show_theme_dialog,
)
from fce_enhanced.diff_pane import DiffPane
from fce_enhanced.file_dialog import open_file, save_file
from fce_enhanced.help_content import HELP_TEXT
from fce_enhanced.languages import extension_for_language, language_for_path
from fce_enhanced.search import SearchReplaceBar
from fce_enhanced.themes import DEFAULT_THEME, THEMES

DEFAULT_CODE = """\
# New file
"""

APPBAR_HEIGHT = 18
ICON_SIZE = 18
DEFAULT_FONT_SIZE = 13
MIN_FONT_SIZE = 8
MAX_FONT_SIZE = 32
TOGGLE_ACTIVE_COLOR = ft.Colors.BLUE


def _language_display_name(lang: fce.CodeLanguage) -> str:
    return lang.name.replace("_", " ").title()


def _offset_to_line_col(text: str, offset: int) -> tuple[int, int]:
    before = text[: max(0, offset)]
    lines = before.split("\n")
    return len(lines), len(lines[-1]) + 1


def _line_to_offset(text: str, line: int) -> int:
    """Return the character offset of the start of a 1-based line number."""
    lines = text.split("\n")
    return sum(len(lines[i]) + 1 for i in range(min(line - 1, len(lines))))


@dataclass
class EditorHandle:
    """Imperative handle to a mounted :func:`EnhancedCodeEditor` component.

    Populated on every render so external callers can drive the editor without
    a control instance. Coroutine methods (``open_path``, ``save``,
    ``save_as``, ``close``) are scheduled with ``page.run_task``. Read-only
    accessors (``value``, ``dirty``, ``current_path``) reflect live state.
    """

    open_path: Any = None
    save: Any = None
    save_as: Any = None
    close: Any = None
    _get_value: Any = None
    _get_dirty: Any = None
    _get_path: Any = None

    @property
    def value(self) -> str:
        return self._get_value() if self._get_value else ""

    @property
    def dirty(self) -> bool:
        return self._get_dirty() if self._get_dirty else False

    @property
    def current_path(self) -> str | None:
        return self._get_path() if self._get_path else None


@dataclass
class _Refs:
    """Mutable, render-stable state that should not trigger re-renders.

    ``text`` is the authoritative current content, kept in sync by the editor's
    ``on_change``. ``last_saved`` is the content as of the last save/load, used
    for dirty tracking and the diff pane.
    """

    text: str = ""
    last_saved: str = ""
    snackbar: ft.SnackBar | None = None
    editor: ft.Ref = field(default_factory=ft.Ref)
    keyboard: Any = None


@ft.component
def EnhancedCodeEditor(
    language: fce.CodeLanguage = fce.CodeLanguage.PLAINTEXT,
    value: str = DEFAULT_CODE,
    show_toolbar: bool = True,
    show_status_bar: bool = True,
    show_gutter: bool = True,
    register_keyboard_shortcuts: bool = True,
    autocomplete: bool = True,
    autocomplete_words: list[str] | None = None,
    code_theme: fce.CustomCodeTheme | None = None,
    text_style: ft.TextStyle | None = None,
    gutter_style: fce.GutterStyle | None = None,
    on_title_change=None,
    ruff_on_save: bool = False,
    initial_path: str | None = None,
    handle: EditorHandle | None = None,
    expand: bool = False,
) -> ft.Control:
    """A reusable Flet CodeEditor with a full-featured toolbar.

    Toolbar: Open, Save, Save As, Close, Revert, Find, Go to Line, Font Size
    +/-, Diff, Read-Only toggle, Ruff On/Off toggle, Gutter toggle, Language
    selector, Theme selector, and Help.

    Keyboard shortcuts (Cmd/Ctrl unless noted):
        O/S/Shift+S/W — file ops | F — find | Option+F / Ctrl+H — replace |
        G — go to line | L — read-only | Shift+L — language | Shift+G — gutter |
        Shift+R — revert | +/- — font size | Shift+P — palette | F1 — help |
        Esc — close search | D — diff

    Args:
        language: Initial code language for syntax highlighting.
        value: Initial editor content.
        show_toolbar: Whether to show the file I/O toolbar.
        show_status_bar: Whether to show the line/column status bar.
        show_gutter: Whether to initially show the line-number gutter.
        register_keyboard_shortcuts: Whether to register global keyboard shortcuts.
        autocomplete: Whether to enable autocomplete.
        autocomplete_words: Words for autocomplete suggestions.
        code_theme: Custom code theme for syntax highlighting.
        text_style: Text style for the editor content.
        gutter_style: Style for the line number gutter.
        on_title_change: Callback ``(display_path, name, is_dirty)`` fired when
            the file title or dirty state changes.
        ruff_on_save: Run ruff check --fix and ruff format on Python files after
            saving. Requires ruff installed. Defaults to False.
        initial_path: File to open automatically on mount (e.g. from argv).
        handle: Optional :class:`EditorHandle` populated with imperative methods.
        expand: Whether the root column should expand to fill its parent.
    """
    if code_theme is None:
        code_theme = DEFAULT_THEME
    base_theme: fce.CodeTheme | None = (
        code_theme if isinstance(code_theme, fce.CodeTheme) else None
    )

    default_text_style = text_style or ft.TextStyle(
        font_family="monospace", height=1.2, size=DEFAULT_FONT_SIZE
    )
    visible_gutter = gutter_style or fce.GutterStyle(
        text_style=ft.TextStyle(font_family="monospace", height=1.2),
        show_line_numbers=True,
        show_folding_handles=True,
        width=80,
    )
    hidden_gutter = fce.GutterStyle(
        show_line_numbers=False,
        show_folding_handles=False,
        show_errors=False,
        width=0,
        margin=0,
    )

    # --- State (drives re-render) ---
    current_path, set_current_path = ft.use_state(None)
    dirty, set_dirty = ft.use_state(False)
    gutter_on, set_gutter_on = ft.use_state(show_gutter)
    ruff_on, set_ruff_on = ft.use_state(ruff_on_save)
    read_only, set_read_only = ft.use_state(False)
    font_size, set_font_size = ft.use_state(
        int(default_text_style.size or DEFAULT_FONT_SIZE)
    )
    lang, set_lang = ft.use_state(language)
    theme, set_theme = ft.use_state(base_theme)
    search_open, set_search_open = ft.use_state(False)
    search_with_replace, set_search_with_replace = ft.use_state(False)
    diff_open, set_diff_open = ft.use_state(False)
    editor_value, set_editor_value = ft.use_state(value)
    text_version, set_text_version = ft.use_state(0)
    status, set_status = ft.use_state((1, 1, 0))
    selection, set_selection = ft.use_state(
        ft.TextSelection(base_offset=0, extent_offset=0)
    )

    # --- Refs (mutable, no re-render) ---
    refs = ft.use_ref(lambda: _Refs(text=value, last_saved=value))
    r: _Refs = refs.current
    page = ft.context.page

    # --- Editor-control helpers ---

    def _load_content(content: str, *, mark_clean: bool = False) -> None:
        """Set editor content programmatically (controlled ``value`` prop).

        ``editor_value`` state is the editor's ``value`` prop; changing it
        re-renders and patches the new content onto the live control. Cursor is
        reset to the top via ``selection``.
        """
        r.text = content
        if mark_clean:
            r.last_saved = content
            set_dirty(False)
        else:
            set_dirty(content != r.last_saved)
        set_editor_value(content)
        set_selection(ft.TextSelection(base_offset=0, extent_offset=0))
        set_text_version(text_version + 1)

    async def _focus_editor() -> None:
        # Best-effort: focus() is a method invoke (no prop mutation), so it is
        # safe even on a frozen render snapshot as long as it is mounted.
        ctrl = r.editor.current
        if ctrl is not None:
            with suppress(Exception):
                await ctrl.focus()

    def _focus_editor_sync() -> None:
        page.run_task(_focus_editor)

    def _set_editor_selection(base: int, extent: int) -> None:
        set_selection(ft.TextSelection(base_offset=base, extent_offset=extent))

    def _apply_replace_text(new_text: str) -> None:
        _load_content(new_text)

    # --- Snackbar ---

    def _dismiss_snackbar() -> None:
        if r.snackbar is not None and r.snackbar.open:
            page.pop_dialog()

    def _show_snackbar(message: str, *, is_error: bool = False) -> None:
        if r.snackbar is not None and r.snackbar.open:
            page.pop_dialog()
        snack = ft.SnackBar(
            ft.Text(message, color=ft.Colors.WHITE, selectable=True),
            bgcolor=ft.Colors.RED_800 if is_error else ft.Colors.GREY_800,
            action="Dismiss",
            duration=86400000,  # effectively permanent until dismissed
        )
        r.snackbar = snack
        page.show_dialog(snack)

    # --- Dirty / clean ---

    def _mark_clean(content: str) -> None:
        r.last_saved = content
        set_dirty(False)

    # --- Ruff on save ---

    async def _run_ruff(path: str) -> None:
        if not ruff_on or not path.endswith(".py"):
            return
        ruff = shutil.which("ruff")
        if ruff is None:
            logger.debug("ruff not found on PATH, skipping post-save formatting")
            return

        check_proc = await asyncio.create_subprocess_exec(
            ruff,
            "check",
            "--fix",
            path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        check_stdout, _ = await check_proc.communicate()
        check_output = check_stdout.decode().strip()
        if check_proc.returncode != 0 and check_output:
            lines = [
                ln for ln in check_output.splitlines() if not ln.startswith("Found ")
            ]
            if lines:
                _show_snackbar(f"Ruff: {'; '.join(lines)}", is_error=True)

        fmt_proc = await asyncio.create_subprocess_exec(
            ruff,
            "format",
            path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, fmt_stderr = await fmt_proc.communicate()
        if fmt_proc.returncode != 0:
            msg = fmt_stderr.decode().strip()
            logger.warning("ruff format failed: {}", msg)
            _show_snackbar(f"Ruff format failed: {msg}", is_error=True)
            return

        try:
            formatted = Path(path).read_text(encoding="utf-8")
        except OSError as exc:
            logger.warning("Failed to reload after ruff: {}", exc)
            return
        if formatted != r.text:
            _load_content(formatted, mark_clean=True)

    # --- File operations ---

    async def open_path(path: str) -> None:
        try:
            content = Path(path).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError, ValueError) as exc:
            _show_snackbar(f"Cannot open file: {exc}", is_error=True)
            return
        set_diff_open(False)
        set_lang(language_for_path(path))
        set_current_path(path)
        set_ruff_on(path.endswith(".py"))
        _load_content(content, mark_clean=True)

    async def _handle_open(_e=None) -> None:
        if dirty:
            action = await confirm_discard(page)
            if action == "save":
                if not await _do_save():
                    return
            elif action == "cancel":
                return
        path = await open_file("Open File")
        if path is None:
            return
        await open_path(path)

    async def _do_save() -> bool:
        if current_path is None:
            return await _do_save_as()
        content = r.text
        try:
            Path(current_path).write_text(content, encoding="utf-8")
        except OSError as exc:
            logger.error("Failed to save {}: {}", current_path, exc)
            _show_snackbar(f"Save failed: {exc}", is_error=True)
            return False
        _dismiss_snackbar()
        _mark_clean(content)
        await _run_ruff(current_path)
        return True

    async def _do_save_as() -> bool:
        if current_path:
            default = Path(current_path).name
        else:
            default = f"untitled{extension_for_language(lang)}"
        path = await save_file("Save File", default)
        if path is None:
            return False
        content = r.text
        try:
            Path(path).write_text(content, encoding="utf-8")
        except OSError as exc:
            logger.error("Failed to save {}: {}", path, exc)
            _show_snackbar(f"Save failed: {exc}", is_error=True)
            return False
        _dismiss_snackbar()
        set_current_path(path)
        set_lang(language_for_path(path))
        set_ruff_on(path.endswith(".py"))
        _mark_clean(content)
        await _run_ruff(path)
        return True

    async def _do_close(_e=None) -> None:
        if dirty:
            action = await confirm_discard(page)
            if action == "save":
                if not await _do_save():
                    return
            elif action == "cancel":
                return
        set_diff_open(False)
        set_current_path(None)
        set_ruff_on(False)
        set_lang(fce.CodeLanguage.PYTHON)
        _load_content(DEFAULT_CODE, mark_clean=True)

    async def _handle_revert(_e=None) -> None:
        if not dirty:
            return
        if not await confirm_revert(page):
            return
        set_diff_open(False)
        _load_content(r.last_saved, mark_clean=True)

    # --- Theme / language ---

    def _handle_theme_click(_e=None) -> None:
        show_theme_dialog(page, THEMES, theme, _select_theme)

    def _select_theme(selected: fce.CodeTheme) -> None:
        set_theme(selected)
        page.pop_dialog()

    def _handle_language_click(_e=None) -> None:
        show_language_dialog(page, lang, _select_language)

    def _select_language(selected: fce.CodeLanguage) -> None:
        set_lang(selected)
        page.pop_dialog()

    # --- Toggles ---

    def _toggle_read_only() -> None:
        set_read_only(not read_only)

    def _toggle_ruff_on_save(_e=None) -> None:
        set_ruff_on(not ruff_on)

    def _toggle_gutter() -> None:
        set_gutter_on(not gutter_on)

    def _toggle_diff_pane() -> None:
        set_diff_open(not diff_open)

    def _change_font_size(delta: int) -> None:
        new_size = max(MIN_FONT_SIZE, min(MAX_FONT_SIZE, font_size + delta))
        if new_size != font_size:
            set_font_size(new_size)

    # --- Search ---

    def _open_search(*, with_replace: bool = False) -> None:
        set_search_with_replace(with_replace)
        set_search_open(True)

    def _close_search() -> None:
        set_search_open(False)

    # --- Go to line ---

    async def _handle_goto_line(_e=None) -> None:
        content = r.text
        max_lines = content.count("\n") + 1
        line_num = await goto_line_dialog(page, max_lines)
        if line_num is not None:
            offset = _line_to_offset(content, line_num)
            _set_editor_selection(offset, offset)
            await _focus_editor()

    # --- Help / palette ---

    def _show_help(_e=None) -> None:
        show_help_dialog(page, HELP_TEXT)

    async def _open_command_palette() -> None:
        is_mac = platform.system() == "Darwin"
        mod = "⌘" if is_mac else "Ctrl+"
        shift_mod = "⇧⌘" if is_mac else "Ctrl+Shift+"
        commands = [
            ("Open File", f"{mod}O", _handle_open),
            ("Save", f"{mod}S", lambda _e: _do_save()),
            ("Save As", f"{shift_mod}S", lambda _e: _do_save_as()),
            ("Close File", f"{mod}W", _do_close),
            ("Revert to Saved", f"{shift_mod}R", _handle_revert),
            ("Find", f"{mod}F", lambda _e: _open_search(with_replace=False)),
            (
                "Find and Replace",
                f"⌥{mod}F" if is_mac else "Ctrl+H",
                lambda _e: _open_search(with_replace=True),
            ),
            ("Go to Line", f"{mod}G", _handle_goto_line),
            ("Toggle Diff", f"{mod}D", lambda _e: _toggle_diff_pane()),
            ("Choose Theme", "", _handle_theme_click),
            ("Choose Language", f"{shift_mod}L", _handle_language_click),
            ("Toggle Read-Only", f"{mod}L", lambda _e: _toggle_read_only()),
            ("Toggle Gutter", f"{shift_mod}G", lambda _e: _toggle_gutter()),
            ("Increase Font Size", f"{mod}+", lambda _e: _change_font_size(1)),
            ("Decrease Font Size", f"{mod}-", lambda _e: _change_font_size(-1)),
            ("Help", "F1", _show_help),
        ]
        await open_command_palette(page, commands)

    # --- Keyboard ---

    async def _handle_keyboard(e: ft.KeyboardEvent) -> None:
        if e.key == "Escape" and search_open:
            _close_search()
            return
        if e.key == "F1":
            _show_help()
            return
        if not (e.meta or e.ctrl):
            return
        is_mac = platform.system() == "Darwin"
        key = e.key.upper()
        match key:
            case "P" if e.shift:
                await _open_command_palette()
            case "F" if e.alt and is_mac:
                _open_search(with_replace=True)
            case "F":
                _open_search(with_replace=False)
            case "H" if not is_mac:
                _open_search(with_replace=True)
            case "S" if not e.shift:
                await _do_save()
            case "S":
                await _do_save_as()
            case "O":
                await _handle_open()
            case "W":
                await _do_close()
            case "R" if e.shift:
                await _handle_revert()
            case "L" if e.shift:
                _handle_language_click()
            case "L":
                _toggle_read_only()
            case "G" if e.shift:
                _toggle_gutter()
            case "G":
                await _handle_goto_line()
            case "EQUAL" | "+" | "=":
                _change_font_size(1)
            case "MINUS" | "-":
                _change_font_size(-1)
            case "D":
                _toggle_diff_pane()

    r.keyboard = _handle_keyboard

    # --- Editor change / selection ---

    def _on_change(e) -> None:
        r.text = e.control.value or ""
        # Keep editor_value in sync with live text so a later programmatic
        # reload of identical-to-saved content (e.g. revert after edits) is
        # still a real state change that patches the control.
        set_editor_value(r.text)
        new_dirty = r.text != r.last_saved
        if new_dirty != dirty:
            set_dirty(new_dirty)
        if search_open or diff_open:
            set_text_version(text_version + 1)

    def _on_selection_change(e) -> None:
        caret = e.selection.end
        sel = e.selected_text or ""
        line, col = _offset_to_line_col(r.text, caret)
        set_status((line, col, len(sel)))
        # Keep selection state in sync with the user's cursor so unrelated
        # re-renders don't re-send a stale selection and yank the cursor.
        set_selection(e.selection)

    # --- Effects ---

    def _notify_title():
        if on_title_change:
            display, name = _title_parts(current_path)
            on_title_change(display, name, dirty)

    ft.use_effect(_notify_title, [current_path, dirty])

    def _register_keyboard():
        if not register_keyboard_shortcuts:
            return
        page.on_keyboard_event = lambda e: page.run_task(r.keyboard, e)

    def _unregister_keyboard():
        if register_keyboard_shortcuts:
            page.on_keyboard_event = None

    ft.use_effect(_register_keyboard, [], _unregister_keyboard)

    def _open_initial():
        if initial_path:
            page.run_task(open_path, initial_path)

    ft.use_effect(_open_initial, [])

    # --- Imperative handle ---

    if handle is not None:
        handle.open_path = lambda path: page.run_task(open_path, path)
        handle.save = lambda: page.run_task(_do_save)
        handle.save_as = lambda: page.run_task(_do_save_as)
        handle.close = lambda: page.run_task(_do_close)
        handle._get_value = lambda: r.text
        handle._get_dirty = lambda: dirty
        handle._get_path = lambda: current_path

    # --- Render ---

    active_text_style = ft.TextStyle(
        font_family="monospace", height=1.2, size=font_size
    )
    editor_control = fce.CodeEditor(
        ref=r.editor,
        language=lang,
        code_theme=theme,
        autocomplete=autocomplete,
        autocomplete_words=autocomplete_words or [],
        value=editor_value,
        selection=selection,
        autofocus=True,
        read_only=read_only,
        text_style=active_text_style,
        gutter_style=visible_gutter if gutter_on else hidden_gutter,
        on_selection_change=_on_selection_change,
        on_change=_on_change,
        expand=True,
    )

    controls: list[ft.Control] = []

    if show_toolbar:
        controls.append(
            _build_toolbar(
                dirty=dirty,
                read_only=read_only,
                ruff_on=ruff_on,
                gutter_on=gutter_on,
                diff_open=diff_open,
                lang=lang,
                on_open=lambda _e: page.run_task(_handle_open),
                on_save=lambda _e: page.run_task(_do_save),
                on_save_as=lambda _e: page.run_task(_do_save_as),
                on_close=lambda _e: page.run_task(_do_close),
                on_revert=lambda _e: page.run_task(_handle_revert),
                on_find=lambda _e: _open_search(with_replace=False),
                on_goto=lambda _e: page.run_task(_handle_goto_line),
                on_font_dec=lambda _e: _change_font_size(-1),
                on_font_inc=lambda _e: _change_font_size(1),
                font_size=font_size,
                on_diff=lambda _e: _toggle_diff_pane(),
                on_lock=lambda _e: _toggle_read_only(),
                on_ruff=_toggle_ruff_on_save,
                on_gutter=lambda _e: _toggle_gutter(),
                on_lang=_handle_language_click,
                on_theme=_handle_theme_click,
                on_help=_show_help,
            )
        )

    if search_open:
        controls.append(
            SearchReplaceBar(
                get_text=lambda: r.text,
                set_selection=_set_editor_selection,
                replace_text=_apply_replace_text,
                focus_editor=_focus_editor_sync,
                on_close=_close_search,
                with_replace=search_with_replace,
                text_version=text_version,
            )
        )

    controls.append(ft.Divider(height=1, color=ft.Colors.GREY_800))

    display, _name = _title_parts(current_path)
    controls.append(
        ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            controls=[
                ft.Text("File: ", size=12, color=ft.Colors.GREY_600),
                ft.Text(
                    display,
                    size=12,
                    color=ft.Colors.AMBER_600 if dirty else ft.Colors.GREY_600,
                ),
            ],
        )
    )

    controls.append(editor_control)

    if show_status_bar:
        line, col, sel_len = status
        lang_name = _language_display_name(lang) if lang else "Plain Text"
        sel_info = f" | {sel_len} chars selected" if sel_len else ""
        controls.append(
            ft.Row(
                controls=[
                    ft.Text(
                        f"Ln {line}, Col {col} | {lang_name}{sel_info}",
                        size=12,
                        color=ft.Colors.GREY_600,
                    )
                ]
            )
        )

    if diff_open:
        controls.append(
            DiffPane(
                original_text=r.last_saved,
                current_text=r.text,
                on_close=lambda: set_diff_open(False),
                code_theme=theme,
            )
        )

    return ft.Column(controls=controls, spacing=10, expand=expand)


def _title_parts(current_path: str | None) -> tuple[str, str]:
    if not current_path:
        return "untitled", "untitled"
    try:
        display = "~/" + str(Path(current_path).relative_to(Path.home()))
    except ValueError:
        display = current_path
    return display, Path(current_path).name


def _divider() -> ft.Control:
    return ft.Container(
        content=ft.VerticalDivider(width=1, thickness=2, color=ft.Colors.GREY_600),
        height=APPBAR_HEIGHT - 2,
    )


def _build_toolbar(
    *,
    dirty: bool,
    read_only: bool,
    ruff_on: bool,
    gutter_on: bool,
    diff_open: bool,
    lang: fce.CodeLanguage,
    on_open,
    on_save,
    on_save_as,
    on_close,
    on_revert,
    on_find,
    on_goto,
    on_font_dec,
    on_font_inc,
    font_size: int,
    on_diff,
    on_lock,
    on_ruff,
    on_gutter,
    on_lang,
    on_theme,
    on_help,
) -> ft.Control:
    return ft.Row(
        spacing=0,
        controls=[
            ft.IconButton(
                ft.Icons.FILE_OPEN,
                icon_size=ICON_SIZE,
                tooltip="Open (⌘O)",
                on_click=on_open,
            ),
            ft.IconButton(
                ft.Icons.SAVE,
                icon_size=ICON_SIZE,
                tooltip="Save (⌘S)",
                on_click=on_save,
                disabled=not dirty,
            ),
            ft.IconButton(
                ft.Icons.SAVE_AS,
                icon_size=ICON_SIZE,
                tooltip="Save As (⇧⌘S)",
                on_click=on_save_as,
            ),
            ft.IconButton(
                ft.Icons.CLOSE,
                icon_size=ICON_SIZE,
                tooltip="Close File (⌘W) ",
                on_click=on_close,
            ),
            ft.IconButton(
                ft.Icons.SETTINGS_BACKUP_RESTORE,
                icon_size=ICON_SIZE,
                tooltip="Revert to Saved (⇧⌘R)",
                on_click=on_revert,
                disabled=not dirty,
            ),
            _divider(),
            ft.IconButton(
                ft.Icons.SEARCH,
                icon_size=ICON_SIZE,
                tooltip="Find (⌘F)",
                on_click=on_find,
            ),
            ft.IconButton(
                ft.Icons.FORMAT_LIST_NUMBERED,
                icon_size=ICON_SIZE,
                tooltip="Go to Line (⌘G)",
                on_click=on_goto,
            ),
            ft.IconButton(
                ft.Icons.REMOVE,
                icon_size=ICON_SIZE,
                tooltip="Decrease Font Size (⌘-)",
                on_click=on_font_dec,
            ),
            ft.Text(f"{font_size}px", size=11, color=ft.Colors.GREY_600),
            ft.IconButton(
                ft.Icons.ADD,
                icon_size=ICON_SIZE,
                tooltip="Increase Font Size (⌘+)",
                on_click=on_font_inc,
            ),
            _divider(),
            ft.IconButton(
                ft.Icons.DIFFERENCE,
                icon_size=ICON_SIZE,
                tooltip="Toggle Diff (⌘D)",
                icon_color=TOGGLE_ACTIVE_COLOR if diff_open else None,
                on_click=on_diff,
            ),
            ft.IconButton(
                ft.Icons.LOCK if read_only else ft.Icons.LOCK_OPEN,
                icon_size=ICON_SIZE,
                icon_color=TOGGLE_ACTIVE_COLOR if read_only else None,
                tooltip="Unlock Editing (⌘L)" if read_only else "Toggle Read-Only (⌘L)",
                on_click=on_lock,
            ),
            ft.IconButton(
                ft.Icons.AUTO_FIX_HIGH if ruff_on else ft.Icons.AUTO_FIX_OFF,
                icon_size=ICON_SIZE,
                icon_color=TOGGLE_ACTIVE_COLOR if ruff_on else None,
                tooltip="Ruff on Save: ON" if ruff_on else "Ruff on Save: OFF",
                on_click=on_ruff,
            ),
            ft.IconButton(
                ft.Icons.FORMAT_LIST_NUMBERED_RTL,
                icon_size=ICON_SIZE,
                icon_color=TOGGLE_ACTIVE_COLOR if gutter_on else None,
                tooltip="Hide Gutter (⇧⌘G)" if gutter_on else "Show Gutter (⇧⌘G)",
                on_click=on_gutter,
            ),
            ft.Container(expand=True),  # spacer to push right-side controls
            ft.TextButton(
                _language_display_name(lang),
                style=ft.ButtonStyle(text_style=ft.TextStyle(size=11)),
                tooltip="Change Language (⇧⌘L)",
                on_click=on_lang,
            ),
            ft.IconButton(
                ft.Icons.PALETTE,
                icon_size=ICON_SIZE,
                tooltip="Choose Editor Theme",
                on_click=on_theme,
            ),
            ft.IconButton(
                ft.Icons.HELP_OUTLINE,
                icon_size=ICON_SIZE,
                tooltip="Help (F1)",
                on_click=on_help,
            ),
        ],
    )


def main(page: ft.Page):
    """Flet main entry point — standalone demo of the EnhancedCodeEditor."""
    page.title = "CodeEditor"
    page.window.width = 800
    page.window.height = 1200

    def _on_title_change(display, name, is_dirty):
        page.title = f"{name}{'*' if is_dirty else ''} — CodeEditor"

    handle = EditorHandle()
    initial = sys.argv[1] if len(sys.argv) > 1 else None

    page.render(
        lambda: EnhancedCodeEditor(
            expand=True,
            on_title_change=_on_title_change,
            handle=handle,
            initial_path=initial,
        )
    )

    page.run_task(page.window.center)


def run():
    """Entry point for the script console command."""
    ft.run(main)


if __name__ == "__main__":
    run()
