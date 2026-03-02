"""Enhanced CodeEditor with file open/save/save-as/close capabilities.

Based on CodeEditor control from Flet docs
https://docs.flet.dev/codeeditor/ with added file I/O toolbar.
"""

import asyncio
import platform
import shutil
from pathlib import Path

import flet as ft
import flet_code_editor as fce
from loguru import logger

from fce_enhanced.file_dialog import open_file, save_file
from fce_enhanced.languages import language_for_path
from fce_enhanced.search import SearchReplaceBar
from fce_enhanced.themes import DEFAULT_THEME, THEMES

DEFAULT_CODE = """\
# New file
"""

BUTTON_STYLE = ft.ButtonStyle(text_style=ft.TextStyle(size=12))
APPBAR_HEIGHT = 18
ICON_SIZE = 16
DEFAULT_FONT_SIZE = 13
MIN_FONT_SIZE = 8
MAX_FONT_SIZE = 32


class EnhancedCodeEditor(ft.Column):
    """A reusable Flet control that wraps CodeEditor with file I/O toolbar.

    Provides Open, Save, Save As, and Close buttons plus keyboard shortcuts
    (Cmd/Ctrl+O, S, Shift+S, W). Can be dropped into any Flet page layout.

    Args:
        language: Initial code language for syntax highlighting.
        value: Initial editor content.
        show_toolbar: Whether to show the file I/O toolbar.
        show_status_bar: Whether to show the line/column status bar.
        register_keyboard_shortcuts: Whether to register global keyboard shortcuts.
        autocomplete: Whether to enable autocomplete.
        autocomplete_words: List of words for autocomplete suggestions.
        code_theme: Custom code theme for syntax highlighting.
        text_style: Text style for the editor content.
        gutter_style: Style for the line number gutter.
        on_title_change: Callback fired with (display_path, name, is_dirty) when
            the file title or dirty state changes.
        ruff_on_save: Run ruff check --fix and ruff format on Python files
            after saving. Requires ruff to be installed. Defaults to True.
    """

    def __init__(
        self,
        language: fce.CodeLanguage = fce.CodeLanguage.PYTHON,
        value: str = DEFAULT_CODE,
        show_toolbar: bool = True,
        show_status_bar: bool = True,
        register_keyboard_shortcuts: bool = True,
        autocomplete: bool = True,
        autocomplete_words: list[str] | None = None,
        code_theme: fce.CustomCodeTheme | None = None,
        text_style: ft.TextStyle | None = None,
        gutter_style: fce.GutterStyle | None = None,
        on_title_change=None,
        ruff_on_save: bool = True,
        **kwargs,
    ):
        super().__init__(**kwargs)

        # --- Configuration ---
        self._register_keyboard_shortcuts = register_keyboard_shortcuts
        self.on_title_change = on_title_change
        self._ruff_on_save = ruff_on_save

        # --- State ---
        self._current_path: str | None = None
        self._dirty: bool = False
        self._last_saved_content: str = value

        # --- Defaults ---
        if code_theme is None:
            code_theme = DEFAULT_THEME
        self._current_theme: fce.CodeTheme | None = (
            code_theme if isinstance(code_theme, fce.CodeTheme) else None
        )

        self._font_size = text_style.size if text_style else DEFAULT_FONT_SIZE

        if text_style is None:
            text_style = ft.TextStyle(
                font_family="monospace", height=1.2, size=self._font_size
            )

        if gutter_style is None:
            gutter_style = fce.GutterStyle(
                text_style=ft.TextStyle(font_family="monospace", height=1.2),
                show_line_numbers=True,
                show_folding_handles=True,
                width=80,
            )

        # --- UI elements ---
        self._title_bar = ft.Text("untitled", size=12, color=ft.Colors.GREY_600)
        self._status_bar = ft.Text(
            "Ln 1, Col 1 | Python", size=12, color=ft.Colors.GREY_600
        )

        self._save_btn = ft.IconButton(
            ft.Icons.SAVE,
            icon_size=ICON_SIZE,
            tooltip="Save (⌘S)",
            on_click=self._handle_save,
            disabled=True,
        )
        self._lock_btn = ft.IconButton(
            ft.Icons.LOCK_OPEN,
            icon_size=ICON_SIZE,
            tooltip="Toggle Read-Only (⌘L)",
            on_click=lambda _e: self._toggle_read_only(),
        )
        self._font_size_label = ft.Text(
            f"{self._font_size}px", size=11, color=ft.Colors.GREY_600
        )

        self._code_editor = fce.CodeEditor(
            language=language,
            code_theme=code_theme,
            autocomplete=autocomplete,
            autocomplete_words=autocomplete_words or [],
            value=value,
            text_style=text_style,
            gutter_style=gutter_style,
            on_selection_change=self._handle_selection_change,
            on_change=self._handle_change,
            expand=True,
        )

        # --- Search bar ---
        self._search_bar = SearchReplaceBar(
            get_text=lambda: self._code_editor.value or "",
            set_selection=self._set_editor_selection,
            replace_text=self._apply_replace_text,
            focus_editor=self._focus_editor,
            on_close=self._on_search_closed,
        )

        # --- Build layout ---
        controls = []

        appbar = ft.Row(
            controls=[
                # Each button here is a direct command
                ft.IconButton(
                    ft.Icons.FILE_OPEN,
                    icon_size=ICON_SIZE,
                    tooltip="Open (⌘O)",
                    on_click=self._handle_open,
                ),
                self._save_btn,
                ft.IconButton(
                    ft.Icons.SAVE_AS,
                    icon_size=ICON_SIZE,
                    tooltip="Save As (⇧⌘S)",
                    on_click=self._handle_save_as,
                ),
                ft.IconButton(
                    ft.Icons.CLOSE,
                    icon_size=ICON_SIZE,
                    tooltip="Close File (⌘W) ",
                    on_click=self._handle_close,
                ),
                ft.IconButton(
                    ft.Icons.PALETTE,
                    icon_size=ICON_SIZE,
                    tooltip="Choose Theme",
                    on_click=self._handle_theme_click,
                ),
                ft.IconButton(
                    ft.Icons.SEARCH,
                    icon_size=ICON_SIZE,
                    tooltip="Find (⌘F)",
                    on_click=self._handle_find_click,
                ),
                ft.IconButton(
                    ft.Icons.FORMAT_LIST_NUMBERED,
                    icon_size=ICON_SIZE,
                    tooltip="Go to Line (⌘G)",
                    on_click=self._handle_goto_line,
                ),
                self._lock_btn,
                ft.VerticalDivider(width=1),
                ft.IconButton(
                    ft.Icons.REMOVE,
                    icon_size=ICON_SIZE,
                    tooltip="Decrease Font Size (⌘-)",
                    on_click=lambda _e: self._change_font_size(-1),
                ),
                self._font_size_label,
                ft.IconButton(
                    ft.Icons.ADD,
                    icon_size=ICON_SIZE,
                    tooltip="Increase Font Size (⌘+)",
                    on_click=lambda _e: self._change_font_size(1),
                ),
            ],
        )

        controls.append(appbar)
        controls.append(self._search_bar)
        controls.append(ft.Divider(height=1, color=ft.Colors.GREY_800))
        controls.append(
            ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                controls=[
                    ft.Text("File: ", size=12, color=ft.Colors.GREY_600),
                    self._title_bar,
                ],
            )
        )
        controls.append(self._code_editor)

        if show_status_bar:
            controls.append(ft.Row(controls=[self._status_bar]))

        self.spacing = 10
        self.controls = controls

    # --- Properties ---

    @property
    def current_path(self) -> str | None:
        """The path of the currently open file, or None for untitled."""
        return self._current_path

    @property
    def dirty(self) -> bool:
        """Whether the editor has unsaved changes."""
        return self._dirty

    @property
    def code_editor(self) -> fce.CodeEditor:
        """The underlying CodeEditor control."""
        return self._code_editor

    @property
    def value(self) -> str:
        """The current editor content."""
        return self._code_editor.value or ""

    @value.setter
    def value(self, content: str):
        self._code_editor.value = content

    @property
    def language(self) -> fce.CodeLanguage:
        """The current syntax highlighting language."""
        return self._code_editor.language

    @language.setter
    def language(self, lang: fce.CodeLanguage):
        self._code_editor.language = lang

    # --- Lifecycle ---

    def did_mount(self):
        if self._register_keyboard_shortcuts and self.page:
            self.page.on_keyboard_event = self._handle_keyboard

    def will_unmount(self):
        if self._register_keyboard_shortcuts and self.page:
            self.page.on_keyboard_event = None

    # --- Title / dirty state ---

    def _update_title(self):
        if self._current_path:
            try:
                display = "~/" + str(Path(self._current_path).relative_to(Path.home()))
            except ValueError:
                display = self._current_path
            name = Path(self._current_path).name
        else:
            display = "untitled"
            name = "untitled"

        self._title_bar.value = display
        self._title_bar.color = ft.Colors.AMBER_600 if self._dirty else None

        if self.on_title_change:
            self.on_title_change(display, name, self._dirty)

        self.update()

    def _mark_dirty(self):
        if not self._dirty:
            self._dirty = True
            self._save_btn.disabled = False
            self._update_title()

    def _mark_clean(self, content: str):
        self._dirty = False
        self._last_saved_content = content
        self._save_btn.disabled = True
        self._update_title()

    # --- Unsaved-changes confirmation dialog ---

    async def _confirm_discard(self) -> str:
        """Show a Save/Discard/Cancel dialog. Returns chosen action string."""
        choice: list[str | None] = [None]

        def _on_choice(action: str):
            def handler(_e):
                choice[0] = action
                dlg.open = False
                self.page.update()

            return handler

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Unsaved Changes"),
            content=ft.Text("You have unsaved changes. What would you like to do?"),
            actions=[
                ft.TextButton("Save", on_click=_on_choice("save")),
                ft.TextButton("Discard", on_click=_on_choice("discard")),
                ft.TextButton("Cancel", on_click=_on_choice("cancel")),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()

        while choice[0] is None:
            await asyncio.sleep(0.05)

        self.page.overlay.remove(dlg)
        self.page.update()
        return choice[0]

    # --- File operations ---

    async def _handle_open(self, _e):
        if self._dirty:
            action = await self._confirm_discard()
            if action == "save":
                await self._do_save()
                if self._dirty:
                    return
            elif action == "cancel":
                return

        path = await open_file("Open File")
        if path is None:
            return

        try:
            content = Path(path).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError, ValueError) as exc:
            err = ft.SnackBar(ft.Text(f"Cannot open file: {exc}"))
            self.page.overlay.append(err)
            err.open = True
            self.page.update()
            return

        self._current_path = path
        self._last_saved_content = content
        self._code_editor.value = content
        self._code_editor.language = language_for_path(path)
        self._mark_clean(content)
        await self._code_editor.focus()
        await asyncio.sleep(0.05)
        self._code_editor.selection = ft.TextSelection(base_offset=0, extent_offset=0)
        try:
            self._code_editor.update()
        except RuntimeError:
            pass

    def _show_snackbar(self, message: str, *, is_error: bool = False) -> None:
        """Show a message to the user via a SnackBar with a dismiss button."""
        snack = ft.SnackBar(
            ft.Text(message, color=ft.Colors.WHITE, selectable=True),
            bgcolor=ft.Colors.RED_800 if is_error else ft.Colors.GREY_800,
            action="Dismiss",
            duration=86400000,  # effectively permanent until dismissed
        )
        self.page.overlay.append(snack)
        snack.open = True
        self.page.update()

    async def _run_ruff(self, path: str) -> None:
        """Run ruff check --fix and ruff format on a saved Python file.

        Silently skips if ruff is not installed or the file is not Python.
        Updates the editor content with the formatted result.
        Shows remaining warnings to the user via a snackbar.
        """
        if not self._ruff_on_save:
            return
        if not path.endswith(".py"):
            return
        ruff = shutil.which("ruff")
        if ruff is None:
            logger.debug("ruff not found on PATH, skipping post-save formatting")
            return

        # ruff check --fix applies auto-fixes but exits non-zero if
        # unfixable violations remain — that's normal, so don't bail out.
        check_proc = await asyncio.create_subprocess_exec(
            ruff,
            "check",
            "--fix",
            path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        check_stdout, _ = await check_proc.communicate()

        # Show remaining lint warnings to the user
        check_output = check_stdout.decode().strip()
        if check_proc.returncode != 0 and check_output:
            # Strip the "Found N errors" summary, keep the actual violations
            lines = [
                ln for ln in check_output.splitlines() if not ln.startswith("Found ")
            ]
            if lines:
                self._show_snackbar(f"Ruff: {'; '.join(lines)}", is_error=True)

        # Run formatter
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
            self._show_snackbar(f"Ruff format failed: {msg}", is_error=True)
            return

        # Reload formatted content into editor
        try:
            formatted = Path(path).read_text(encoding="utf-8")
        except OSError as exc:
            logger.warning("Failed to reload after ruff: {}", exc)
            return
        if formatted != self._code_editor.value:
            self._code_editor.value = formatted
            self._last_saved_content = formatted
            self.update()

    async def _do_save(self) -> bool:
        """Save to current_path. Returns True if saved, False if cancelled."""
        if self._current_path is None:
            return await self._do_save_as()

        content = self._code_editor.value or ""
        try:
            Path(self._current_path).write_text(content, encoding="utf-8")
        except OSError as exc:
            logger.error("Failed to save {}: {}", self._current_path, exc)
            self._show_snackbar(f"Save failed: {exc}", is_error=True)
            return False
        self._mark_clean(content)
        await self._run_ruff(self._current_path)
        return True

    async def _do_save_as(self) -> bool:
        """Save As dialog. Returns True if saved, False if cancelled."""
        default = (
            Path(self._current_path).name if self._current_path else "untitled.txt"
        )
        path = await save_file("Save File", default)
        if path is None:
            return False

        content = self._code_editor.value or ""
        try:
            Path(path).write_text(content, encoding="utf-8")
        except OSError as exc:
            logger.error("Failed to save {}: {}", path, exc)
            self._show_snackbar(f"Save failed: {exc}", is_error=True)
            return False
        self._current_path = path
        self._code_editor.language = language_for_path(path)
        self._mark_clean(content)
        await self._run_ruff(path)
        return True

    async def _handle_save(self, _e):
        await self._do_save()

    async def _handle_save_as(self, _e):
        await self._do_save_as()

    async def _handle_close(self, _e):
        if self._dirty:
            action = await self._confirm_discard()
            if action == "save":
                saved = await self._do_save()
                if not saved:
                    return
            elif action == "cancel":
                return

        self._current_path = None
        self._dirty = False
        self._last_saved_content = DEFAULT_CODE
        self._save_btn.disabled = True
        self._code_editor.language = fce.CodeLanguage.PYTHON
        self._update_title()
        await asyncio.sleep(0.05)
        self._code_editor.value = DEFAULT_CODE
        self.update()
        await self._code_editor.focus()

    # --- Theme selection ---

    def _handle_theme_click(self, _e):
        self._show_theme_dialog()

    def _show_theme_dialog(self):
        theme_list = ft.ListView(
            height=300,
            controls=self._build_theme_tiles(THEMES),
        )

        def close(_e):
            self._theme_dlg.open = False
            self.page.update()

        self._theme_dlg = ft.AlertDialog(
            title=ft.Text("Choose Theme"),
            content=ft.Column(
                [
                    ft.TextField(
                        hint_text="Search themes...",
                        prefix_icon=ft.Icons.SEARCH,
                        on_change=lambda e: self._filter_theme_list(
                            e.control.value, theme_list
                        ),
                        autofocus=True,
                    ),
                    theme_list,
                ],
                tight=True,
                width=350,
            ),
            actions=[ft.TextButton("Close", on_click=close)],
            actions_alignment=ft.MainAxisAlignment.END,
            on_dismiss=close,
        )

        self.page.overlay.append(self._theme_dlg)
        self._theme_dlg.open = True
        self.page.update()

    def _build_theme_tiles(self, themes: dict[str, fce.CodeTheme]) -> list[ft.ListTile]:
        tiles = []
        for display_name, theme_val in themes.items():
            is_current = theme_val == self._current_theme
            tiles.append(
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.CHECK, visible=is_current),
                    title=ft.Text(display_name, size=14),
                    on_click=lambda _e, t=theme_val: self._select_theme(t),
                )
            )
        return tiles

    def _filter_theme_list(self, query: str, theme_list: ft.ListView):
        q = (query or "").lower()
        filtered = {k: v for k, v in THEMES.items() if q in k.lower()}
        theme_list.controls = self._build_theme_tiles(filtered)
        self.page.update()

    def _select_theme(self, theme: fce.CodeTheme):
        self._current_theme = theme
        self._code_editor.code_theme = theme
        if hasattr(self, "_theme_dlg") and self._theme_dlg is not None:
            self._theme_dlg.open = False
        self.page.update()
        self.update()

    # --- Command palette ---

    async def _open_command_palette(self):
        """Show a searchable command palette dialog (Cmd+Shift+P / Ctrl+Shift+P)."""
        is_mac = platform.system() == "Darwin"
        mod = "⌘" if is_mac else "Ctrl+"
        shift_mod = "⇧⌘" if is_mac else "Ctrl+Shift+"
        commands = [
            ("Open File", f"{mod}O", self._handle_open),
            ("Save", f"{mod}S", self._handle_save),
            ("Save As", f"{shift_mod}S", self._handle_save_as),
            ("Close File", f"{mod}W", self._handle_close),
            ("Find", f"{mod}F", lambda _: self._open_search(with_replace=False)),
            (
                "Find and Replace",
                f"{mod}H",
                lambda _: self._open_search(with_replace=True),
            ),
            ("Go to Line", f"{mod}G", self._handle_goto_line),
            ("Choose Theme", "", self._handle_theme_click),
            ("Toggle Read-Only", f"{mod}L", lambda _: self._toggle_read_only()),
            ("Increase Font Size", f"{mod}+", lambda _: self._change_font_size(1)),
            ("Decrease Font Size", f"{mod}-", lambda _: self._change_font_size(-1)),
        ]

        chosen: list[int | None] = [None]
        cancelled: list[bool] = [False]

        def _build_tiles(cmds):
            tiles = []
            for i, (name, shortcut, _handler) in enumerate(cmds):
                tiles.append(
                    ft.ListTile(
                        title=ft.Text(name, size=14),
                        trailing=ft.Text(shortcut, size=12, color=ft.Colors.GREY_500)
                        if shortcut
                        else None,
                        on_click=lambda _e, idx=i: _select(idx),
                    )
                )
            return tiles

        def _select(idx):
            chosen[0] = idx
            dlg.open = False
            self.page.update()

        def _dismiss(_e):
            cancelled[0] = True
            dlg.open = False
            self.page.update()

        # Filtered command list (indices into `commands`)
        filtered: list[int] = list(range(len(commands)))

        cmd_list = ft.ListView(
            height=300,
            controls=_build_tiles(commands),
        )

        def _filter(e):
            q = (e.control.value or "").lower()
            filtered.clear()
            filtered.extend(
                i for i, (name, _s, _h) in enumerate(commands) if q in name.lower()
            )
            cmd_list.controls = [
                ft.ListTile(
                    title=ft.Text(commands[i][0], size=14),
                    trailing=ft.Text(commands[i][1], size=12, color=ft.Colors.GREY_500)
                    if commands[i][1]
                    else None,
                    on_click=lambda _e, idx=i: _select(idx),
                )
                for i in filtered
            ]
            self.page.update()

        dlg = ft.AlertDialog(
            title=ft.Text("Command Palette", size=14),
            content=ft.Column(
                [
                    ft.TextField(
                        hint_text="Type a command...",
                        prefix_icon=ft.Icons.SEARCH,
                        autofocus=True,
                        on_change=_filter,
                    ),
                    cmd_list,
                ],
                tight=True,
                width=350,
            ),
            on_dismiss=_dismiss,
        )

        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()

        while chosen[0] is None and not cancelled[0]:
            await asyncio.sleep(0.05)

        self.page.overlay.remove(dlg)
        self.page.update()

        if chosen[0] is not None:
            handler = commands[chosen[0]][2]
            result = handler(None)
            if asyncio.iscoroutine(result):
                await result

    # --- Read-only toggle ---

    def _toggle_read_only(self) -> None:
        read_only = not self._code_editor.read_only
        self._code_editor.read_only = read_only
        self._lock_btn.icon = ft.Icons.LOCK if read_only else ft.Icons.LOCK_OPEN
        self._lock_btn.tooltip = (
            "Unlock Editing (⌘L)" if read_only else "Toggle Read-Only (⌘L)"
        )
        self.update()

    # --- Font size ---

    def _change_font_size(self, delta: int) -> None:
        new_size = max(MIN_FONT_SIZE, min(MAX_FONT_SIZE, self._font_size + delta))
        if new_size == self._font_size:
            return
        self._font_size = new_size
        self._code_editor.text_style = ft.TextStyle(
            font_family="monospace", height=1.2, size=new_size
        )
        self._font_size_label.value = f"{new_size}px"
        self.update()

    # --- Search / Replace ---

    @property
    def search_bar(self) -> SearchReplaceBar:
        """The search/replace bar control."""
        return self._search_bar

    def _set_editor_selection(self, base: int, extent: int) -> None:
        self._code_editor.selection = ft.TextSelection(
            base_offset=base, extent_offset=extent
        )
        try:
            self._code_editor.update()
        except RuntimeError:
            pass

    def _focus_editor(self) -> None:
        try:
            asyncio.ensure_future(self._code_editor.focus())
        except RuntimeError:
            pass

    def _apply_replace_text(self, new_text: str) -> None:
        self._code_editor.value = new_text

    async def _handle_find_click(self, _e) -> None:
        await self._open_search(with_replace=False)

    async def _open_search(self, *, with_replace: bool = False) -> None:
        self._search_bar.open(with_replace=with_replace)
        self.page.update()
        await self._search_bar.focus_search()

    def _close_search(self) -> None:
        self._search_bar.close()
        self.page.update()

    def _on_search_closed(self) -> None:
        """Called by SearchReplaceBar.close() — just update layout, don't call close again."""
        self.page.update()

    # --- Go to Line ---

    async def _handle_goto_line(self, _e):
        """Show a dialog prompting for a line number, then jump to that line."""
        result: list[int | None] = [None]
        cancelled: list[bool] = [False]
        content = self._code_editor.value or ""
        max_lines = content.count("\n") + 1

        line_field = ft.TextField(
            label=f"Line number (1–{max_lines})",
            keyboard_type=ft.KeyboardType.NUMBER,
            autofocus=True,
            text_size=13,
            label_style=ft.TextStyle(size=12),
            dense=True,
            content_padding=ft.Padding.symmetric(horizontal=8, vertical=4),
        )

        def _go(_e):
            try:
                val = int(line_field.value)
            except (TypeError, ValueError):
                return
            if 1 <= val <= max_lines:
                result[0] = val
                dlg.open = False
                self.page.update()

        def _cancel(_e):
            cancelled[0] = True
            dlg.open = False
            self.page.update()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Go to Line", size=14),
            content=ft.Column([line_field], tight=True, width=200),
            actions=[
                ft.TextButton("Cancel", on_click=_cancel, style=BUTTON_STYLE),
                ft.TextButton("Go", on_click=_go, style=BUTTON_STYLE),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            content_padding=ft.Padding.symmetric(horizontal=20, vertical=8),
            actions_padding=ft.Padding.only(right=12, bottom=8),
        )
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()

        while result[0] is None and not cancelled[0]:
            await asyncio.sleep(0.05)

        self.page.overlay.remove(dlg)
        self.page.update()

        if result[0] is not None:
            offset = self._line_to_offset(content, result[0])
            self._code_editor.selection = ft.TextSelection(
                base_offset=offset, extent_offset=offset
            )
            try:
                self._code_editor.update()
            except RuntimeError:
                pass
            await self._code_editor.focus()

    # --- Keyboard shortcuts ---

    async def _handle_keyboard(self, e: ft.KeyboardEvent):
        if e.key == "Escape" and self._search_bar.is_open:
            self._close_search()
            return

        if not (e.meta or e.ctrl):
            return
        key = e.key.upper()
        if key == "P" and e.shift:
            await self._open_command_palette()
        elif key == "F":
            await self._open_search(with_replace=False)
        elif key == "H":
            await self._open_search(with_replace=True)
        elif key == "S" and not e.shift:
            await self._do_save()
        elif key == "S" and e.shift:
            await self._do_save_as()
        elif key == "O":
            await self._handle_open(None)
        elif key == "W":
            await self._handle_close(None)
        elif key == "L":
            self._toggle_read_only()
        elif key == "G":
            await self._handle_goto_line(None)
        elif key == "EQUAL" or key == "+" or key == "=":
            self._change_font_size(1)
        elif key == "MINUS" or key == "-":
            self._change_font_size(-1)

    # --- Status bar ---

    @staticmethod
    def _offset_to_line_col(text: str, offset: int) -> tuple[int, int]:
        before = text[: max(0, offset)]
        lines = before.split("\n")
        return len(lines), len(lines[-1]) + 1

    @staticmethod
    def _line_to_offset(text: str, line: int) -> int:
        """Return the character offset of the start of a 1-based line number."""
        lines = text.split("\n")
        return sum(len(lines[i]) + 1 for i in range(min(line - 1, len(lines))))

    def _handle_selection_change(self, e: ft.TextSelectionChangeEvent[fce.CodeEditor]):
        caret_offset = e.selection.end
        selected_text = e.selected_text or ""
        content = self._code_editor.value or ""
        line, col = self._offset_to_line_col(content, caret_offset)
        lang = (
            self._code_editor.language.name.replace("_", " ").title()
            if self._code_editor.language
            else "Plain Text"
        )
        sel_info = f" | {len(selected_text)} chars selected" if selected_text else ""
        self._status_bar.value = f"Ln {line}, Col {col} | {lang}{sel_info}"
        self.update()

    def _handle_change(self, _e):
        content = self._code_editor.value or ""
        if content != self._last_saved_content:
            self._mark_dirty()
        elif self._dirty:
            self._dirty = False
            self._save_btn.disabled = True
            self._update_title()

        if self._search_bar.is_open:
            self._search_bar.recompute()
            self._search_bar._safe_update()


def main(page: ft.Page):
    """Flet main entry point — standalone demo of the EnhancedCodeEditor."""
    page.title = "CodeEditor"

    def _on_title_change(display, name, is_dirty):
        page.title = f"{name}{'*' if is_dirty else ''} — CodeEditor"
        page.update()

    editor = EnhancedCodeEditor(
        expand=True,
        on_title_change=_on_title_change,
    )

    page.add(editor)


def run():
    """Entry point for the script console command."""
    ft.run(main)


if __name__ == "__main__":
    run()
