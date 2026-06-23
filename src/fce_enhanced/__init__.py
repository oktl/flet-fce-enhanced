"""Enhanced Flet CodeEditor with file open/save/save-as/close capabilities."""

from importlib.metadata import version

from fce_enhanced.diff_pane import DiffPane, compute_unified_diff
from fce_enhanced.editor import EditorHandle, EnhancedCodeEditor, main, run
from fce_enhanced.file_dialog import open_file, save_file
from fce_enhanced.languages import EXTENSION_TO_LANGUAGE, language_for_path
from fce_enhanced.search import SearchReplaceBar, compute_matches
from fce_enhanced.themes import DEFAULT_THEME, THEMES, theme_display_name

__version__ = version("fce-enhanced")

__all__ = [
    "DEFAULT_THEME",
    "DiffPane",
    "EXTENSION_TO_LANGUAGE",
    "EditorHandle",
    "EnhancedCodeEditor",
    "SearchReplaceBar",
    "THEMES",
    "compute_matches",
    "compute_unified_diff",
    "language_for_path",
    "main",
    "open_file",
    "run",
    "save_file",
    "theme_display_name",
]
