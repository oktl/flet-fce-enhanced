"""Toggleable unified diff pane for EnhancedCodeEditor (declarative)."""

from __future__ import annotations

from collections.abc import Callable
import difflib

import flet as ft
import flet_code_editor as fce

from fce_enhanced.themes import DEFAULT_THEME

ICON_SIZE = 18


@ft.component
def DiffPane(
    original_text: str,
    current_text: str,
    on_close: Callable[[], None] | None = None,
    code_theme: fce.CustomCodeTheme | None = None,
) -> ft.Control:
    """A pane showing a unified diff between saved and current content.

    Rendered only while the diff view is open (the parent controls visibility
    via conditional rendering). Uses a read-only CodeEditor with
    ``language=DIFF`` for green/red syntax coloring of additions/deletions.

    Args:
        original_text: The last-saved file content.
        current_text: The current editor content.
        on_close: Callback invoked when the close button is pressed.
        code_theme: Code theme (should match the main editor).
    """
    if code_theme is None:
        code_theme = DEFAULT_THEME

    diff_text, added, removed = compute_unified_diff(original_text, current_text)
    stats = "No changes" if added == 0 and removed == 0 else f"+{added} / -{removed}"

    header_row = ft.Row(
        spacing=8,
        controls=[
            ft.Icon(ft.Icons.DIFFERENCE, size=ICON_SIZE, color=ft.Colors.GREY_600),
            ft.Text("Diff", size=12, weight=ft.FontWeight.BOLD),
            ft.Text(stats, size=11, color=ft.Colors.GREY_600),
            ft.Container(expand=True),
            ft.IconButton(
                icon=ft.Icons.CLOSE,
                icon_size=ICON_SIZE,
                tooltip="Close Diff",
                on_click=lambda _: on_close() if on_close else None,
            ),
        ],
    )

    diff_container = ft.Container(
        content=fce.CodeEditor(
            language=fce.CodeLanguage.DIFF,
            code_theme=code_theme,
            value=diff_text,
            read_only=True,
            text_style=ft.TextStyle(font_family="monospace", height=1.2, size=12),
            gutter_style=fce.GutterStyle(
                text_style=ft.TextStyle(font_family="monospace", height=1.2),
                show_line_numbers=True,
                show_folding_handles=False,
                width=60,
            ),
            expand=True,
        ),
        height=200,
        border=ft.Border.all(1, ft.Colors.GREY_800),
        border_radius=4,
    )

    return ft.Column(
        spacing=2,
        controls=[
            header_row,
            ft.Divider(height=1, color=ft.Colors.GREY_800),
            diff_container,
        ],
    )


def compute_unified_diff(original: str, current: str) -> tuple[str, int, int]:
    """Compute a unified diff between two strings.

    Returns:
        A tuple of (diff_text, lines_added, lines_removed).
    """
    original_lines = original.splitlines(keepends=True)
    current_lines = current.splitlines(keepends=True)

    diff_lines = list(
        difflib.unified_diff(
            original_lines,
            current_lines,
            fromfile="original",
            tofile="current",
            lineterm="",
        )
    )

    added = sum(
        1 for ln in diff_lines if ln.startswith("+") and not ln.startswith("+++")
    )
    removed = sum(
        1 for ln in diff_lines if ln.startswith("-") and not ln.startswith("---")
    )

    diff_text = "\n".join(line.rstrip("\n") for line in diff_lines)
    return diff_text, added, removed
