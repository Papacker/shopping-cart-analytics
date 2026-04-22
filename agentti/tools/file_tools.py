"""
file_tools.py - Tiedosto-operaatiot agentin tyotilassa projektin sisalla.
"""

import os
from pathlib import Path
from crewai.tools import tool

# Tunnistetaan projektin juuri ja tyotila
PROJECT_ROOT = Path(__file__).resolve().parent.parent
WORKSPACE = PROJECT_ROOT / "workspace"
WORKSPACE.mkdir(parents=True, exist_ok=True)


def _safe_path(path_str: str) -> Path | None:
    """
    Palauttaa validoidun polun tyotilan sisalla.
    Estaa agenttia karkaamasta tyotilan ulkopuolelle (esim. ../../).
    """
    if path_str.startswith("workspace/") or path_str.startswith("workspace\\"):
        path_str = path_str[len("workspace/"):]
    try:
        requested_path = (WORKSPACE / path_str).resolve()
        if WORKSPACE.resolve() in requested_path.parents or requested_path == WORKSPACE.resolve():
            return requested_path
    except OSError:
        return None
    return None


# ── Yksityiset toteutukset (kutsuttavissa suoraan testeista) ──────


def _read_file(path: str) -> str:
    """Lukee tiedoston tyotilasta."""
    full_path = _safe_path(path)
    if not full_path or not full_path.is_file():
        return f"VIRHE: Tiedostoa '{path}' ei loydy tai se on tyotilan ulkopuolella."
    try:
        content = full_path.read_text(encoding="utf-8")
        return content[:5000] if len(content) > 5000 else content
    except OSError as e:
        return f"VIRHE luettaessa tiedostoa: {e}"


def _write_file(path: str, content: str) -> str:
    """Kirjoittaa tiedoston tyotilaan."""
    full_path = _safe_path(path)
    if not full_path:
        return "VIRHE: Polku on tyotilan ulkopuolella."
    try:
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")
        return f"OK: Tiedosto '{path}' kirjoitettu onnistuneesti."
    except OSError as e:
        return f"VIRHE kirjoitettaessa tiedostoa: {e}"


def _list_files(path: str = ".") -> str:
    """Listaa tyotilan tiedostot ja hakemistot."""
    full_path = _safe_path(path)
    if not full_path or not full_path.is_dir():
        return f"VIRHE: Hakemistoa '{path}' ei loydy."
    try:
        items = sorted(full_path.iterdir())
        if not items:
            return "(tyhjä hakemisto)"
        result = []
        for item in items:
            prefix = "📁 " if item.is_dir() else "📄 "
            result.append(f"{prefix}{item.name}")
        return "\n".join(result)
    except OSError as e:
        return f"VIRHE listattaessa tiedostoja: {e}"


# ── CrewAI @tool -kaareet ─────────────────────────────────────────

@tool("read_file")
def read_file(path: str) -> str:
    """
    Lukee tiedoston tyotilasta. Anna tiedostonimi, esim. 'raportti.txt'.
    Hyodyllinen agentin luomien koodien tai analyysien tarkistamiseen.
    """
    return _read_file(path)


@tool("write_file")
def write_file(path: str, content: str) -> str:
    """
    Kirjoittaa tiedoston tyotilaan. Kayta tata analyysien tai Python-skriptien tallentamiseen.
    Esimerkki: path='analyysi.py', content='import pandas as pd...'
    """
    return _write_file(path, content)


@tool("list_files")
def list_files(path: str = ".") -> str:
    """
    Listaa tyotilan tiedostot ja hakemistot.
    Auttaa agenttia hahmottamaan, mita tiedostoja se on jo luonut.
    """
    return _list_files(path)