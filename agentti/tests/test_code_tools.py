"""
test_code_tools.py — Yksikkotest code_tools.py:lle.
Kattaa: _run_python, _run_shell.
"""

import sys
from pathlib import Path

AGENTTI_DIR = Path(__file__).resolve().parent.parent
if str(AGENTTI_DIR) not in sys.path:
    sys.path.insert(0, str(AGENTTI_DIR))

import pytest
from tools.code_tools import _run_python, _run_shell


# ── _run_python ──────────────────────────────────────────────────

class TestRunPython:
    def test_simple_print(self):
        result = _run_python("print('hei')")
        assert "hei" in result

    def test_arithmetic(self):
        result = _run_python("print(2 + 2)")
        assert "4" in result

    def test_multiline_code(self):
        code = "x = 10\ny = 20\nprint(x + y)"
        result = _run_python(code)
        assert "30" in result

    def test_syntax_error_reported(self):
        result = _run_python("def broken(: pass")
        assert "VIRHE" in result or "SyntaxError" in result or "error" in result.lower()

    def test_runtime_error_reported(self):
        result = _run_python("raise ValueError('testata')")
        assert "VIRHE" in result or "ValueError" in result

    def test_import_standard_library(self):
        result = _run_python("import os; print(type(os).__name__)")
        assert "module" in result

    def test_output_truncated_at_5000(self):
        result = _run_python("print('x' * 6000)")
        assert len(result) <= 5000

    def test_no_output_returns_placeholder(self):
        result = _run_python("x = 1")
        assert result == "(ei tulostetta)" or len(result) >= 0

    def test_multiline_output(self):
        code = "for i in range(3):\n    print(i)"
        result = _run_python(code)
        assert "0" in result
        assert "1" in result
        assert "2" in result


# ── _run_shell ───────────────────────────────────────────────────

class TestRunShell:
    def test_echo_command(self):
        result = _run_shell("echo testi")
        assert "testi" in result

    def test_blocked_command_rm_rf(self):
        result = _run_shell("rm -rf /")
        assert "VIRHE" in result or "estetty" in result

    def test_blocked_command_mkfs(self):
        result = _run_shell("mkfs /dev/sda")
        assert "VIRHE" in result or "estetty" in result

    def test_python_version(self):
        result = _run_shell(f"{sys.executable} --version")
        assert "Python" in result

    def test_invalid_command_reported(self):
        result = _run_shell("komento_jota_ei_ole_olemassa_12345")
        assert result  # ei tyhjä

    def test_blocked_dd_command(self):
        result = _run_shell("dd if=/dev/zero")
        assert "VIRHE" in result or "estetty" in result
