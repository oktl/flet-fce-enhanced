"""Reusable dialog functions for the enhanced code editor."""

from __future__ import annotations

import asyncio
from collections.abc import Callable

import flet as ft
import flet_code_editor as fce

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _build_list_tiles(
    items: dict[str, object],
    current: object,
    on_select: Callable[[object], None],
) -> list[ft.ListTile]:
    """Build ListTile controls with a check mark on the current selection."""
    tiles = []
    for display_name, value in items.items():
        is_current = value == current
        tiles.append(
            ft.ListTile(
                leading=ft.Icon(ft.Icons.CHECK, visible=is_current),
                title=ft.Text(display_name, size=14),
                on_click=lambda _e, v=value: on_select(v),
            )
        )
    return tiles


def _searchable_list_dialog(
    *,
    title: str,
    items: dict[str, object],
    current: object,
    on_select: Callable[[object], None],
    page: ft.Page,
    hint: str = "Search...",
) -> ft.AlertDialog:
    """Create and open a searchable list dialog (used by theme & language pickers)."""
    list_view = ft.ListView(
        height=300,
        controls=_build_list_tiles(items, current, on_select),
    )

    def _close(_e):
        page.pop_dialog()

    def _filter(e):
        q = (e.control.value or "").lower()
        filtered = {k: v for k, v in items.items() if q in k.lower()}
        list_view.controls = _build_list_tiles(filtered, current, on_select)
        page.update()

    dlg = ft.AlertDialog(
        title=ft.Text(title),
        content=ft.Column(
            [
                ft.TextField(
                    hint_text=hint,
                    prefix_icon=ft.Icons.SEARCH,
                    on_change=_filter,
                    autofocus=True,
                ),
                list_view,
            ],
            tight=True,
            width=350,
        ),
        actions=[ft.TextButton("Close", on_click=_close)],
        actions_alignment=ft.MainAxisAlignment.END,
        on_dismiss=_close,
    )

    page.show_dialog(dlg)
    return dlg


# ---------------------------------------------------------------------------
# Confirm-discard dialog
# ---------------------------------------------------------------------------


async def confirm_discard(page: ft.Page) -> str:
    """Show a Save / Discard / Cancel dialog.

    Returns:
        ``"save"``, ``"discard"``, or ``"cancel"``.
    """
    choice: list[str | None] = [None]

    def _on_choice(action: str):
        def handler(_e):
            choice[0] = action
            page.pop_dialog()

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
    page.show_dialog(dlg)

    while choice[0] is None:
        await asyncio.sleep(0.05)

    page.pop_dialog()
    return choice[0]


# ---------------------------------------------------------------------------
# Confirm-revert dialog
# ---------------------------------------------------------------------------


async def confirm_revert(page: ft.Page) -> bool:
    """Show a Revert / Cancel dialog.

    Returns:
        ``True`` if the user chose to revert, ``False`` if cancelled.
    """
    choice: list[bool | None] = [None]

    def _on_choice(revert: bool):
        def handler(_e):
            choice[0] = revert
            page.pop_dialog()

        return handler

    dlg = ft.AlertDialog(
        modal=True,
        title=ft.Text("Revert to Saved"),
        content=ft.Text("Discard all changes and revert to the last saved version?"),
        actions=[
            ft.TextButton("Revert", on_click=_on_choice(True)),
            ft.TextButton("Cancel", on_click=_on_choice(False)),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    page.show_dialog(dlg)

    while choice[0] is None:
        await asyncio.sleep(0.05)

    page.pop_dialog()
    return choice[0]


# ---------------------------------------------------------------------------
# Theme dialog
# ---------------------------------------------------------------------------


def show_theme_dialog(
    page: ft.Page,
    themes: dict[str, fce.CodeTheme],
    current_theme: fce.CodeTheme | None,
    on_select: Callable[[fce.CodeTheme], None],
) -> ft.AlertDialog:
    """Open a searchable theme picker dialog.

    Returns the dialog instance so the caller can close it after selection.
    """
    return _searchable_list_dialog(
        title="Choose Theme",
        items=themes,
        current=current_theme,
        on_select=on_select,
        page=page,
        hint="Search themes...",
    )


# ---------------------------------------------------------------------------
# Language dialog
# ---------------------------------------------------------------------------


COMMON_LANGUAGES: set[str] = {
    "BASH",
    "CPP",
    "CS",
    "CSS",
    "DART",
    "DOCKERFILE",
    "ELIXIR",
    "ERLANG",
    "GO",
    "GRAPHQL",
    "HASKELL",
    "JAVA",
    "JAVASCRIPT",
    "JSON",
    "KOTLIN",
    "LUA",
    "MAKEFILE",
    "MARKDOWN",
    "OBJECTIVEC",
    "PERL",
    "PHP",
    "PLAINTEXT",
    "POWERSHELL",
    "PYTHON",
    "R",
    "RUBY",
    "RUST",
    "SCALA",
    "SCSS",
    "SHELL",
    "SQL",
    "SWIFT",
    "TYPESCRIPT",
    "VUE",
    "XML",
    "YAML",
}


def show_language_dialog(
    page: ft.Page,
    current_language: fce.CodeLanguage,
    on_select: Callable[[fce.CodeLanguage], None],
) -> ft.AlertDialog:
    """Open a searchable language picker dialog with a Common/All toggle.

    Returns the dialog instance so the caller can close it after selection.
    """
    all_languages = {
        lang.name.replace("_", " ").title(): lang
        for lang in sorted(fce.CodeLanguage, key=lambda lg: lg.name)
    }
    common_languages = {
        k: v for k, v in all_languages.items() if v.name in COMMON_LANGUAGES
    }

    # Always start with Common
    active_items = [common_languages]

    list_view = ft.ListView(
        height=300,
        controls=_build_list_tiles(active_items[0], current_language, on_select),
    )

    search_field = ft.TextField(
        hint_text="Search languages...",
        prefix_icon=ft.Icons.SEARCH,
        autofocus=True,
    )

    def _refresh():
        q = (search_field.value or "").lower()
        items = active_items[0]
        filtered = {k: v for k, v in items.items() if q in k.lower()} if q else items
        list_view.controls = _build_list_tiles(filtered, current_language, on_select)
        page.update()

    search_field.on_change = lambda _e: _refresh()

    common_btn = ft.TextButton(
        "Common",
        style=ft.ButtonStyle(
            bgcolor=ft.Colors.PRIMARY,
            color=ft.Colors.ON_PRIMARY,
        ),
    )
    all_btn = ft.TextButton("All")

    def _on_toggle(show_all: bool):
        active_items[0] = all_languages if show_all else common_languages
        if show_all:
            all_btn.style = ft.ButtonStyle(
                bgcolor=ft.Colors.PRIMARY, color=ft.Colors.ON_PRIMARY
            )
            common_btn.style = ft.ButtonStyle()
        else:
            common_btn.style = ft.ButtonStyle(
                bgcolor=ft.Colors.PRIMARY, color=ft.Colors.ON_PRIMARY
            )
            all_btn.style = ft.ButtonStyle()
        _refresh()

    common_btn.on_click = lambda _e: _on_toggle(False)
    all_btn.on_click = lambda _e: _on_toggle(True)

    toggle_row = ft.Row([common_btn, all_btn], spacing=4)

    def _close(_e):
        page.pop_dialog()

    dlg = ft.AlertDialog(
        title=ft.Text("Choose Language"),
        content=ft.Column(
            [
                toggle_row,
                search_field,
                list_view,
            ],
            tight=True,
            width=350,
        ),
        actions=[ft.TextButton("Close", on_click=_close)],
        actions_alignment=ft.MainAxisAlignment.END,
        on_dismiss=_close,
    )

    page.show_dialog(dlg)
    return dlg


# ---------------------------------------------------------------------------
# Go-to-line dialog
# ---------------------------------------------------------------------------

_GOTO_BUTTON_STYLE = ft.ButtonStyle(text_style=ft.TextStyle(size=12))


async def goto_line_dialog(page: ft.Page, max_lines: int) -> int | None:
    """Prompt the user for a line number.

    Returns:
        The 1-based line number, or ``None`` if cancelled.
    """
    result: list[int | None] = [None]
    cancelled: list[bool] = [False]

    line_field = ft.TextField(
        label=f"Line number (1\u2013{max_lines})",
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
            page.pop_dialog()

    def _cancel(_e):
        cancelled[0] = True
        page.pop_dialog()

    dlg = ft.AlertDialog(
        modal=True,
        title=ft.Text("Go to Line", size=14),
        content=ft.Column([line_field], tight=True, width=200),
        actions=[
            ft.TextButton("Cancel", on_click=_cancel, style=_GOTO_BUTTON_STYLE),
            ft.TextButton("Go", on_click=_go, style=_GOTO_BUTTON_STYLE),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
        content_padding=ft.Padding.symmetric(horizontal=20, vertical=8),
        actions_padding=ft.Padding.only(right=12, bottom=8),
    )
    page.show_dialog(dlg)

    while result[0] is None and not cancelled[0]:
        await asyncio.sleep(0.05)

    page.pop_dialog()
    return result[0]


# ---------------------------------------------------------------------------
# Command palette
# ---------------------------------------------------------------------------


async def open_command_palette(
    page: ft.Page,
    commands: list[tuple[str, str, Callable]],
) -> None:
    """Show a searchable command palette.

    Args:
        page: The Flet page.
        commands: List of ``(name, shortcut_label, handler)`` tuples.
            Handlers receive a single ``_e`` argument and may be sync or async.
    """
    chosen: list[int | None] = [None]
    cancelled: list[bool] = [False]

    def _build_tiles(cmds):
        tiles = []
        for i, (name, shortcut, _handler) in enumerate(cmds):
            tiles.append(
                ft.ListTile(
                    title=ft.Text(name, size=14),
                    trailing=(
                        ft.Text(shortcut, size=12, color=ft.Colors.GREY_500)
                        if shortcut
                        else None
                    ),
                    on_click=lambda _e, idx=i: _select(idx),
                )
            )
        return tiles

    def _select(idx):
        chosen[0] = idx
        page.pop_dialog()

    def _dismiss(_e):
        cancelled[0] = True
        page.pop_dialog()

    cmd_list = ft.ListView(
        height=300,
        controls=_build_tiles(commands),
    )

    def _filter(e):
        q = (e.control.value or "").lower()
        filtered = [
            (i, commands[i])
            for i in range(len(commands))
            if q in commands[i][0].lower()
        ]
        cmd_list.controls = [
            ft.ListTile(
                title=ft.Text(cmd[0], size=14),
                trailing=(
                    ft.Text(cmd[1], size=12, color=ft.Colors.GREY_500)
                    if cmd[1]
                    else None
                ),
                on_click=lambda _e, idx=i: _select(idx),
            )
            for i, cmd in filtered
        ]
        page.update()

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

    page.show_dialog(dlg)

    while chosen[0] is None and not cancelled[0]:
        await asyncio.sleep(0.05)

    page.pop_dialog()

    if chosen[0] is not None:
        handler = commands[chosen[0]][2]
        result = handler(None)
        if asyncio.iscoroutine(result):
            await result


# ---------------------------------------------------------------------------
# Help dialog
# ---------------------------------------------------------------------------


def show_help_dialog(page: ft.Page, content: str) -> None:
    """Show a scrollable markdown help dialog."""

    def _close(_e):
        page.pop_dialog()

    def _on_link(e):
        page.run_task(page.launch_url, e.data)

    dlg = ft.AlertDialog(
        title=ft.Text("Help"),
        content=ft.Column(
            [
                ft.Markdown(
                    content,
                    extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                    selectable=True,
                    on_tap_link=_on_link,
                ),
            ],
            scroll=ft.ScrollMode.AUTO,
            width=500,
            height=450,
        ),
        actions=[ft.TextButton("Close", on_click=_close)],
        actions_alignment=ft.MainAxisAlignment.END,
        on_dismiss=_close,
    )

    page.show_dialog(dlg)
