"""macOS native open/save file dialogs.

Uses AppleScript's `choose file` / `choose file name` dialogs via osascript.
Falls back to Flet's FilePicker on non-macOS platforms.
"""

import asyncio
import platform
import subprocess

from loguru import logger

IS_MACOS = platform.system() == "Darwin"

# Common text/code file extensions for the open dialog filter.
_TEXT_EXTENSIONS = [
    "py",
    "js",
    "ts",
    "jsx",
    "tsx",
    "html",
    "css",
    "scss",
    "json",
    "xml",
    "yaml",
    "yml",
    "toml",
    "md",
    "txt",
    "sh",
    "bash",
    "zsh",
    "rs",
    "go",
    "java",
    "kt",
    "c",
    "cpp",
    "h",
    "hpp",
    "cs",
    "rb",
    "php",
    "sql",
    "r",
    "swift",
    "dart",
    "lua",
    "vim",
    "conf",
    "cfg",
    "ini",
    "env",
    "csv",
    "makefile",
    "dockerfile",
    "gitignore",
]


def _open_file_macos(prompt: str = "Open File") -> str | None:
    """Open native macOS file picker dialog via AppleScript.

    Args:
        prompt: Prompt message to display in the dialog.

    Returns:
        POSIX path string of selected file, or None if cancelled/error.
    """
    try:
        type_list = ", ".join(f'"{ext}"' for ext in _TEXT_EXTENSIONS)
        script = (
            f'POSIX path of (choose file with prompt "{prompt}" '
            f"of type {{{type_list}}})"
        )
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=300,
        )

        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()

        return None

    except subprocess.TimeoutExpired:
        logger.warning("File open dialog timed out")
        return None
    except Exception as e:
        logger.error(f"Error opening file dialog: {e}")
        return None


def _save_file_macos(
    prompt: str = "Save File", default_name: str = "untitled.txt"
) -> str | None:
    """Open native macOS save-file dialog via AppleScript.

    Args:
        prompt: Prompt message to display in the dialog.
        default_name: Default filename suggestion.

    Returns:
        POSIX path string of chosen save location, or None if cancelled/error.
    """
    try:
        script = (
            f'POSIX path of (choose file name with prompt "{prompt}" '
            f'default name "{default_name}")'
        )
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=300,
        )

        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()

        return None

    except subprocess.TimeoutExpired:
        logger.warning("File save dialog timed out")
        return None
    except Exception as e:
        logger.error(f"Error opening save dialog: {e}")
        return None


async def open_file(prompt: str = "Open File") -> str | None:
    """Open a file picker dialog appropriate for the current platform.

    On macOS, uses AppleScript's `choose file` with text/code extension filter.
    On other platforms, falls back to Flet's built-in FilePicker.

    Args:
        prompt: Prompt message to display in the dialog.

    Returns:
        Path string of selected file, or None if cancelled/error.
    """
    if IS_MACOS:
        return await asyncio.to_thread(_open_file_macos, prompt)

    import flet as ft

    picker = ft.FilePicker()
    result = await picker.pick_files_async(dialog_title=prompt)
    if result and result.files:
        return result.files[0].path
    return None


async def save_file(
    prompt: str = "Save File", default_name: str = "untitled.txt"
) -> str | None:
    """Open a save-file dialog appropriate for the current platform.

    On macOS, uses AppleScript's `choose file name`.
    On other platforms, falls back to Flet's built-in FilePicker.

    Args:
        prompt: Prompt message to display in the dialog.
        default_name: Default filename suggestion.

    Returns:
        Path string of chosen save location, or None if cancelled/error.
    """
    if IS_MACOS:
        return await asyncio.to_thread(_save_file_macos, prompt, default_name)

    import flet as ft

    picker = ft.FilePicker()
    result = await picker.save_file_async(dialog_title=prompt, file_name=default_name)
    return result
