#!/usr/bin/env python3
"""Test Python code snippets extracted from documentation.

Verifies that all Python code blocks in the docs are:
1. Syntactically valid Python
2. Use correct imports (modules and names exist)
3. Call ux3270 APIs with valid constructor/method signatures

Run with:  pytest tests/test_doc_snippets.py -v
Standalone: python tests/test_doc_snippets.py
"""

import ast
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = ROOT / "docs"
README = ROOT / "README.md"


def extract_python_snippets(path: Path) -> list[tuple[int, str]]:
    """Extract ``python code blocks from a markdown file."""
    text = path.read_text()
    snippets: list[tuple[int, str]] = []
    in_block = False
    block_lines: list[str] = []
    block_start = 0

    for i, line in enumerate(text.splitlines(), 1):
        if line.strip().startswith("```python"):
            in_block = True
            block_lines = []
            block_start = i + 1
        elif in_block and line.strip().startswith("```"):
            in_block = False
            code = "\n".join(block_lines)
            if code.strip():
                snippets.append((block_start, code))
        elif in_block:
            block_lines.append(line)

    return snippets


def collect_all_snippets() -> list[tuple[str, int, str]]:
    """Collect all Python snippets from markdown files."""
    snippets: list[tuple[str, int, str]] = []
    md_files = sorted(DOCS_DIR.rglob("*.md"))
    if README.exists():
        md_files.append(README)
    for md_file in md_files:
        rel = str(md_file.relative_to(ROOT))
        for lineno, code in extract_python_snippets(md_file):
            snippets.append((rel, lineno, code))
    return snippets


ALL_SNIPPETS = collect_all_snippets()


def _first_code_line(code: str) -> str:
    """Return the first non-blank, non-comment line."""
    for line in code.strip().splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            return stripped
    return ""


def _has_imports(code: str) -> bool:
    """True if the snippet starts with import statements."""
    first = _first_code_line(code)
    return first.startswith("from ") or first.startswith("import ")


EXECUTABLE_SNIPPETS = [s for s in ALL_SNIPPETS if _has_imports(s[2])]


class _FakeDB:
    """Stub for ``db`` references in doc examples.

    Any attribute access returns a callable that returns an empty list,
    so patterns like ``for item in db.get_all():`` work without error.
    """

    def __getattr__(self, _name: str):
        return lambda *_a, **_kw: []


@pytest.mark.parametrize(
    "snippet",
    ALL_SNIPPETS,
    ids=[f"{s[0]}:{s[1]}" for s in ALL_SNIPPETS],
)
def test_snippet_syntax(snippet):
    """Every Python snippet in the docs must be syntactically valid."""
    path, lineno, code = snippet
    try:
        ast.parse(code)
    except SyntaxError as e:
        pytest.fail(f"{path}:{lineno}: {e}")


@pytest.mark.parametrize(
    "snippet",
    EXECUTABLE_SNIPPETS,
    ids=[f"{s[0]}:{s[1]}" for s in EXECUTABLE_SNIPPETS],
)
def test_snippet_executes(snippet):
    """Snippets with imports must execute with mocked terminal I/O."""
    path, lineno, code = snippet

    # Simulate user pressing F3 (cancel) so dialog loops exit immediately
    mock_result = {"aid": "F3", "fields": {}, "current_field": None, "key": ""}

    # Stubs for external names that doc examples reference but don't define
    exec_globals: dict = {
        "__builtins__": __builtins__,
        "db": _FakeDB(),
        "edit_item": lambda *a, **k: None,
        "delete_item": lambda *a, **k: None,
        "display_item": lambda *a, **k: None,
        "add_new_item": lambda *a, **k: None,
        "confirm_delete": lambda: True,
    }

    with patch("ux3270.panel.screen.Screen.show", return_value=mock_result):
        try:
            exec(compile(code, f"{path}:{lineno}", "exec"), exec_globals)
        except Exception as e:
            pytest.fail(f"{path}:{lineno}: {type(e).__name__}: {e}")


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
