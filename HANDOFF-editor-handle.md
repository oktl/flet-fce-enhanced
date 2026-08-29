# Handoff: extend EditorHandle for external drivers

**Written:** 2026-08-28 · **Repo state:** `main` @ `67fecee`, clean, in sync with origin,
`version = "0.2.1"` (published to PyPI)

## Why this work exists

`uv-forger` embeds `EnhancedCodeEditor` and drives it from its own keyboard handler. Against
the 0.1.x class-based editor it did that by calling **15 private members** on the control
instance. The 0.2.x declarative rewrite removed all of them, so uv-forger cannot upgrade past
`fce-enhanced 0.1.6`.

The fix is not for uv-forger to find new privates to poke. It is for `EditorHandle` to expose
what an embedder legitimately needs, so the coupling runs through a public API.

Related: uv-forger is currently **broken** on `fce-enhanced 0.1.6 + Flet 0.86.5` — 0.1.6's
`self._dirty: bool` collides with Flet's reserved `BaseControl._dirty: dict`, so `page.update()`
raises `AttributeError: 'bool' object has no attribute 'clear'` when the editor is mounted.
That collision does **not** exist in 0.2.x (dirty is `ft.use_state`).

## What uv-forger uses today (the full list)

From `uv_forger/ui/dialogs.py:2843` (`create_file_editor_view`) and
`uv_forger/handlers/build_handlers.py:655` (`_handle_editor_keyboard`):

| Private member used | Covered by 0.2.1 `EditorHandle`? |
| --- | --- |
| `_do_save`, `_do_save_as` | yes — `handle.save`, `handle.save_as` |
| `.value` | yes — `handle.value` |
| `_current_path` (read) | yes — `handle.current_path` |
| `_current_path` (**write**) | **no** — see gap 1 |
| `_title_bar.value` (write) | **no** — `on_title_change` only notifies |
| `_code_editor` | **no** — see gap 3 |
| `_open_search`, `_close_search`, `_search_bar.is_open` | **no** |
| `_show_help`, `_toggle_diff_pane`, `_handle_goto_line` | **no** |
| `_toggle_read_only`, `_handle_language_click` | **no** |
| `_open_command_palette`, `_change_font_size` | **no** |

## The three gaps

### Gap 1 — no way to set a save target without loading from disk

`initial_path` triggers `page.run_task(open_path, initial_path)` in the `_open_initial` effect
(`editor.py:600-604`), which **reads that file and replaces the content**. uv-forger needs the
opposite: display the content it passes in `value=` (a user's unsaved override), while saves go
to a template path that may not exist on disk yet.

Suggested: `initial_path: str | None` gains a companion `load_initial: bool = True`, or add a
separate `save_path: str | None` that seeds `current_path` without opening. Either is a small
change to `_open_initial`.

### Gap 2 — ten actions have no public route

All ten already exist as closures inside the component body and are **in scope** where the
handle is populated (`editor.py:606`), so this is mechanical wiring, not new behaviour:

```
_handle_revert          412      _toggle_diff_pane       447
_handle_language_click  429      _change_font_size       450
_toggle_read_only       438      _open_search            457
_toggle_gutter          444      _close_search           461
                                 _handle_goto_line       466
                                 _show_help              477
                                 _open_command_palette   480
```

Also expose the `search_open` state (`editor.py:209`) — uv-forger checks it to decide whether
Escape closes the search bar or closes the whole editor view.

Add these next to the existing four assignments at `editor.py:609-613`. Async ones follow the
existing `lambda: page.run_task(...)` pattern; sync ones can be assigned directly.

### Gap 3 — initial syntax highlighting

uv-forger carries a workaround: on mount, set the inner `fce.CodeEditor.language` to a dummy
value, flush, then set the real one after 50ms, because highlighting doesn't apply on first
render. It reaches `editor._code_editor` to do this.

0.2.x exposes no inner control, and nothing in the source suggests the underlying bug was
fixed. **Verify empirically** whether 0.2.x still needs it. If it does, the fix belongs here
(inside the component), not in every embedder.

## Suggested shape

Keep `EditorHandle` a dataclass of callables so it stays render-stable. Something like:

```python
@dataclass
class EditorHandle:
    # existing
    open_path: Any = None
    save: Any = None
    save_as: Any = None
    close: Any = None
    # new — actions
    revert: Any = None
    open_search: Any = None      # (with_replace: bool = False)
    close_search: Any = None
    goto_line: Any = None
    command_palette: Any = None
    show_help: Any = None
    toggle_diff: Any = None
    toggle_read_only: Any = None
    toggle_gutter: Any = None
    change_font_size: Any = None  # (delta: int)
    set_language: Any = None
    # new — readers
    _get_search_open: Any = None

    @property
    def search_open(self) -> bool:
        return self._get_search_open() if self._get_search_open else False
```

Name them without the leading underscore in the public handle — the point is that embedders
stop touching privates.

## Release checklist (learned the hard way today)

The `v0.2.0` release failed because the tag pointed at `2e024b4`, one commit **before** the
version bump, so CI built `0.1.6` artifacts and PyPI rejected them as duplicates. That release
and tag were deleted; `v0.2.1` was tagged at `67fecee` and published successfully.

So: **bump the version, commit, then tag that commit.** Verify with
`git show <tag>:pyproject.toml | grep version` before creating the GitHub release. The workflow
triggers on `release: published`, not on tag push.

Note `67fecee`'s commit message says "version 0.2.0" but the file says `0.2.1` — harmless, just
confusing in `git log`.

## Definition of done

- `EditorHandle` covers every row marked "no" in the table above.
- A save target can be set without reading from disk.
- The highlighting question is answered (fixed in-component, or documented as still needed).
- Version bumped, tagged on the bump commit, released, PyPI shows the new version.
- Then uv-forger can migrate — see `declarative-refactor.md` in that repo.
