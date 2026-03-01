"""Enhanced CodeEditor with file open/save/save-as/close capabilities.

Based on CodeEditor control from Flet docs
https://docs.flet.dev/codeeditor/ with added file I/O toolbar.
"""

import asyncio
from pathlib import Path

import flet as ft
import flet_code_editor as fce

from fce_enhanced.file_dialog import open_file, save_file
from fce_enhanced.languages import language_for_path
from fce_enhanced.search import SearchReplaceBar

DEFAULT_CODE = """\
# New file
"""

BUTTON_STYLE = ft.ButtonStyle(text_style=ft.TextStyle(size=12))
APPBAR_HEIGHT = 18
ICON_SIZE = 16


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
        **kwargs,
    ):
        super().__init__(**kwargs)

        # --- Configuration ---
        self._register_keyboard_shortcuts = register_keyboard_shortcuts
        self.on_title_change = on_title_change

        # --- State ---
        self._current_path: str | None = None
        self._dirty: bool = False
        self._last_saved_content: str = value

        # --- Defaults ---
        if code_theme is None:
            code_theme = fce.CustomCodeTheme(
                keyword=ft.TextStyle(
                    color=ft.Colors.INDIGO_600, weight=ft.FontWeight.W_600
                ),
                string=ft.TextStyle(color=ft.Colors.RED_700),
                comment=ft.TextStyle(color=ft.Colors.GREY_600, italic=True),
            )

        if text_style is None:
            text_style = ft.TextStyle(font_family="monospace", height=1.2, size=13)

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
                    ft.Icons.SEARCH,
                    icon_size=ICON_SIZE,
                    tooltip="Find (⌘F)",
                    on_click=self._handle_find_click,
                ),
                self.search_bar,
            ],
        )

        controls.append(appbar)
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
        # controls.append(self._search_bar)
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
        if self._register_keyboard_shortcuts:
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
        except (UnicodeDecodeError, ValueError):
            err = ft.SnackBar(ft.Text("Cannot open: file is not valid UTF-8 text"))
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

    async def _do_save(self) -> bool:
        """Save to current_path. Returns True if saved, False if cancelled."""
        if self._current_path is None:
            return await self._do_save_as()

        content = self._code_editor.value or ""
        Path(self._current_path).write_text(content, encoding="utf-8")
        self._mark_clean(content)
        return True

    async def _do_save_as(self) -> bool:
        """Save As dialog. Returns True if saved, False if cancelled."""
        default = (
            Path(self._current_path).name if self._current_path else "untitled.txt"
        )
        path = await save_file("Save File", default)
        if path is None:
            return False

        self._current_path = path
        content = self._code_editor.value or ""
        Path(path).write_text(content, encoding="utf-8")
        self._code_editor.language = language_for_path(path)
        self._mark_clean(content)
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

    # --- Keyboard shortcuts ---

    async def _handle_keyboard(self, e: ft.KeyboardEvent):
        if e.key == "Escape" and self._search_bar.is_open:
            self._close_search()
            return

        if not (e.meta or e.ctrl):
            return
        key = e.key.upper()
        if key == "F":
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

    # --- Status bar ---

    @staticmethod
    def _offset_to_line_col(text: str, offset: int) -> tuple[int, int]:
        before = text[: max(0, offset)]
        lines = before.split("\n")
        return len(lines), len(lines[-1]) + 1

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
    # page.add(
    #     appbar
    #     )
    page.add(editor)


def run():
    """Entry point for the script console command."""
    ft.run(main)


if __name__ == "__main__":
    run()
