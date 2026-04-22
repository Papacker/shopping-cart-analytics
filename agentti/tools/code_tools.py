"""
code_tools.py - Työkalut Pythonin ja Shell-komentojen turvalliseen ajoon CrewAI:lle.
"""

import os
import subprocess
import sys
from pathlib import Path
from crewai.tools import tool

# 1. TUNNISTETAAN PROJEKTIN JUURI 
PROJECT_ROOT = Path(__file__).resolve().parent.parent
WORKSPACE = PROJECT_ROOT / "workspace"
os.makedirs(WORKSPACE, exist_ok=True)

# Lisätään projektin juuri ympäristömuuttujiin, jotta 'import config.store_config' toimii
env_vars = os.environ.copy()
env_vars["PYTHONPATH"] = str(PROJECT_ROOT) + ":" + env_vars.get("PYTHONPATH", "")

def _run_python(code: str) -> str:
    """Sisainen toteutus — kutsuttavissa suoraan testeista."""
    try:
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=WORKSPACE,
            env=env_vars,
        )
        output = result.stdout
        if result.returncode != 0:
            output += f"\nVIRHE (exit {result.returncode}):\n{result.stderr}"
        return (output.strip() or "(ei tulostetta)")[:5000]
    except subprocess.TimeoutExpired:
        return "VIRHE: aikakatkaisu (60s)"


@tool("run_python")
def run_python(code: str) -> str:
    """
    Ajaa Python-koodia ja palauttaa tulosteen.
    Kaytettavissa: pandas, duckdb, matplotlib, plotly, streamlit.
    HUOM: Kayta tietokantahakuihin polkua: ../database/store.db
    """
    return _run_python(code)


def _run_shell(command: str) -> str:
    """Sisainen toteutus — kutsuttavissa suoraan testeista."""
    blocked = ["rm -rf /", "mkfs", "dd if=", ":(){", "fork", "reset_env"]
    if any(b in command for b in blocked):
        return "VIRHE: komento estetty turvallisuussyista"
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60,
            cwd=WORKSPACE,
            env=env_vars,
        )
        output = result.stdout
        if result.returncode != 0:
            output += f"\nVIRHE (exit {result.returncode}):\n{result.stderr}"
        return (output.strip() or "(ei tulostetta)")[:5000]
    except subprocess.TimeoutExpired:
        return "VIRHE: aikakatkaisu (60s)"


@tool("run_shell")
def run_shell(command: str) -> str:
    """
    Ajaa shell-komennon tyotilassa.
    Kayta datan hallintaan, esim: 'ls -la ../database/', 'pip install'.
    """
    return _run_shell(command)