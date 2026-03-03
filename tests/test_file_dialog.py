"""Tests for fce_enhanced.file_dialog."""

import subprocess
from unittest.mock import AsyncMock, patch

import pytest

from fce_enhanced.file_dialog import (
    _open_file_macos,
    _save_file_macos,
    open_file,
    save_file,
)

# --- _open_file_macos ---


def test_open_file_macos_success():
    mock_result = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="/tmp/test.py\n", stderr=""
    )
    with patch("fce_enhanced.file_dialog.subprocess.run", return_value=mock_result):
        assert _open_file_macos("Open") == "/tmp/test.py"


def test_open_file_macos_cancel():
    mock_result = subprocess.CompletedProcess(
        args=[], returncode=1, stdout="", stderr=""
    )
    with patch("fce_enhanced.file_dialog.subprocess.run", return_value=mock_result):
        assert _open_file_macos("Open") is None


def test_open_file_macos_timeout():
    with patch(
        "fce_enhanced.file_dialog.subprocess.run",
        side_effect=subprocess.TimeoutExpired(cmd="osascript", timeout=300),
    ):
        assert _open_file_macos("Open") is None


def test_open_file_macos_error():
    with patch(
        "fce_enhanced.file_dialog.subprocess.run",
        side_effect=OSError("something went wrong"),
    ):
        assert _open_file_macos("Open") is None


# --- _save_file_macos ---


def test_save_file_macos_success():
    mock_result = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="/tmp/output.py\n", stderr=""
    )
    with patch("fce_enhanced.file_dialog.subprocess.run", return_value=mock_result):
        assert _save_file_macos("Save", "output.py") == "/tmp/output.py"


def test_save_file_macos_cancel():
    mock_result = subprocess.CompletedProcess(
        args=[], returncode=1, stdout="", stderr=""
    )
    with patch("fce_enhanced.file_dialog.subprocess.run", return_value=mock_result):
        assert _save_file_macos("Save", "output.py") is None


def test_save_file_macos_timeout():
    with patch(
        "fce_enhanced.file_dialog.subprocess.run",
        side_effect=subprocess.TimeoutExpired(cmd="osascript", timeout=300),
    ):
        assert _save_file_macos("Save", "output.py") is None


# --- async wrappers ---


@pytest.mark.asyncio
async def test_open_file_async_delegates_to_thread():
    with (
        patch("fce_enhanced.file_dialog.IS_MACOS", True),
        patch(
            "fce_enhanced.file_dialog.asyncio.to_thread",
            new_callable=AsyncMock,
            return_value="/tmp/test.py",
        ) as mock_to_thread,
    ):
        result = await open_file("Open")
        mock_to_thread.assert_awaited_once_with(_open_file_macos, "Open")
        assert result == "/tmp/test.py"


@pytest.mark.asyncio
async def test_save_file_async_delegates_to_thread():
    with (
        patch("fce_enhanced.file_dialog.IS_MACOS", True),
        patch(
            "fce_enhanced.file_dialog.asyncio.to_thread",
            new_callable=AsyncMock,
            return_value="/tmp/out.py",
        ) as mock_to_thread,
    ):
        result = await save_file("Save", "out.py")
        mock_to_thread.assert_awaited_once_with(_save_file_macos, "Save", "out.py")
        assert result == "/tmp/out.py"
