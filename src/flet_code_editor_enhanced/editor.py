"""Enhanced CodeEditor with file open/save/save-as/close capabilities.

Based on samples/code_editor_selection_handling.py with added file I/O toolbar.
"""

import asyncio
from pathlib import Path

import flet_code_editor as fce

import flet as ft

from flet_code_editor_enhanced.file_dialog import open_file, save_file

# Map file extensions to CodeLanguage enum values.
EXTENSION_TO_LANGUAGE: dict[str, fce.CodeLanguage] = {
    ".py": fce.CodeLanguage.PYTHON,
    ".js": fce.CodeLanguage.JAVASCRIPT,
    ".jsx": fce.CodeLanguage.JAVASCRIPT,
    ".ts": fce.CodeLanguage.TYPESCRIPT,
    ".tsx": fce.CodeLanguage.TYPESCRIPT,
    ".html": fce.CodeLanguage.HTMLBARS,
    ".css": fce.CodeLanguage.CSS,
    ".scss": fce.CodeLanguage.SCSS,
    ".json": fce.CodeLanguage.JSON,
    ".xml": fce.CodeLanguage.XML,
    ".yaml": fce.CodeLanguage.YAML,
    ".yml": fce.CodeLanguage.YAML,
    ".toml": fce.CodeLanguage.INI,
    ".md": fce.CodeLanguage.MARKDOWN,
    ".txt": fce.CodeLanguage.PLAINTEXT,
    ".sh": fce.CodeLanguage.BASH,
    ".bash": fce.CodeLanguage.BASH,
    ".zsh": fce.CodeLanguage.BASH,
    ".rs": fce.CodeLanguage.RUST,
    ".go": fce.CodeLanguage.GO,
    ".java": fce.CodeLanguage.JAVA,
    ".kt": fce.CodeLanguage.KOTLIN,
    ".c": fce.CodeLanguage.CPP,
    ".cpp": fce.CodeLanguage.CPP,
    ".h": fce.CodeLanguage.CPP,
    ".hpp": fce.CodeLanguage.CPP,
    ".cs": fce.CodeLanguage.CS,
    ".rb": fce.CodeLanguage.RUBY,
    ".php": fce.CodeLanguage.PHP,
    ".sql": fce.CodeLanguage.SQL,
    ".r": fce.CodeLanguage.R,
    ".swift": fce.CodeLanguage.SWIFT,
    ".dart": fce.CodeLanguage.DART,
    ".lua": fce.CodeLanguage.LUA,
    ".vim": fce.CodeLanguage.VIM,
    ".ini": fce.CodeLanguage.INI,
    ".cfg": fce.CodeLanguage.INI,
    ".makefile": fce.CodeLanguage.MAKEFILE,
    ".dockerfile": fce.CodeLanguage.DOCKERFILE,
    ".scala": fce.CodeLanguage.SCALA,
    ".ex": fce.CodeLanguage.ELIXIR,
    ".exs": fce.CodeLanguage.ELIXIR,
    ".erl": fce.CodeLanguage.ERLANG,
    ".hs": fce.CodeLanguage.HASKELL,
    ".clj": fce.CodeLanguage.CLOJURE,
    ".gradle": fce.CodeLanguage.GRADLE,
    ".graphql": fce.CodeLanguage.GRAPHQL,
    ".vue": fce.CodeLanguage.VUE,
}


def language_for_path(path: str | None) -> fce.CodeLanguage:
    """Detect CodeLanguage from a file path's extension.

    Args:
        path: File path string, or None for untitled files.

    Returns:
        Matching CodeLanguage, or PLAINTEXT if unrecognised.
    """
    if path is None:
        return fce.CodeLanguage.PLAINTEXT
    ext = Path(path).suffix.lower()
    return EXTENSION_TO_LANGUAGE.get(ext, fce.CodeLanguage.PLAINTEXT)


DEFAULT_CODE = """\
# New file
"""


def main(page: ft.Page):
    page.title = "CodeEditor — File I/O"
    max_selection_preview = 80

    # --- State ---
    current_path: list[str | None] = [None]  # mutable container for closure
    dirty: list[bool] = [False]
    last_saved_content: list[str] = [DEFAULT_CODE]

    # --- Theme (preserved from original sample) ---
    theme = fce.CustomCodeTheme(
        keyword=ft.TextStyle(color=ft.Colors.INDIGO_600, weight=ft.FontWeight.W_600),
        string=ft.TextStyle(color=ft.Colors.RED_700),
        comment=ft.TextStyle(color=ft.Colors.GREY_600, italic=True),
    )

    text_style = ft.TextStyle(font_family="monospace", height=1.2, size=13)

    gutter_style = fce.GutterStyle(
        text_style=ft.TextStyle(font_family="monospace", height=1.2),
        show_line_numbers=True,
        show_folding_handles=True,
        width=80,
    )

    # --- UI refs ---
    title_bar = ft.Text("untitled", size=16, weight=ft.FontWeight.BOLD, expand=True)

    def _update_title():
        if current_path[0]:
            try:
                display = "~/" + str(Path(current_path[0]).relative_to(Path.home()))
            except ValueError:
                display = current_path[0]
        else:
            display = "untitled"
        title_bar.value = display
        title_bar.color = ft.Colors.AMBER_600 if dirty[0] else None
        page.update()

    def _mark_dirty():
        if not dirty[0]:
            dirty[0] = True
            _update_title()

    def _mark_clean(content: str):
        dirty[0] = False
        last_saved_content[0] = content
        _update_title()

    # --- Unsaved-changes confirmation dialog ---
    async def _confirm_discard() -> str:
        """Show a Save/Discard/Cancel dialog. Returns chosen action string."""
        choice_event = asyncio.Event()
        choice: list[str] = ["cancel"]

        def _on_choice(action: str):
            def handler(_e):
                choice[0] = action
                dlg.open = False
                page.update()
                choice_event.set()

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
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

        await choice_event.wait()
        page.overlay.remove(dlg)
        page.update()
        return choice[0]

    # --- Toolbar actions ---
    async def _handle_open(_e):
        if dirty[0]:
            action = await _confirm_discard()
            if action == "save":
                await _do_save()
                if dirty[0]:  # save was cancelled
                    return
            elif action == "cancel":
                return

        path = await open_file("Open File")
        if path is None:
            return

        content = Path(path).read_text(encoding="utf-8")
        editor.value = content
        current_path[0] = path
        editor.language = language_for_path(path)
        _mark_clean(content)
        await editor.focus()

    async def _do_save() -> bool:
        """Save to current_path. Returns True if saved, False if cancelled."""
        if current_path[0] is None:
            return await _do_save_as()

        content = editor.value or ""
        Path(current_path[0]).write_text(content, encoding="utf-8")
        _mark_clean(content)
        return True

    async def _do_save_as() -> bool:
        """Save As dialog. Returns True if saved, False if cancelled."""
        default = Path(current_path[0]).name if current_path[0] else "untitled.txt"
        path = await save_file("Save File", default)
        if path is None:
            return False

        current_path[0] = path
        content = editor.value or ""
        Path(path).write_text(content, encoding="utf-8")
        editor.language = language_for_path(path)
        _mark_clean(content)
        return True

    async def _handle_save(_e):
        await _do_save()

    async def _handle_save_as(_e):
        await _do_save_as()

    async def _handle_close(_e):
        if dirty[0]:
            action = await _confirm_discard()
            if action == "save":
                saved = await _do_save()
                if not saved:
                    return
            elif action == "cancel":
                return

        editor.value = DEFAULT_CODE
        editor.language = fce.CodeLanguage.PYTHON
        current_path[0] = None
        _mark_clean(DEFAULT_CODE)
        await editor.focus()

    # --- Selection handling (preserved from original sample) ---
    def handle_selection_change(e: ft.TextSelectionChangeEvent[fce.CodeEditor]):
        if e.selected_text:
            normalized = " ".join(e.selected_text.split())
            suffix = "..." if len(normalized) > max_selection_preview else ""
            preview = normalized[:max_selection_preview]
            selection.value = (
                f"Selection ({len(e.selected_text)} chars): '{preview}{suffix}'"
            )
        else:
            selection.value = "No selection."
        selection_details.value = f"start={e.selection.start}, end={e.selection.end}"
        caret.value = f"Caret position: {e.selection.end}"

    def handle_change(_e):
        content = editor.value or ""
        if content != last_saved_content[0]:
            _mark_dirty()
        elif dirty[0]:
            dirty[0] = False
            _update_title()

    async def select_all(_e):
        await editor.focus()
        editor.selection = ft.TextSelection(
            base_offset=0,
            extent_offset=len(editor.value or ""),
        )

    async def move_caret_to_start(_e):
        await editor.focus()
        editor.selection = ft.TextSelection(base_offset=0, extent_offset=0)

    # --- Layout ---
    page.add(
        ft.Column(
            expand=True,
            spacing=10,
            controls=[
                # Title bar
                ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=[title_bar],
                ),
                # Toolbar
                ft.Row(
                    spacing=10,
                    controls=[
                        ft.Button(
                            "Open",
                            icon=ft.Icons.FOLDER_OPEN,
                            on_click=_handle_open,
                        ),
                        ft.Button(
                            "Save",
                            icon=ft.Icons.SAVE,
                            on_click=_handle_save,
                        ),
                        ft.Button(
                            "Save As",
                            icon=ft.Icons.SAVE_AS,
                            on_click=_handle_save_as,
                        ),
                        ft.Button(
                            "Close",
                            icon=ft.Icons.CLOSE,
                            on_click=_handle_close,
                        ),
                    ],
                ),
                # Editor
                editor := fce.CodeEditor(
                    language=fce.CodeLanguage.PYTHON,
                    code_theme=theme,
                    # code_theme=fce.CodeTheme.DARK,  # Uncomment to test custom theme vs built-in
                    autocomplete=True,
                    autocomplete_words=[
                        "Container",
                        "Button",
                        "Text",
                        "Row",
                        "Column",
                    ],
                    value=DEFAULT_CODE,
                    text_style=text_style,
                    gutter_style=gutter_style,
                    on_selection_change=handle_selection_change,
                    on_change=handle_change,
                    expand=True,
                ),
                # Selection info (preserved from original)
                selection := ft.Text("Select some text from the editor."),
                selection_details := ft.Text(),
                caret := ft.Text("Caret position: -"),
                ft.Row(
                    spacing=10,
                    controls=[
                        ft.Button("Select all text", on_click=select_all),
                        ft.Button("Move caret to start", on_click=move_caret_to_start),
                    ],
                ),
            ],
        )
    )


def run():
    """Entry point for the script console command."""
    ft.run(main)


if __name__ == "__main__":
    run()
