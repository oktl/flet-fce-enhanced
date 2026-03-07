# fce-enhanced

[![PyPI version](https://img.shields.io/pypi/v/fce-enhanced)](https://pypi.org/project/fce-enhanced/)
[![Python versions](https://img.shields.io/pypi/pyversions/fce-enhanced)](https://pypi.org/project/fce-enhanced/)
[![License](https://img.shields.io/pypi/l/fce-enhanced)](https://github.com/oktl/flet-fce-enhanced/blob/main/LICENSE)
[![CI](https://github.com/oktl/flet-fce-enhanced/actions/workflows/ci.yml/badge.svg)](https://github.com/oktl/flet-fce-enhanced/actions/workflows/ci.yml)

An enhanced [Flet](https://flet.dev) CodeEditor control with file I/O, search/replace, syntax highlighting, and theme selection.

Built on top of [`flet-code-editor`](https://pypi.org/project/flet-code-editor/), adding a full-featured editing experience you can drop into any Flet app or run standalone. This project was created to explore and showcase what's possible with Flet — building a desktop-quality code editor entirely in Python.

![fce-enhanced screenshot](https://raw.githubusercontent.com/oktl/flet-fce-enhanced/main/docs/images/Screenshot.png)

## Install

```bash
pip install fce-enhanced
```

Or with uv:

```bash
uv add fce-enhanced
```

### Development setup

```bash
git clone https://github.com/oktl/flet-fce-enhanced.git
cd flet-fce-enhanced
uv sync
source .venv/bin/activate
pre-commit install  # optional, for development
```

## Usage

### Run as a standalone app

```bash
fce-enhanced
```

Or during development:

```bash
flet run src/fce_enhanced/editor.py
```

### Embed in your own Flet app

`EnhancedCodeEditor` is a standard `ft.Column` subclass — add it to any Flet page or layout just like any other control.

#### Minimal example

```python
import flet as ft
from fce_enhanced import EnhancedCodeEditor


def main(page: ft.Page):
    page.title = "My Editor"
    editor = EnhancedCodeEditor(expand=True)
    page.add(editor)


ft.run(main)
```

#### With configuration

```python
import flet as ft
import flet_code_editor as fce
from fce_enhanced import EnhancedCodeEditor


def main(page: ft.Page):
    page.title = "My Editor"

    def on_title_change(display_path, name, is_dirty):
        page.title = f"{name}{'*' if is_dirty else ''} — My Editor"
        page.update()

    editor = EnhancedCodeEditor(
        language=fce.CodeLanguage.JAVASCRIPT,
        value="console.log('hello');",
        code_theme=fce.CodeTheme.MONOKAI,
        on_title_change=on_title_change,
        ruff_on_save=False,  # disable ruff (only applies to Python files)
        expand=True,
    )
    page.add(editor)


ft.run(main)
```

#### Constructor parameters

| Parameter                     | Type           | Default          | Description                                |
| ----------------------------- | -------------- | ---------------- | ------------------------------------------ |
| `language`                    | `CodeLanguage` | `PYTHON`         | Initial syntax highlighting language       |
| `value`                       | `str`          | `"# New file\n"` | Initial editor content                     |
| `show_toolbar`                | `bool`         | `True`           | Show the file I/O toolbar                  |
| `show_status_bar`             | `bool`         | `True`           | Show the line/column status bar            |
| `register_keyboard_shortcuts` | `bool`         | `True`           | Register global keyboard shortcuts         |
| `autocomplete`                | `bool`         | `True`           | Enable autocomplete                        |
| `autocomplete_words`          | `list[str]`    | `None`           | Custom autocomplete suggestions            |
| `code_theme`                  | `CodeTheme`    | `ATOM_ONE_DARK`  | Syntax highlighting theme                  |
| `text_style`                  | `TextStyle`    | `None`           | Text style for editor content              |
| `gutter_style`                | `GutterStyle`  | `None`           | Style for the line number gutter           |
| `on_title_change`             | `callable`     | `None`           | Callback `(display_path, name, is_dirty)`  |
| `ruff_on_save`                | `bool`         | `True`           | Auto-format Python files with ruff on save |

Any additional keyword arguments are passed through to `ft.Column`.

#### Useful properties

```python
editor.value           # current editor content (str)
editor.current_path    # path of open file, or None
editor.dirty           # True if there are unsaved changes
editor.language        # current CodeLanguage
editor.code_editor     # the underlying fce.CodeEditor control
editor.search_bar      # the SearchReplaceBar control
```

## Features

- **File operations** — Open, Save, Save As, Close with unsaved-changes confirmation
- **Native file dialogs** — AppleScript dialogs on macOS, Flet FilePicker fallback elsewhere
- **Search & Replace** — Find toolbar with match counting, case sensitivity toggle, prev/next navigation
- **Command Palette** — Searchable list of all actions (Cmd+Shift+P / Ctrl+Shift+P)
- **Theme Selector** — 89 built-in syntax highlighting themes via a searchable dialog
- **Go to Line** — Jump to a specific line number (Cmd+G / Ctrl+G)
- **Read-Only Mode** — Toggle editing lock (Cmd+L / Ctrl+L)
- **Font Size Controls** — Increase/decrease font size (Cmd+= / Cmd+-)
- **Language Selector** — Choose syntax highlighting language from a searchable dialog; auto-detected on file open, and Save As defaults to the matching file extension
- **Language Detection** — Automatic syntax highlighting for 40+ file extensions
- **Dirty-File Tracking** — Visual indicator for unsaved changes
- **Diff Pane** — Toggleable unified diff view showing changes since last save, with green/red syntax coloring (Cmd+D / Ctrl+D)
- **Ruff on Save** — Auto-runs `ruff check --fix` and `ruff format` on Python files (requires ruff on PATH); toggleable from the toolbar
- **Status Bar** — Line, column, language, and selection info

### Keyboard shortcuts

| Action             | macOS | Windows / Linux |
| ------------------ | ----- | --------------- |
| Open File          | ⌘O    | Ctrl+O          |
| Save               | ⌘S    | Ctrl+S          |
| Save As            | ⇧⌘S   | Ctrl+Shift+S    |
| Close File         | ⌘W    | Ctrl+W          |
| Find               | ⌘F    | Ctrl+F          |
| Find and Replace   | ⌥⌘F   | Ctrl+H          |
| Toggle Diff        | ⌘D    | Ctrl+D          |
| Go to Line         | ⌘G    | Ctrl+G          |
| Toggle Read-Only   | ⌘L    | Ctrl+L          |
| Increase Font Size | ⌘+    | Ctrl++          |
| Decrease Font Size | ⌘-    | Ctrl+-          |
| Command Palette    | ⇧⌘P   | Ctrl+Shift+P    |
| Help               | F1    | F1              |
| Close Search Bar   | Esc   | Esc             |

## License

MIT

## Development

Code style is enforced with [ruff](https://docs.astral.sh/ruff/) via pre-commit hooks:

```bash
pre-commit run --all-files
```

Run tests:

```bash
pytest
```

## Built With

- [Flet](https://flet.dev) — Build multi-platform apps in Python powered by Flutter
- [flet-code-editor](https://pypi.org/project/flet-code-editor/) — Code editor control for Flet with syntax highlighting
- [ruff](https://docs.astral.sh/ruff/) — Fast Python linter and formatter
