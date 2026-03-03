"""Tests for fce_enhanced.diff_pane (DiffPane control)."""

from unittest.mock import MagicMock

from fce_enhanced.diff_pane import DiffPane, compute_unified_diff

# --- Helpers ---


def _make_pane(
    original: str = "hello\nworld\n",
    current: str = "hello\nworld\n",
) -> tuple[DiffPane, MagicMock]:
    """Create a DiffPane with mock callbacks."""
    on_close = MagicMock()
    pane = DiffPane(
        get_original_text=lambda: original,
        get_current_text=lambda: current,
        on_close=on_close,
    )
    return pane, on_close


# --- Open / Close ---


def test_initially_not_visible():
    pane, _ = _make_pane()
    assert pane.is_open is False
    assert pane.controls == []


def test_open_makes_visible():
    pane, _ = _make_pane()
    pane.open()
    assert pane.is_open is True
    assert len(pane.controls) == 3  # header_row + divider + diff_editor


def test_close_hides_and_resets():
    pane, _ = _make_pane(original="a\n", current="b\n")
    pane.open()
    pane.close()
    assert pane.is_open is False
    assert pane.controls == []
    assert pane._diff_editor.value == ""
    assert pane._stats_label.value == "No changes"


def test_close_calls_on_close():
    pane, on_close = _make_pane()
    pane.open()
    pane.close()
    on_close.assert_called_once()


def test_close_when_not_open_does_not_call_on_close():
    pane, on_close = _make_pane()
    pane.close()
    on_close.assert_not_called()


# --- compute_unified_diff ---


def test_no_changes():
    diff_text, added, removed = compute_unified_diff("hello\n", "hello\n")
    assert diff_text == ""
    assert added == 0
    assert removed == 0


def test_additions():
    diff_text, added, removed = compute_unified_diff("line1\n", "line1\nnew line\n")
    assert added > 0
    assert removed == 0
    assert "+new line" in diff_text


def test_deletions():
    diff_text, added, removed = compute_unified_diff("line1\nline2\n", "line1\n")
    assert removed > 0
    assert added == 0
    assert "-line2" in diff_text


def test_modifications():
    diff_text, added, removed = compute_unified_diff("old line\n", "new line\n")
    assert added > 0
    assert removed > 0
    assert "-old line" in diff_text
    assert "+new line" in diff_text


def test_empty_to_content():
    diff_text, added, removed = compute_unified_diff("", "hello\n")
    assert added > 0
    assert removed == 0


def test_content_to_empty():
    diff_text, added, removed = compute_unified_diff("hello\n", "")
    assert removed > 0
    assert added == 0


# --- Recompute with mutable text ---


def test_recompute_updates_on_text_change():
    current = ["hello\n"]
    pane = DiffPane(
        get_original_text=lambda: "hello\n",
        get_current_text=lambda: current[0],
    )
    pane.open()
    assert pane._stats_label.value == "No changes"

    current[0] = "hello\nworld\n"
    pane.recompute()
    assert pane._stats_label.value == "+1 / -0"


def test_stats_label_format():
    pane, _ = _make_pane(original="a\nb\nc\n", current="a\nx\ny\nz\n")
    pane.open()
    # b,c removed (-2), x,y,z added (+3)
    stats = pane._stats_label.value
    assert stats.startswith("+")
    assert "/ -" in stats
