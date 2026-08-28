"""Tests for fce_enhanced.search."""

import flet as ft

from fce_enhanced.search import SearchReplaceBar, compute_matches

# --- compute_matches (pure function) ---


def test_finds_all_matches():
    assert compute_matches("hello world hello", "hello") == [(0, 5), (12, 17)]


def test_no_matches():
    assert compute_matches("abc def", "xyz") == []


def test_empty_query():
    assert compute_matches("anything", "") == []


def test_empty_text():
    assert compute_matches("", "foo") == []


def test_case_insensitive_by_default():
    assert len(compute_matches("Foo foo FOO", "foo")) == 3


def test_case_sensitive():
    assert compute_matches("Foo foo FOO", "foo", case_sensitive=True) == [(4, 7)]


def test_match_offsets_use_query_length():
    # Case-insensitive match against differently-cased text keeps query length.
    assert compute_matches("FOO", "foo") == [(0, 3)]


def test_overlapping_matches():
    # find() with start=idx+1 allows overlapping occurrences.
    assert compute_matches("aaaa", "aa") == [(0, 2), (1, 3), (2, 4)]


def test_whole_word():
    assert compute_matches("foo foobar foo", "foo", whole_word=True) == [
        (0, 3),
        (11, 14),
    ]


def test_whole_word_case_sensitive():
    matches = compute_matches("Foo foo", "foo", whole_word=True, case_sensitive=True)
    assert matches == [(4, 7)]


def test_whole_word_special_chars_escaped():
    # query is regex-escaped, so "." is literal.
    assert compute_matches("a.b a b", "a.b", whole_word=True) == [(0, 3)]


# --- SearchReplaceBar (component render) ---


def _bar(render_component, **kw):
    return render_component(
        SearchReplaceBar,
        get_text=kw.pop("get_text", lambda: "foo bar"),
        set_selection=lambda a, b: None,
        replace_text=lambda t: None,
        **kw,
    )


def test_renders_search_and_replace_rows(render_component):
    tree, _ = _bar(render_component)
    assert isinstance(tree, ft.Column)
    assert len(tree.controls) == 2  # search row + replace row


def test_replace_row_hidden_by_default(render_component):
    tree, _ = _bar(render_component)
    _search_row, replace_row = tree.controls
    assert replace_row.visible is False


def test_replace_row_visible_with_replace(render_component):
    tree, _ = _bar(render_component, with_replace=True)
    _search_row, replace_row = tree.controls
    assert replace_row.visible is True
