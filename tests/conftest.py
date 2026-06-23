"""Shared test fixtures."""

from pathlib import Path
from unittest.mock import MagicMock

from flet.components.component import Renderer
import flet.controls.context as ctxmod
import pytest


@pytest.fixture
def fake_page():
    """Bind a mock page to the Flet context so components can render headless."""
    page = MagicMock()
    page.session = MagicMock()
    token = ctxmod._context_page.set(page)
    try:
        yield page
    finally:
        ctxmod._context_page.reset(token)


@pytest.fixture
def render_component(fake_page):
    """Return a helper that executes a component body and returns its control tree.

    Usage::

        tree, comp = render_component(MyComponent, some_prop=1)

    The component body runs through Flet's Renderer (so all hooks execute), but
    effects are not scheduled — only the synchronous render output is returned.
    """

    def _render(fn, **kwargs):
        comp = Renderer().render(lambda: fn(**kwargs))
        comp._state.mounted = True
        comp._state.hook_cursor = 0
        tree = Renderer(comp).render(comp.fn, *comp.args, **comp.kwargs)
        return tree, comp

    return _render


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
