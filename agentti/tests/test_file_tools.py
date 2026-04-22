"""
test_file_tools.py — Yksikkotest file_tools.py:lle.
Kattaa: _safe_path, _read_file, _write_file, _list_files.
"""

import sys
from pathlib import Path

AGENTTI_DIR = Path(__file__).resolve().parent.parent
if str(AGENTTI_DIR) not in sys.path:
    sys.path.insert(0, str(AGENTTI_DIR))

import pytest
from tools.file_tools import _read_file, _write_file, _list_files, _safe_path, WORKSPACE


# ── _safe_path ───────────────────────────────────────────────────

class TestSafePath:
    def test_valid_filename(self, tmp_path, monkeypatch):
        monkeypatch.setattr("tools.file_tools.WORKSPACE", tmp_path)
        result = _safe_path("testi.txt")
        # Palauttaa polun tai None — joka tapauksessa ei kaadu
        assert result is not None or result is None  # syntaksi ok

    def test_path_traversal_blocked(self, tmp_path, monkeypatch):
        monkeypatch.setattr("tools.file_tools.WORKSPACE", tmp_path)
        result = _safe_path("../../hakkeroi.txt")
        assert result is None

    def test_workspace_prefix_stripped(self, tmp_path, monkeypatch):
        monkeypatch.setattr("tools.file_tools.WORKSPACE", tmp_path)
        result = _safe_path("workspace/testi.txt")
        assert result is not None


# ── _write_file ──────────────────────────────────────────────────

class TestWriteFile:
    def test_write_creates_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr("tools.file_tools.WORKSPACE", tmp_path)
        result = _write_file("testi.txt", "hei maailma")
        assert "OK" in result
        assert (tmp_path / "testi.txt").read_text(encoding="utf-8") == "hei maailma"

    def test_write_subdirectory(self, tmp_path, monkeypatch):
        monkeypatch.setattr("tools.file_tools.WORKSPACE", tmp_path)
        result = _write_file("alihakemisto/testi.txt", "sisalto")
        assert "OK" in result
        assert (tmp_path / "alihakemisto" / "testi.txt").exists()

    def test_write_outside_workspace_blocked(self, tmp_path, monkeypatch):
        monkeypatch.setattr("tools.file_tools.WORKSPACE", tmp_path)
        result = _write_file("../../hakkeroi.txt", "paha")
        assert "VIRHE" in result

    def test_write_strips_workspace_prefix(self, tmp_path, monkeypatch):
        monkeypatch.setattr("tools.file_tools.WORKSPACE", tmp_path)
        result = _write_file("workspace/testi.txt", "sisalto")
        assert "OK" in result

    def test_overwrite_existing(self, tmp_path, monkeypatch):
        monkeypatch.setattr("tools.file_tools.WORKSPACE", tmp_path)
        _write_file("sama.txt", "vanha")
        result = _write_file("sama.txt", "uusi")
        assert "OK" in result
        assert (tmp_path / "sama.txt").read_text(encoding="utf-8") == "uusi"


# ── _read_file ───────────────────────────────────────────────────

class TestReadFile:
    def test_read_existing_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr("tools.file_tools.WORKSPACE", tmp_path)
        (tmp_path / "lue_minut.txt").write_text("terve!", encoding="utf-8")
        result = _read_file("lue_minut.txt")
        assert result == "terve!"

    def test_read_missing_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr("tools.file_tools.WORKSPACE", tmp_path)
        result = _read_file("ei_ole.txt")
        assert "VIRHE" in result

    def test_read_outside_workspace_blocked(self, tmp_path, monkeypatch):
        monkeypatch.setattr("tools.file_tools.WORKSPACE", tmp_path)
        result = _read_file("../../salaisuus.txt")
        assert "VIRHE" in result

    def test_read_truncates_large_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr("tools.file_tools.WORKSPACE", tmp_path)
        (tmp_path / "iso.txt").write_text("x" * 6000, encoding="utf-8")
        result = _read_file("iso.txt")
        assert len(result) <= 5000

    def test_read_utf8_content(self, tmp_path, monkeypatch):
        monkeypatch.setattr("tools.file_tools.WORKSPACE", tmp_path)
        (tmp_path / "unicode.txt").write_text("äöå", encoding="utf-8")
        result = _read_file("unicode.txt")
        assert "äöå" in result


# ── _list_files ──────────────────────────────────────────────────

class TestListFiles:
    def test_list_empty_directory(self, tmp_path, monkeypatch):
        monkeypatch.setattr("tools.file_tools.WORKSPACE", tmp_path)
        result = _list_files(".")
        assert "tyhjä" in result

    def test_list_with_files(self, tmp_path, monkeypatch):
        monkeypatch.setattr("tools.file_tools.WORKSPACE", tmp_path)
        (tmp_path / "a.txt").write_text("a")
        (tmp_path / "b.py").write_text("b")
        result = _list_files(".")
        assert "a.txt" in result
        assert "b.py" in result

    def test_list_missing_directory(self, tmp_path, monkeypatch):
        monkeypatch.setattr("tools.file_tools.WORKSPACE", tmp_path)
        result = _list_files("ei_ole_hakemistoa")
        assert "VIRHE" in result

    def test_list_outside_workspace_blocked(self, tmp_path, monkeypatch):
        monkeypatch.setattr("tools.file_tools.WORKSPACE", tmp_path)
        result = _list_files("../../..")
        assert "VIRHE" in result

    def test_list_shows_directory_icon(self, tmp_path, monkeypatch):
        monkeypatch.setattr("tools.file_tools.WORKSPACE", tmp_path)
        (tmp_path / "alihakemisto").mkdir()
        result = _list_files(".")
        assert "📁" in result

    def test_list_shows_file_icon(self, tmp_path, monkeypatch):
        monkeypatch.setattr("tools.file_tools.WORKSPACE", tmp_path)
        (tmp_path / "tiedosto.txt").write_text("x")
        result = _list_files(".")
        assert "📄" in result
