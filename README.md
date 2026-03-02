# fce-enhanced

An enhanced [Flet](https://flet.dev) CodeEditor control with file open/save/save-as/close/search and replace capabilities.

Built on top of [`flet-code-editor`](https://pypi.org/project/flet-code-editor/), adding a toolbar for common file operations and native macOS file dialogs.

## Install

```bash
uv add fce-enhanced
```

## Usage

### Run as a standalone app

```bash
fce-enhanced
```

Or:

```bash
flet run src/fce_enhanced/editor.py
```

### Import in your own Flet app

```python
from fce_enhanced.editor import main
from fce_enhanced.editor import language_for_path, EXTENSION_TO_LANGUAGE
from fce_enhanced.file_dialog import open_file, save_file
```

## Features

- **Open** files with a native macOS file dialog (falls back to Flet's FilePicker on other platforms)
- **Save** the current file (Ctrl+S style workflow)
- **Save As** to a new location
- **Close** the current file with unsaved-changes confirmation
- Automatic language detection from file extension (40+ languages)
- Dirty-file indicator in the title bar
- **Search & Replace** with a find toolbar
- **Theme Selector** — choose from 89 built-in syntax highlighting themes via a searchable palette dialog
- **Ruff on Save** — automatically runs `ruff check --fix` and `ruff format` when saving Python files (requires ruff on PATH)
- Selection and caret position display

## License

MIT

## Development

Clone the repo and install dependencies including dev tools:

```bash
git clone https://github.com/yourusername/fce-enhanced
cd fce-enhanced
uv sync
pre-commit install
```

Code style is enforced with [ruff](https://docs.astral.sh/ruff/). The pre-commit hook will run automatically on each commit, or you can run it manually:

```bash
pre-commit run --all-files
```
