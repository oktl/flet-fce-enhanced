"""Toggleable unified diff pane for EnhancedCodeEditor."""

from __future__ import annotations

from collections.abc import Callable
import difflib

import flet as ft
import flet_code_editor as fce

from fce_enhanced.themes import DEFAULT_THEME

ICON_SIZE = 16


class DiffPane(ft.Column):
    """A toggleable pane showing a unified diff between saved and current content.

    Uses a read-only CodeEditor with ``language=DIFF`` for green/red syntax
    coloring of additions and deletions.

    Args:
        get_original_text: Callback returning the last-saved file content.
        get_current_text: Callback returning the current editor content.
        on_close: Callback invoked when the pane is dismissed.
        code_theme: Initial code theme (should match the main editor).
    """

    def __init__(
        self,
        get_original_text: Callable[[], str],
        get_current_text: Callable[[], str],
        on_close: Callable[[], None] | None = None,
        code_theme: fce.CustomCodeTheme | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)

        self._get_original_text = get_original_text
        self._get_current_text = get_current_text
        self._on_close = on_close

        if code_theme is None:
            code_theme = DEFAULT_THEME

        self._stats_label = ft.Text("No changes", size=11, color=ft.Colors.GREY_600)

        self._diff_editor = fce.CodeEditor(
            language=fce.CodeLanguage.DIFF,
            code_theme=code_theme,
            value="",
            read_only=True,
            text_style=ft.TextStyle(font_family="monospace", height=1.2, size=12),
            gutter_style=fce.GutterStyle(
                text_style=ft.TextStyle(font_family="monospace", height=1.2),
                show_line_numbers=True,
                show_folding_handles=False,
                width=60,
            ),
            expand=True,
        )

        self._diff_container = ft.Container(
            content=self._diff_editor,
            height=200,
            border=ft.Border.all(1, ft.Colors.GREY_800),
            border_radius=4,
        )

        self._header_row = ft.Row(
            spacing=8,
            controls=[
                ft.Icon(ft.Icons.DIFFERENCE, size=ICON_SIZE, color=ft.Colors.GREY_600),
                ft.Text("Diff", size=12, weight=ft.FontWeight.BOLD),
                self._stats_label,
                ft.Container(expand=True),
                ft.IconButton(
                    icon=ft.Icons.CLOSE,
                    icon_size=ICON_SIZE,
                    tooltip="Close Diff",
                    on_click=lambda _: self.close(),
                ),
            ],
        )

        self.spacing = 2
        self._is_open = False
        self.controls = []

    # --- Public API ---

    @property
    def is_open(self) -> bool:
        """Whether the diff pane is currently visible."""
        return self._is_open

    @property
    def code_theme(self) -> fce.CustomCodeTheme:
        """The current code theme of the diff editor."""
        return self._diff_editor.code_theme

    @code_theme.setter
    def code_theme(self, theme: fce.CustomCodeTheme) -> None:
        self._diff_editor.code_theme = theme

    def open(self) -> None:
        """Show the diff pane and compute the current diff."""
        self._is_open = True
        self.controls = [
            self._header_row,
            ft.Divider(height=1, color=ft.Colors.GREY_800),
            self._diff_container,
        ]
        self.recompute()

    def close(self) -> None:
        """Hide the diff pane and clear content."""
        was_open = self._is_open
        self._is_open = False
        self._diff_editor.value = ""
        self._stats_label.value = "No changes"
        self.controls = []
        if was_open and self._on_close:
            self._on_close()

    def recompute(self) -> None:
        """Recompute the unified diff and update the display."""
        original = self._get_original_text()
        current = self._get_current_text()

        diff_text, added, removed = compute_unified_diff(original, current)

        self._diff_editor.value = diff_text
        if added == 0 and removed == 0:
            self._stats_label.value = "No changes"
        else:
            self._stats_label.value = f"+{added} / -{removed}"
        self._safe_update()

    def _safe_update(self) -> None:
        """Call self.update() only if mounted."""
        try:
            self.update()
        except RuntimeError:
            pass


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
