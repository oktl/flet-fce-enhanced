"""Shared test fixtures."""

from pathlib import Path

import pytest


@pytest.fixture
def tmp_py_file(tmp_path: Path) -> Path:
    """Create a temporary .py file with known content."""
    p = tmp_path / "example.py"
    p.write_text("print('hello')\n", encoding="utf-8")
    return p


@pytest.fixture
def tmp_js_file(tmp_path: Path) -> Path:
    """Create a temporary .js file with known content."""
    p = tmp_path / "example.js"
    p.write_text("console.log('hello');\n", encoding="utf-8")
    return p


@pytest.fixture
def tmp_text_file(tmp_path: Path) -> Path:
    """Create a temporary .txt file with known content."""
    p = tmp_path / "example.txt"
    p.write_text("hello world\n", encoding="utf-8")
    return p
