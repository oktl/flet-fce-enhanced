"""Enhanced Flet CodeEditor with file open/save/save-as/close capabilities."""

from flet_code_editor_enhanced.editor import EnhancedCodeEditor, main, run
from flet_code_editor_enhanced.file_dialog import open_file, save_file
from flet_code_editor_enhanced.languages import EXTENSION_TO_LANGUAGE, language_for_path
from flet_code_editor_enhanced.search import SearchReplaceBar

__all__ = [
    "EnhancedCodeEditor",
    "EXTENSION_TO_LANGUAGE",
    "SearchReplaceBar",
    "language_for_path",
    "main",
    "open_file",
    "run",
    "save_file",
]
