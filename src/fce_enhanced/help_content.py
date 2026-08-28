"""Help text displayed in the help dialog."""

HELP_TEXT = """\
## Keyboard Shortcuts

| Action | Mac | Windows / Linux |
|---|---|---|
| Open File | ⌘O | Ctrl+O |
| Save | ⌘S | Ctrl+S |
| Save As | ⇧⌘S | Ctrl+Shift+S |
| Close File | ⌘W | Ctrl+W |
| Revert to Saved | ⇧⌘R | Ctrl+Shift+R |
| Find | ⌘F | Ctrl+F |
| Find & Replace | ⌥⌘F | Ctrl+H |
| Go to Line | ⌘G | Ctrl+G |
| Command Palette | ⇧⌘P | Ctrl+Shift+P |
| Toggle Read-Only | ⌘L | Ctrl+L |
| Toggle Diff | ⌘D | Ctrl+D |
| Toggle Gutter | ⇧⌘G | Ctrl+Shift+G |
| Change Language | ⇧⌘L | Ctrl+Shift+L |
| Increase Font Size | ⌘+ | Ctrl++ |
| Decrease Font Size | ⌘- | Ctrl+- |
| Help | F1 | F1 |
| Close Search Bar | Escape | Escape |

## Toolbar

- **Open / Save / Save As / Close / Revert** — file operations
- **Find** — open the search bar (toggle replace with the expand button)
- **Diff** — toggle a unified diff pane showing changes since last save
- **Go to Line** — jump to a specific line number
- **Font Size** — increase or decrease editor font size
- **Read-Only Lock** — toggle read-only mode
- **Ruff** — toggle automatic ruff check + format on save (Python files only)
- **Gutter** — toggle the line-number gutter
- **Language** — change syntax highlighting language
- **Theme** — choose from 89 editor color themes
- **Help** — open this dialog

## Search & Replace

- Open with ⌘F (find) or ⌥⌘F (find & replace) on Mac, Ctrl+H on Windows/Linux.
- Use the **Aa** button to toggle case sensitivity.
- Use the **ABC** button to toggle whole word matching.
- Navigate matches with the arrow buttons or press Enter.
- Press Escape to close the search bar.

## Ruff Integration

Ruff on Save is automatically enabled when you open or save-as a `.py` file,
and disabled when you close the file. You can also toggle it manually with the
toolbar button. When enabled, saving a Python file automatically runs
`ruff check --fix` followed by `ruff format`. Remaining lint warnings are
shown in a snackbar. Requires [ruff](https://docs.astral.sh/ruff/) to be
installed.

## Command Palette

Press ⇧⌘P (Mac) or Ctrl+Shift+P to open the command palette. Type to filter
commands, then click to execute.
"""
