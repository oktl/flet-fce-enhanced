"""Tests for flet_code_editor_enhanced.search (SearchReplaceBar control)."""

from unittest.mock import MagicMock


from flet_code_editor_enhanced.search import SearchReplaceBar


# --- Helpers ---


def _make_bar(
    text: str = "hello world hello",
) -> tuple[SearchReplaceBar, MagicMock, MagicMock]:
    """Create a SearchReplaceBar with mock callbacks."""
    set_selection = MagicMock()
    replace_text = MagicMock()
    bar = SearchReplaceBar(
        get_text=lambda: text,
        set_selection=set_selection,
        replace_text=replace_text,
        on_close=MagicMock(),
    )
    return bar, set_selection, replace_text


def _search(bar: SearchReplaceBar, query: str, case_sensitive: bool = False) -> None:
    """Simulate typing a search query."""
    bar._case_sensitive = case_sensitive
    bar._search_query = query
    bar._search_field.value = query
    bar._compute_matches()
    bar._update_match_display()


# --- Open / Close ---


def test_initially_not_visible():
    bar, _, _ = _make_bar()
    assert bar.is_open is False
    assert bar.controls == []


def test_open_makes_visible():
    bar, _, _ = _make_bar()
    bar.open()
    assert bar.is_open is True
    assert len(bar.controls) == 2  # search_row + replace_row


def test_open_with_replace():
    bar, _, _ = _make_bar()
    bar.open(with_replace=True)
    assert bar._replace_row.visible is True


def test_open_without_replace():
    bar, _, _ = _make_bar()
    bar.open(with_replace=False)
    assert bar._replace_row.visible is False


def test_close_hides_and_resets():
    bar, _, _ = _make_bar()
    bar.open()
    _search(bar, "hello")
    bar.close()
    assert bar.is_open is False
    assert bar.controls == []
    assert bar._search_query == ""
    assert bar._match_positions == []
    assert bar._current_match_index == -1


def test_close_calls_on_close():
    bar, _, _ = _make_bar()
    bar.open()
    bar.close()
    bar._on_close.assert_called_once()


# --- Match computation ---


def test_finds_all_matches():
    bar, sel, _ = _make_bar("hello world hello")
    _search(bar, "hello")
    assert len(bar._match_positions) == 2
    assert bar._match_positions[0] == (0, 5)
    assert bar._match_positions[1] == (12, 17)


def test_no_matches():
    bar, sel, _ = _make_bar("hello world")
    _search(bar, "xyz")
    assert len(bar._match_positions) == 0
    assert bar._current_match_index == -1


def test_empty_query_no_matches():
    bar, sel, _ = _make_bar("hello world")
    _search(bar, "")
    assert len(bar._match_positions) == 0


def test_first_match_selected():
    bar, sel, _ = _make_bar("hello world hello")
    _search(bar, "hello")
    assert bar._current_match_index == 0
    sel.assert_called_with(0, 5)


def test_match_count_label():
    bar, _, _ = _make_bar("hello world hello")
    _search(bar, "hello")
    assert bar._match_count_label.value == "1 of 2"


def test_no_results_label():
    bar, _, _ = _make_bar("hello world")
    _search(bar, "xyz")
    assert bar._match_count_label.value == "No results"


# --- Case sensitivity ---


def test_case_insensitive_by_default():
    bar, sel, _ = _make_bar("Hello HELLO hello")
    _search(bar, "hello", case_sensitive=False)
    assert len(bar._match_positions) == 3


def test_case_sensitive_search():
    bar, sel, _ = _make_bar("Hello HELLO hello")
    _search(bar, "hello", case_sensitive=True)
    assert len(bar._match_positions) == 1
    assert bar._match_positions[0] == (12, 17)


def test_toggle_case():
    bar, _, _ = _make_bar("Hello hello")
    _search(bar, "hello", case_sensitive=False)
    assert len(bar._match_positions) == 2

    bar._case_sensitive = True
    bar._compute_matches()
    assert len(bar._match_positions) == 1


# --- Navigation ---


def test_next_match():
    bar, sel, _ = _make_bar("aa bb aa cc aa")
    _search(bar, "aa")
    assert bar._current_match_index == 0

    bar._go_to_match(1)
    assert bar._current_match_index == 1
    sel.assert_called_with(6, 8)


def test_prev_match():
    bar, sel, _ = _make_bar("aa bb aa cc aa")
    _search(bar, "aa")
    bar._go_to_match(-1)  # wraps to last
    assert bar._current_match_index == 2
    sel.assert_called_with(12, 14)


def test_next_wraps_around():
    bar, sel, _ = _make_bar("aa bb aa")
    _search(bar, "aa")
    bar._go_to_match(1)  # index 1
    bar._go_to_match(1)  # wraps to 0
    assert bar._current_match_index == 0


def test_prev_wraps_around():
    bar, sel, _ = _make_bar("aa bb aa")
    _search(bar, "aa")
    bar._go_to_match(-1)  # wraps to 1
    assert bar._current_match_index == 1


def test_navigate_with_no_matches():
    bar, sel, _ = _make_bar("hello")
    _search(bar, "xyz")
    bar._go_to_match(1)  # should not crash
    assert bar._current_match_index == -1


# --- Replace one ---


def test_replace_one():
    text = "hello world hello"
    replaced = []

    def mock_replace(new_text):
        replaced.append(new_text)

    bar = SearchReplaceBar(
        get_text=lambda: replaced[-1] if replaced else text,
        set_selection=MagicMock(),
        replace_text=mock_replace,
    )
    _search(bar, "hello")
    bar._replace_field.value = "hi"
    bar._handle_replace_one(None)

    assert replaced[0] == "hi world hello"


def test_replace_one_with_empty():
    text = "hello world"
    replaced = []

    def mock_replace(new_text):
        replaced.append(new_text)

    bar = SearchReplaceBar(
        get_text=lambda: replaced[-1] if replaced else text,
        set_selection=MagicMock(),
        replace_text=mock_replace,
    )
    _search(bar, "hello")
    bar._replace_field.value = ""
    bar._handle_replace_one(None)

    assert replaced[0] == " world"


def test_replace_one_no_match():
    bar, _, replace_text = _make_bar("hello")
    _search(bar, "xyz")
    bar._handle_replace_one(None)
    replace_text.assert_not_called()


# --- Replace all ---


def test_replace_all():
    text = "hello world hello"
    replaced = []

    bar = SearchReplaceBar(
        get_text=lambda: replaced[-1] if replaced else text,
        set_selection=MagicMock(),
        replace_text=lambda t: replaced.append(t),
    )
    _search(bar, "hello")
    bar._replace_field.value = "hi"
    bar._handle_replace_all(None)

    assert replaced[0] == "hi world hi"


def test_replace_all_case_insensitive():
    text = "Hello world HELLO"
    replaced = []

    bar = SearchReplaceBar(
        get_text=lambda: replaced[-1] if replaced else text,
        set_selection=MagicMock(),
        replace_text=lambda t: replaced.append(t),
    )
    _search(bar, "hello", case_sensitive=False)
    bar._replace_field.value = "hi"
    bar._handle_replace_all(None)

    assert replaced[0] == "hi world hi"


def test_replace_all_case_sensitive():
    text = "Hello world hello"
    replaced = []

    bar = SearchReplaceBar(
        get_text=lambda: replaced[-1] if replaced else text,
        set_selection=MagicMock(),
        replace_text=lambda t: replaced.append(t),
    )
    _search(bar, "hello", case_sensitive=True)
    bar._replace_field.value = "hi"
    bar._handle_replace_all(None)

    assert replaced[0] == "Hello world hi"


def test_replace_all_no_matches():
    bar, _, replace_text = _make_bar("hello")
    _search(bar, "xyz")
    bar._handle_replace_all(None)
    replace_text.assert_not_called()


# --- Recompute ---


def test_recompute_updates_matches():
    current_text = ["hello world hello"]

    bar = SearchReplaceBar(
        get_text=lambda: current_text[0],
        set_selection=MagicMock(),
        replace_text=MagicMock(),
    )
    bar._search_query = "hello"
    bar.recompute()
    assert len(bar._match_positions) == 2

    # Simulate text change
    current_text[0] = "hello world"
    bar.recompute()
    assert len(bar._match_positions) == 1


# --- Toggle replace visibility ---


def test_toggle_replace():
    bar, _, _ = _make_bar()
    bar.open(with_replace=False)
    assert bar._replace_row.visible is False

    bar._handle_toggle_replace(None)
    assert bar._replace_row.visible is True

    bar._handle_toggle_replace(None)
    assert bar._replace_row.visible is False
