"""macOS native open/save file dialogs.

Uses AppleScript's `choose file` / `choose file name` dialogs via osascript.
Falls back to Flet's FilePicker on non-macOS platforms.
"""

import asyncio
import platform
import subprocess

from loguru import logger

from fce_enhanced.languages import EXTENSION_TO_LANGUAGE

IS_MACOS = platform.system() == "Darwin"


def _escape_applescript(s: str) -> str:
    """Escape a string for safe interpolation into AppleScript."""
    return s.replace("\\", "\\\\").replace('"', '\\"')


# Derived from EXTENSION_TO_LANGUAGE, plus extras not tied to a CodeLanguage.
_TEXT_EXTENSIONS = sorted(
    {ext.lstrip(".") for ext in EXTENSION_TO_LANGUAGE}
    | {"conf", "env", "csv", "gitignore"}
)


def _open_file_macos(prompt: str = "Open File") -> str | None:
    """Open native macOS file picker dialog via AppleScript.

    Args:
        prompt: Prompt message to display in the dialog.

    Returns:
        POSIX path string of selected file, or None if cancelled/error.
    """
    try:
        safe_prompt = _escape_applescript(prompt)
        type_list = ", ".join(f'"{ext}"' for ext in _TEXT_EXTENSIONS)
        script = (
            f'POSIX path of (choose file with prompt "{safe_prompt}" '
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
        safe_prompt = _escape_applescript(prompt)
        safe_name = _escape_applescript(default_name)
        script = (
            f'POSIX path of (choose file name with prompt "{safe_prompt}" '
            f'default name "{safe_name}")'
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

    files = await ft.FilePicker().pick_files(dialog_title=prompt)
    if files:
        return files[0].path
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

    return await ft.FilePicker().save_file(dialog_title=prompt, file_name=default_name)
