"""Search & Replace bar for EnhancedCodeEditor (declarative)."""

from __future__ import annotations

from collections.abc import Callable
from contextlib import suppress
import re

import flet as ft

SEARCH_ICON_SIZE = 18
SEARCH_BUTTON_STYLE = ft.ButtonStyle(text_style=ft.TextStyle(size=10))


def compute_matches(
    text: str,
    query: str,
    *,
    case_sensitive: bool = False,
    whole_word: bool = False,
) -> list[tuple[int, int]]:
    """Return ``(start, end)`` offsets of every occurrence of ``query`` in ``text``."""
    if not query:
        return []

    matches: list[tuple[int, int]] = []
    if whole_word:
        pattern = r"\b" + re.escape(query) + r"\b"
        flags = 0 if case_sensitive else re.IGNORECASE
        for m in re.finditer(pattern, text, flags):
            matches.append((m.start(), m.end()))
    else:
        if case_sensitive:
            haystack, needle = text, query
        else:
            haystack, needle = text.lower(), query.lower()
        start = 0
        while True:
            idx = haystack.find(needle, start)
            if idx == -1:
                break
            matches.append((idx, idx + len(query)))
            start = idx + 1
    return matches


@ft.component
def SearchReplaceBar(
    get_text: Callable[[], str],
    set_selection: Callable[[int, int], None],
    replace_text: Callable[[str], None],
    focus_editor: Callable[[], None] | None = None,
    on_close: Callable[[], None] | None = None,
    with_replace: bool = False,
    text_version: int = 0,
) -> ft.Control:
    """A search/replace bar that talks to an editor via callbacks.

    Rendered only while open (the parent controls visibility via conditional
    rendering). Match positions are derived from the current editor text on
    every render via the pure :func:`compute_matches` function.

    Args:
        get_text: Returns the current editor content.
        set_selection: ``(base_offset, extent_offset)`` to highlight a match.
        replace_text: ``(new_full_text)`` to replace the entire editor content.
        focus_editor: Give focus back to the editor (for explicit navigation).
        on_close: Invoked when the bar is dismissed.
        with_replace: Whether the replace row starts visible.
        text_version: Bumped by the parent when editor text changes, to force a
            match recompute.
    """
    query, set_query = ft.use_state("")
    case_sensitive, set_case_sensitive = ft.use_state(False)
    whole_word, set_whole_word = ft.use_state(False)
    replace_visible, set_replace_visible = ft.use_state(with_replace)
    current_index, set_current_index = ft.use_state(0)

    replace_ref = ft.use_ref("")
    navigated_ref = ft.use_ref(False)
    search_field_ref = ft.use_ref(lambda: ft.Ref())

    text = get_text()
    matches = compute_matches(
        text, query, case_sensitive=case_sensitive, whole_word=whole_word
    )
    count = len(matches)
    idx = current_index if 0 <= current_index < count else 0

    # Highlight the current match whenever the match set or selection changes.
    def _highlight() -> None:
        if matches:
            start, end = matches[idx]
            set_selection(start, end)

    ft.use_effect(
        _highlight, [query, case_sensitive, whole_word, idx, count, text_version]
    )

    # Focus the search field when the bar first mounts.
    async def _focus_field() -> None:
        ctrl = search_field_ref.current.current
        if ctrl is not None:
            with suppress(Exception):
                await ctrl.focus()

    ft.use_effect(_focus_field, [])

    if not query or count == 0:
        match_label = "No results"
    else:
        match_label = f"{idx + 1} of {count}"

    # --- Handlers ---

    def _on_search_change(e) -> None:
        navigated_ref.current = False
        set_current_index(0)
        set_query(e.control.value or "")

    def _go(delta: int) -> None:
        if not matches:
            return
        if navigated_ref.current:
            set_current_index((idx + delta) % count)
        else:
            navigated_ref.current = True
            set_current_index(idx)
        if focus_editor:
            focus_editor()

    def _on_replace_one(_e) -> None:
        if not matches:
            return
        start, end = matches[idx]
        replacement = replace_ref.current or ""
        new_text = text[:start] + replacement + text[end:]
        replace_text(new_text)
        set_current_index(min(idx, max(0, count - 2)))

    def _on_replace_all(_e) -> None:
        if not matches:
            return
        replacement = replace_ref.current or ""
        if case_sensitive:
            new_text = text.replace(query, replacement)
        else:
            new_text = re.sub(
                re.escape(query), lambda _m: replacement, text, flags=re.IGNORECASE
            )
        replace_text(new_text)
        set_current_index(0)

    # --- Layout ---

    search_row = ft.Row(
        spacing=4,
        controls=[
            ft.IconButton(
                icon=ft.Icons.EXPAND_LESS if replace_visible else ft.Icons.EXPAND_MORE,
                tooltip="Toggle Replace",
                icon_size=SEARCH_ICON_SIZE,
                on_click=lambda _: set_replace_visible(not replace_visible),
            ),
            ft.TextField(
                ref=search_field_ref.current,
                value=query,
                hint_text="Find",
                dense=True,
                width=200,
                text_size=13,
                content_padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                border_color=ft.Colors.GREY_800,
                focused_border_color=ft.Colors.GREY_600,
                on_change=_on_search_change,
                on_submit=lambda _: _go(1),
                border_width=0.5,
            ),
            ft.Text(match_label, size=12, color=ft.Colors.GREY_600),
            ft.IconButton(
                icon=ft.Icons.FORMAT_SIZE,
                tooltip="Match Case",
                icon_size=SEARCH_ICON_SIZE,
                selected=case_sensitive,
                icon_color=ft.Colors.BLUE if case_sensitive else None,
                on_click=lambda _: set_case_sensitive(not case_sensitive),
            ),
            ft.IconButton(
                icon=ft.Icons.ABC,
                tooltip="Whole Word",
                icon_size=18,
                selected=whole_word,
                icon_color=ft.Colors.BLUE if whole_word else None,
                on_click=lambda _: set_whole_word(not whole_word),
            ),
            ft.IconButton(
                icon=ft.Icons.ARROW_UPWARD,
                tooltip="Previous Match",
                icon_size=SEARCH_ICON_SIZE,
                on_click=lambda _: _go(-1),
            ),
            ft.IconButton(
                icon=ft.Icons.ARROW_DOWNWARD,
                tooltip="Next Match",
                icon_size=SEARCH_ICON_SIZE,
                on_click=lambda _: _go(1),
            ),
            ft.IconButton(
                icon=ft.Icons.CLOSE,
                tooltip="Close (Escape)",
                icon_size=SEARCH_ICON_SIZE,
                on_click=lambda _: on_close() if on_close else None,
            ),
        ],
    )

    replace_row = ft.Row(
        spacing=4,
        visible=replace_visible,
        controls=[
            ft.Container(width=40),  # spacer to align with search field
            ft.TextField(
                value=replace_ref.current,
                hint_text="Replace",
                dense=True,
                width=200,
                text_size=13,
                content_padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                border_color=ft.Colors.GREY_800,
                focused_border_color=ft.Colors.GREY_600,
                on_change=lambda e: setattr(replace_ref, "current", e.control.value),
                border_width=0.5,
            ),
            ft.TextButton(
                "Replace", on_click=_on_replace_one, style=SEARCH_BUTTON_STYLE
            ),
            ft.TextButton(
                "Replace All", on_click=_on_replace_all, style=SEARCH_BUTTON_STYLE
            ),
        ],
    )

    return ft.Column(spacing=2, controls=[search_row, replace_row])
