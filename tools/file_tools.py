"""
file_tools.py - Tiedosto-operaatiot agentin työtilassa projektin sisällä.
"""

import os
from pathlib import Path
from crewai.tools import tool

# 1. TUNNISTETAAN PROJEKTIN JUURI JA TYÖTILA
PROJECT_ROOT = Path(__file__).resolve().parent.parent
WORKSPACE = PROJECT_ROOT / "workspace"
WORKSPACE.mkdir(parents=True, exist_ok=True)

def _safe_path(path_str: str) -> Path | None:
    """
    Palauttaa validoidun polun työtilan sisällä.
    Estää agenttia karkaamasta työtilan ulkopuolelle (esim. ../../).
    """
    if path_str.startswith("workspace/"):
        path_str = path_str[len("workspace/"):]
    
    # Rakennetaan polku pathlibillä
    try:
        requested_path = (WORKSPACE / path_str).resolve()
        # Varmistetaan, että polku on oikeasti WORKSPACE-kansion sisällä
        if WORKSPACE.resolve() in requested_path.parents or requested_path == WORKSPACE.resolve():
            return requested_path
    except Exception:
        return None
    return None

@tool("read_file")
def read_file(path: str) -> str:
    """
    Lukee tiedoston työtilasta. Anna tiedostonimi, esim. 'raportti.txt'.
    Hyödyllinen agentin luomien koodien tai analyysien tarkistamiseen.
    """
    full_path = _safe_path(path)
    if not full_path or not full_path.is_file():
        return f"VIRHE: Tiedostoa '{path}' ei löydy tai se on työtilan ulkopuolella."
    
    try:
        content = full_path.read_text(encoding="utf-8")
        return content[:5000] if len(content) > 5000 else content
    except Exception as e:
        return f"VIRHE luettaessa tiedostoa: {e}"

@tool("write_file")
def write_file(path: str, content: str) -> str:
    """
    Kirjoittaa tiedoston työtilaan. Käytä tätä analyysien tai Python-skriptien tallentamiseen.
    Esimerkki: path='analyysi.py', content='import pandas as pd...'
    """
    full_path = _safe_path(path)
    if not full_path:
        return "VIRHE: Polku on työtilan ulkopuolella."
    
    try:
        # Luodaan alihakemistot tarvittaessa
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")
        return f"OK: Tiedosto '{path}' kirjoitettu onnistuneesti."
    except Exception as e:
        return f"VIRHE kirjoitettaessa tiedostoa: {e}"

@tool("list_files")
def list_files(path: str = ".") -> str:
    """
    Listaa työtilan tiedostot ja hakemistot.
    Auttaa agenttia hahmottamaan, mitä tiedostoja se on jo luonut.
    """
    full_path = _safe_path(path)
    if not full_path or not full_path.is_dir():
        return f"VIRHE: Hakemistoa '{path}' ei löydy."
    
    try:
        items = sorted(full_path.iterdir())
        if not items:
            return "(tyhjä hakemisto)"
        
        result = []
        for item in items:
            prefix = "📁 " if item.is_dir() else "📄 "
            result.append(f"{prefix}{item.name}")
        return "\n".join(result)
    except Exception as e:
        return f"VIRHE listattaessa tiedostoja: {e}"