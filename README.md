# flet-code-editor-enhanced

An enhanced [Flet](https://flet.dev) CodeEditor control with file open/save/save-as/close capabilities.

Built on top of [`flet-code-editor`](https://pypi.org/project/flet-code-editor/), adding a toolbar for common file operations and native macOS file dialogs.

## Install

```bash
uv add flet-code-editor-enhanced
```

## Usage

### Run as a standalone app

```bash
flet-code-editor-enhanced
```

Or:

```bash
flet run src/flet_code_editor_enhanced/editor.py
```

### Import in your own Flet app

```python
from flet_code_editor_enhanced.editor import main
from flet_code_editor_enhanced.editor import language_for_path, EXTENSION_TO_LANGUAGE
from flet_code_editor_enhanced.file_dialog import open_file, save_file
```

## Features

- **Open** files with a native macOS file dialog (falls back to Flet's FilePicker on other platforms)
- **Save** the current file (Ctrl+S style workflow)
- **Save As** to a new location
- **Close** the current file with unsaved-changes confirmation
- Automatic language detection from file extension (40+ languages)
- Dirty-file indicator in the title bar
- Selection and caret position display

## License

MIT

## Development

Clone the repo and install dependencies including dev tools:

```bash
git clone https://github.com/yourusername/flet-code-editor-enhanced
cd flet-code-editor-enhanced
uv sync
pre-commit install
```

Code style is enforced with [ruff](https://docs.astral.sh/ruff/). The pre-commit hook will run automatically on each commit, or you can run it manually:

```bash
pre-commit run --all-files
```
