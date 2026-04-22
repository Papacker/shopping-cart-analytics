"""
test_tester_agent.py — Yksikkotest tester_agent.py:lle.
Kattaa: _resolve_path, _run_test_file seka check_syntax, run_and_assert
        ja muiden tyokalujen yksityiset vastineet.
"""

import sys
from pathlib import Path

AGENTTI_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = AGENTTI_DIR.parent
if str(AGENTTI_DIR) not in sys.path:
    sys.path.insert(0, str(AGENTTI_DIR))

import pytest
from tools.tester_agent import (
    _resolve_path,
    _run_cmd,
    _run_test_file,
)


# ── _resolve_path ────────────────────────────────────────────────

class TestResolvePath:
    def test_project_root_relative(self):
        result = _resolve_path("agentti/crew.py")
        assert result is not None
        assert result.exists()

    def test_absolute_path(self):
        target = AGENTTI_DIR / "crew.py"
        result = _resolve_path(str(target))
        assert result is not None
        assert result.exists()

    def test_nonexistent_path_returns_none(self):
        result = _resolve_path("ei/ole/tiedostoa_abc123.py")
        assert result is None

    def test_workspace_relative(self, tmp_path, monkeypatch):
        monkeypatch.setattr("tools.tester_agent.WORKSPACE", tmp_path)
        (tmp_path / "testi.py").write_text("x = 1")
        result = _resolve_path("testi.py")
        assert result is not None

    def test_workspace_prefix_stripped(self, tmp_path, monkeypatch):
        monkeypatch.setattr("tools.tester_agent.WORKSPACE", tmp_path)
        (tmp_path / "testi.py").write_text("x = 1")
        result = _resolve_path("workspace/testi.py")
        assert result is not None

    def test_init_py_found(self):
        result = _resolve_path("agentti/tools/__init__.py")
        assert result is not None


# ── _run_cmd ─────────────────────────────────────────────────────

class TestRunCmd:
    def test_successful_command(self):
        out, code = _run_cmd([sys.executable, "-c", "print('ok')"])
        assert "ok" in out
        assert code == 0

    def test_failing_command(self):
        out, code = _run_cmd([sys.executable, "-c", "import sys; sys.exit(1)"])
        assert code != 0

    def test_timeout(self):
        out, code = _run_cmd(
            [sys.executable, "-c", "import time; time.sleep(10)"],
            timeout=1
        )
        assert "Aikakatkaisu" in out or code == -1


# ── _run_test_file ───────────────────────────────────────────────

class TestRunTestFile:
    def test_returns_markdown_report(self):
        result = _run_test_file("agentti/tools/__init__.py")
        assert "# Testitulokset" in result
        assert "## 1. Syntaksi" in result
        assert "## 2. Pylint" in result
        assert "## 3. Pytest" in result
        assert "## 4. Yhteenveto" in result

    def test_missing_file_returns_error(self):
        result = _run_test_file("ei_ole_abc123.py")
        assert "VIRHE" in result

    def test_valid_file_syntax_ok(self):
        result = _run_test_file("agentti/tools/__init__.py")
        assert "✅ OK" in result

    def test_report_contains_date(self):
        result = _run_test_file("agentti/tools/__init__.py")
        assert "Päiväys" in result or "202" in result

    def test_report_contains_filepath(self):
        result = _run_test_file("agentti/tools/__init__.py")
        assert "__init__" in result

    def test_pylint_score_in_report(self):
        result = _run_test_file("agentti/tools/__init__.py")
        assert "rated at" in result or "pylint" in result.lower()

    def test_yhteenveto_table(self):
        result = _run_test_file("agentti/tools/__init__.py")
        assert "| Syntaksi |" in result
        assert "| Pylint" in result

    def test_file_tools_test(self):
        result = _run_test_file("agentti/tools/file_tools.py")
        assert "# Testitulokset" in result

    def test_code_tools_test(self):
        result = _run_test_file("agentti/tools/code_tools.py")
        assert "# Testitulokset" in result
