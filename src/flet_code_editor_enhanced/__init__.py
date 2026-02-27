"""Enhanced Flet CodeEditor with file open/save/save-as/close capabilities."""

from flet_code_editor_enhanced.editor import (
    EXTENSION_TO_LANGUAGE,
    language_for_path,
    main,
    run,
)
from flet_code_editor_enhanced.file_dialog import open_file, save_file

__all__ = [
    "EXTENSION_TO_LANGUAGE",
    "language_for_path",
    "main",
    "open_file",
    "run",
    "save_file",
]
