"""Language detection from file extensions."""

from pathlib import Path

import flet_code_editor as fce

# Map file extensions to CodeLanguage enum values.
EXTENSION_TO_LANGUAGE: dict[str, fce.CodeLanguage] = {
    ".py": fce.CodeLanguage.PYTHON,
    ".js": fce.CodeLanguage.JAVASCRIPT,
    ".jsx": fce.CodeLanguage.JAVASCRIPT,
    ".ts": fce.CodeLanguage.TYPESCRIPT,
    ".tsx": fce.CodeLanguage.TYPESCRIPT,
    ".html": fce.CodeLanguage.HTMLBARS,
    ".css": fce.CodeLanguage.CSS,
    ".scss": fce.CodeLanguage.SCSS,
    ".json": fce.CodeLanguage.JSON,
    ".xml": fce.CodeLanguage.XML,
    ".yaml": fce.CodeLanguage.YAML,
    ".yml": fce.CodeLanguage.YAML,
    ".toml": fce.CodeLanguage.INI,
    ".md": fce.CodeLanguage.MARKDOWN,
    ".txt": fce.CodeLanguage.PLAINTEXT,
    ".sh": fce.CodeLanguage.BASH,
    ".bash": fce.CodeLanguage.BASH,
    ".zsh": fce.CodeLanguage.BASH,
    ".rs": fce.CodeLanguage.RUST,
    ".go": fce.CodeLanguage.GO,
    ".java": fce.CodeLanguage.JAVA,
    ".kt": fce.CodeLanguage.KOTLIN,
    ".c": fce.CodeLanguage.CPP,
    ".cpp": fce.CodeLanguage.CPP,
    ".h": fce.CodeLanguage.CPP,
    ".hpp": fce.CodeLanguage.CPP,
    ".cs": fce.CodeLanguage.CS,
    ".rb": fce.CodeLanguage.RUBY,
    ".php": fce.CodeLanguage.PHP,
    ".sql": fce.CodeLanguage.SQL,
    ".r": fce.CodeLanguage.R,
    ".swift": fce.CodeLanguage.SWIFT,
    ".dart": fce.CodeLanguage.DART,
    ".lua": fce.CodeLanguage.LUA,
    ".vim": fce.CodeLanguage.VIM,
    ".ini": fce.CodeLanguage.INI,
    ".cfg": fce.CodeLanguage.INI,
    ".makefile": fce.CodeLanguage.MAKEFILE,
    ".dockerfile": fce.CodeLanguage.DOCKERFILE,
    ".scala": fce.CodeLanguage.SCALA,
    ".ex": fce.CodeLanguage.ELIXIR,
    ".exs": fce.CodeLanguage.ELIXIR,
    ".erl": fce.CodeLanguage.ERLANG,
    ".hs": fce.CodeLanguage.HASKELL,
    ".clj": fce.CodeLanguage.CLOJURE,
    ".gradle": fce.CodeLanguage.GRADLE,
    ".graphql": fce.CodeLanguage.GRAPHQL,
    ".vue": fce.CodeLanguage.VUE,
}


# Reverse map: first extension found for each language (prefer shorter/canonical ones).
LANGUAGE_TO_EXTENSION: dict[fce.CodeLanguage, str] = {}
for _ext, _lang in EXTENSION_TO_LANGUAGE.items():
    if _lang not in LANGUAGE_TO_EXTENSION:
        LANGUAGE_TO_EXTENSION[_lang] = _ext


def extension_for_language(lang: fce.CodeLanguage) -> str:
    """Return the canonical file extension for a CodeLanguage (e.g. '.py', '.json').

    Returns '.txt' if no mapping exists.
    """
    return LANGUAGE_TO_EXTENSION.get(lang, ".txt")


def language_for_path(path: str | None) -> fce.CodeLanguage:
    """Detect CodeLanguage from a file path's extension.

    Args:
        path: File path string, or None for untitled files.

    Returns:
        Matching CodeLanguage, or PLAINTEXT if unrecognised.
    """
    if path is None:
        return fce.CodeLanguage.PLAINTEXT
    ext = Path(path).suffix.lower()
    return EXTENSION_TO_LANGUAGE.get(ext, fce.CodeLanguage.PLAINTEXT)
