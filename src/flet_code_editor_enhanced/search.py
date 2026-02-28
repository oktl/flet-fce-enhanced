"""Search & Replace bar for EnhancedCodeEditor."""

from __future__ import annotations

import re
from collections.abc import Callable

import flet as ft


class SearchReplaceBar(ft.Column):
    """A search/replace bar that communicates with an editor via callbacks.

    Args:
        get_text: Callback that returns the current editor content.
        set_selection: Callback ``(base_offset, extent_offset)`` to highlight a match.
        replace_text: Callback ``(new_full_text)`` to replace the entire editor content.
        focus_editor: Callback to give focus back to the editor (for explicit navigation).
        on_close: Callback invoked when the bar is dismissed (e.g. to refocus the editor).
    """

    def __init__(
        self,
        get_text: Callable[[], str],
        set_selection: Callable[[int, int], None],
        replace_text: Callable[[str], None],
        focus_editor: Callable[[], None] | None = None,
        on_close: Callable[[], None] | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)

        # --- Callbacks ---
        self._get_text = get_text
        self._set_selection = set_selection
        self._replace_text = replace_text
        self._focus_editor = focus_editor
        self._on_close = on_close

        # --- State ---
        self._search_query: str = ""
        self._case_sensitive: bool = False
        self._match_positions: list[tuple[int, int]] = []  # (start, end)
        self._current_match_index: int = -1
        self._replace_visible: bool = False

        # --- UI elements ---
        self._search_field = ft.TextField(
            hint_text="Find",
            dense=True,
            expand=True,
            text_size=13,
            content_padding=ft.Padding.symmetric(horizontal=8, vertical=4),
            border_color=ft.Colors.GREY_600,
            focused_border_color=ft.Colors.GREY_400,
            on_change=self._handle_search_change,
            on_submit=self._handle_next,
        )

        self._match_count_label = ft.Text(
            "No results", size=12, color=ft.Colors.GREY_600
        )

        self._case_btn = ft.IconButton(
            icon=ft.Icons.FORMAT_SIZE,
            tooltip="Match Case",
            icon_size=16,
            selected=False,
            on_click=self._handle_toggle_case,
        )

        self._replace_field = ft.TextField(
            hint_text="Replace",
            dense=True,
            expand=True,
            text_size=13,
            content_padding=ft.Padding.symmetric(horizontal=8, vertical=4),
            border_color=ft.Colors.GREY_800,
            focused_border_color=ft.Colors.GREY_600,
        )

        self._replace_toggle_btn = ft.IconButton(
            icon=ft.Icons.EXPAND_MORE,
            tooltip="Toggle Replace",
            icon_size=16,
            on_click=self._handle_toggle_replace,
        )

        self._replace_row = ft.Row(
            spacing=4,
            visible=False,
            controls=[
                ft.Container(width=32),  # spacer to align with search field
                self._replace_field,
                ft.TextButton("Replace", on_click=self._handle_replace_one),
                ft.TextButton("Replace All", on_click=self._handle_replace_all),
            ],
        )

        search_row = ft.Row(
            spacing=4,
            controls=[
                self._replace_toggle_btn,
                self._search_field,
                self._match_count_label,
                self._case_btn,
                ft.IconButton(
                    icon=ft.Icons.ARROW_UPWARD,
                    tooltip="Previous Match",
                    icon_size=16,
                    on_click=self._handle_prev,
                ),
                ft.IconButton(
                    icon=ft.Icons.ARROW_DOWNWARD,
                    tooltip="Next Match",
                    icon_size=16,
                    on_click=self._handle_next,
                ),
                ft.IconButton(
                    icon=ft.Icons.CLOSE,
                    tooltip="Close (Escape)",
                    icon_size=16,
                    on_click=lambda _: self.close(),
                ),
            ],
        )

        self._search_row = search_row
        self.spacing = 2
        self._is_open = False
        # Start with no children — rows are added/removed by open()/close()
        # to avoid Flet rendering issues with initially-invisible controls.
        self.controls = []

    # --- Public API ---

    @property
    def is_open(self) -> bool:
        """Whether the search bar is currently open."""
        return self._is_open

    def open(self, *, with_replace: bool = False) -> None:
        """Show the search bar, optionally with replace row."""
        self._is_open = True
        self._replace_visible = with_replace
        self._replace_row.visible = with_replace
        self._replace_toggle_btn.icon = (
            ft.Icons.EXPAND_LESS if with_replace else ft.Icons.EXPAND_MORE
        )
        # Populate controls so Flet renders the rows
        self.controls = [self._search_row, self._replace_row]
        self.recompute()

    async def focus_search(self) -> None:
        """Focus the search text field."""
        await self._search_field.focus()

    def close(self) -> None:
        """Hide the search bar and clear state."""
        was_open = self._is_open
        self._is_open = False
        self._search_query = ""
        self._search_field.value = ""
        self._match_positions = []
        self._current_match_index = -1
        self._match_count_label.value = "No results"
        # Remove all children so Flet renders nothing
        self.controls = []
        if was_open and self._on_close:
            self._on_close()

    def recompute(self) -> None:
        """Recompute matches against current editor content. Call when text changes."""
        self._compute_matches()
        self._update_match_display()

    # --- Core logic ---

    def _compute_matches(self) -> None:
        """Find all occurrences of the search query in the editor text."""
        self._match_positions = []
        self._current_match_index = -1

        if not self._search_query:
            return

        text = self._get_text()
        query = self._search_query

        if not self._case_sensitive:
            text_search = text.lower()
            query = query.lower()
        else:
            text_search = text

        start = 0
        while True:
            idx = text_search.find(query, start)
            if idx == -1:
                break
            self._match_positions.append((idx, idx + len(self._search_query)))
            start = idx + 1

        if self._match_positions:
            self._current_match_index = 0

    def _update_match_display(self) -> None:
        """Update the match count label and highlight current match."""
        count = len(self._match_positions)
        if not self._search_query:
            self._match_count_label.value = "No results"
        elif count == 0:
            self._match_count_label.value = "No results"
        else:
            self._match_count_label.value = (
                f"{self._current_match_index + 1} of {count}"
            )
            start, end = self._match_positions[self._current_match_index]
            self._set_selection(start, end)

    def _go_to_match(self, delta: int) -> None:
        """Navigate to next (+1) or previous (-1) match with wrapping."""
        if not self._match_positions:
            return
        self._current_match_index = (self._current_match_index + delta) % len(
            self._match_positions
        )
        self._update_match_display()

    # --- Event handlers ---

    def _safe_update(self) -> None:
        """Call self.update() only if the control is mounted on a page."""
        try:
            self.update()
        except RuntimeError:
            pass

    def _handle_search_change(self, e) -> None:
        self._search_query = e.control.value or ""
        self.recompute()
        self._safe_update()

    def _handle_next(self, _e) -> None:
        self._go_to_match(1)
        if self._focus_editor:
            self._focus_editor()
        self._safe_update()

    def _handle_prev(self, _e) -> None:
        self._go_to_match(-1)
        if self._focus_editor:
            self._focus_editor()
        self._safe_update()

    def _handle_toggle_case(self, _e) -> None:
        self._case_sensitive = not self._case_sensitive
        self._case_btn.selected = self._case_sensitive
        self._case_btn.icon_color = ft.Colors.BLUE if self._case_sensitive else None
        self.recompute()
        self._safe_update()

    def _handle_toggle_replace(self, _e) -> None:
        self._replace_visible = not self._replace_visible
        self._replace_row.visible = self._replace_visible
        self._replace_toggle_btn.icon = (
            ft.Icons.EXPAND_LESS if self._replace_visible else ft.Icons.EXPAND_MORE
        )
        self._safe_update()

    def _handle_replace_one(self, _e) -> None:
        """Replace the current match and advance to next."""
        if not self._match_positions or self._current_match_index < 0:
            return

        text = self._get_text()
        start, end = self._match_positions[self._current_match_index]
        replacement = self._replace_field.value or ""
        new_text = text[:start] + replacement + text[end:]
        self._replace_text(new_text)

        # Recompute and try to stay near the same position
        old_index = self._current_match_index
        self._compute_matches()
        if self._match_positions:
            self._current_match_index = min(old_index, len(self._match_positions) - 1)
        self._update_match_display()
        self._safe_update()

    def _handle_replace_all(self, _e) -> None:
        """Replace all matches at once."""
        if not self._match_positions:
            return

        text = self._get_text()
        replacement = self._replace_field.value or ""
        query = self._search_query

        if self._case_sensitive:
            new_text = text.replace(query, replacement)
        else:
            new_text = re.sub(re.escape(query), replacement, text, flags=re.IGNORECASE)

        self._replace_text(new_text)
        self._compute_matches()
        self._update_match_display()
        self._safe_update()
