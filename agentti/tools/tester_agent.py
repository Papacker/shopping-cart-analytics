"""
tester_agent.py - Python-koodin testaustyökalut CrewAI:n testaaja-agentille.

Voidaan ajaa myös SUORAAN terminaalista:
    uv run python agentti/tools/tester_agent.py src/app.py
    uv run python agentti/tools/tester_agent.py agentti/crew.py

Sisältää:
  - test_file      : PÄÄTYÖKALU — syntaksi + pylint + pytest + coverage yhdellä kutsulla
  - run_file       : Suorittaa tiedoston skriptinä ja palauttaa tulosteen
  - check_syntax   : Syntaksitarkistus koodimerkkijonosta
  - run_pylint     : Pylint tiedostopolulle
  - run_tests      : Pytest + coverage tiedostopolulle
  - run_and_assert : Koodinpätkän ajo + tulosteen vertailu
  - run_coverage   : Coverage-raportti erikseen
"""

import ast
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from crewai.tools import tool

# --- Polut ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent  # projektin juuri
AGENTTI_ROOT = Path(__file__).resolve().parent.parent         # agentti/
WORKSPACE    = AGENTTI_ROOT / "workspace"
WORKSPACE.mkdir(parents=True, exist_ok=True)

env_vars = os.environ.copy()
env_vars["PYTHONPATH"] = str(PROJECT_ROOT) + os.pathsep + env_vars.get("PYTHONPATH", "")


def _resolve_path(path_str: str) -> Path | None:
    """
    Muuntaa suhteellisen tai osittaisen polun absoluuttiseksi.
    Hyväksyy: 'src/main.py', 'agentti/crew.py', 'analyysi.py' (workspace), abs. polut.
    """
    p = Path(path_str)
    if p.is_absolute():
        return p if p.exists() else None

    # 1. Projektin juuresta
    candidate = (PROJECT_ROOT / p).resolve()
    if candidate.exists():
        return candidate

    # 2. Workspace-kansiosta (strip 'workspace/' prefix)
    ws_str = path_str
    for prefix in ("workspace/", "workspace\\"):
        if ws_str.startswith(prefix):
            ws_str = ws_str[len(prefix):]
            break
    candidate_ws = (WORKSPACE / ws_str).resolve()
    if candidate_ws.exists():
        return candidate_ws

    return None


def _run_cmd(cmd: list[str], timeout: int = 120) -> tuple[str, int]:
    """Ajaa komennon ja palauttaa (output, returncode)."""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True,
            timeout=timeout, cwd=PROJECT_ROOT, env=env_vars,
        )
        return ((result.stdout + result.stderr).strip(), result.returncode)
    except subprocess.TimeoutExpired:
        return (f"VIRHE: Aikakatkaisu ({timeout}s)", -1)
    except FileNotFoundError as e:
        return (f"VIRHE: Ohjelma ei löydy — {e}", -1)


# ═══════════════════════════════════════════════════════════════
# Sisäinen testiajuri (käytetään sekä @tool:ista että __main__:sta)
# ═══════════════════════════════════════════════════════════════

def _run_test_file(path: str) -> str:
    """Ajaa kaikki testit ja palauttaa markdown-raportin merkkijonona."""

    resolved = _resolve_path(path)
    if not resolved:
        msg = (
            f"# Testitulokset: {path}\n\n"
            f"**VIRHE:** Tiedostoa `{path}` ei löydy.\n\n"
            f"Anna polku projektin juuresta, esim. `src/main.py` tai `agentti/crew.py`.\n\n"
            f"Projektin juuri: `{PROJECT_ROOT}`"
        )
        print(msg)
        return msg

    rel_path = str(resolved.relative_to(PROJECT_ROOT))
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    sections = []

    # ── 1. Syntaksi ──────────────────────────────────────────
    try:
        source = resolved.read_text(encoding="utf-8")
        ast.parse(source)
        syntax_ok = True
        syntax_result = "✅ OK — syntaksi on kunnossa."
    except SyntaxError as e:
        syntax_ok = False
        syntax_result = f"❌ VIRHE rivillä {e.lineno}: {e.msg}\n\n```\n{e.text}\n```"
    except Exception as e:
        syntax_ok = False
        syntax_result = f"❌ VIRHE: {e}"

    sections.append(f"## 1. Syntaksi\n\n{syntax_result}")

    # ── 2. Pylint ─────────────────────────────────────────────
    pylint_out, _ = _run_cmd([
        sys.executable, "-m", "pylint", str(resolved),
        "--output-format=text", "--score=yes",
        "--disable=C0114,C0115,C0116",
    ], timeout=60)

    score_line = ""
    pylint_ok = False
    for line in pylint_out.splitlines():
        if "Your code has been rated" in line:
            score_line = line.strip()
            try:
                score = float(score_line.split("rated at")[1].split("/")[0].strip())
                pylint_ok = score >= 7.0
            except Exception:
                pass

    if "No module named pylint" in pylint_out:
        pylint_section = "⚠️  pylint ei ole asennettu. Asenna: `uv add pylint`"
        pylint_ok = None
    else:
        icon = "✅" if pylint_ok else "❌"
        pylint_section = (
            f"```\n{pylint_out[:3000]}\n```\n\n"
            f"{icon} Pistemäärä: **{score_line}** (kynnys: 7.0/10)"
        )

    sections.append(f"## 2. Pylint-koodilaatu\n\n{pylint_section}")

    # ── 3. Pytest + Coverage ──────────────────────────────────
    pytest_cmd = [
        sys.executable, "-m", "pytest", str(resolved),
        "--tb=short", "-v", "--no-header",
        f"--cov={resolved.parent}",
        "--cov-report=term-missing",
    ]
    pytest_out, pytest_code = _run_cmd(pytest_cmd, timeout=120)

    if "No module named pytest_cov" in pytest_out or "no plugin named" in pytest_out.lower():
        plain_cmd = [
            sys.executable, "-m", "pytest", str(resolved),
            "--tb=short", "-v", "--no-header",
        ]
        pytest_out, pytest_code = _run_cmd(plain_cmd, timeout=120)
        pytest_out += "\n\n⚠️  pytest-cov ei ole asennettu. Asenna: `uv add pytest-cov`"
        cov_pct = "N/A"
    else:
        cov_pct = "N/A"
        for line in pytest_out.splitlines():
            if "TOTAL" in line:
                parts = line.split()
                if parts:
                    cov_pct = parts[-1]

    if pytest_code == 5:
        pytest_ok = None
        pytest_status = "⚠️  Ei pytest-testejä löydy tiedostosta."
    elif pytest_code == 0:
        pytest_ok = True
        pytest_status = "✅ Kaikki testit läpäisivät."
    else:
        pytest_ok = False
        pytest_status = "❌ Osa testeistä epäonnistui."

    pytest_section = (
        f"```\n{pytest_out[:3000]}\n```\n\n"
        f"{pytest_status}\n"
        f"- **Coverage:** {cov_pct}"
    )
    sections.append(f"## 3. Pytest + Coverage\n\n{pytest_section}")

    # ── 4. Yhteenveto ─────────────────────────────────────────
    def _icon(ok):
        if ok is True:  return "✅"
        if ok is False: return "❌"
        return "⚠️ "

    summary = (
        f"| Tarkistus | Tulos |\n"
        f"|---|---|\n"
        f"| Syntaksi | {_icon(syntax_ok)} {'OK' if syntax_ok else 'VIRHE'} |\n"
        f"| Pylint (≥7.0/10) | {_icon(pylint_ok)} {score_line or 'N/A'} |\n"
        f"| Pytest | {_icon(pytest_ok)} {'Passed' if pytest_ok else ('Ei testejä' if pytest_ok is None else 'Failed')} |\n"
        f"| Coverage | {_icon(None)} {cov_pct} |\n"
    )
    sections.append(f"## 4. Yhteenveto\n\n{summary}")

    # ── Kootaan raportti ──────────────────────────────────────
    report = (
        f"# Testitulokset: `{rel_path}`\n\n"
        f"**Päiväys:** {now}  \n"
        f"**Tiedosto:** `{resolved}`\n\n"
        + "\n\n---\n\n".join(sections)
    )

    # Tulostetaan myös suoraan terminaaliin
    print("\n" + "="*60)
    print(f"📋 TESTITULOKSET: {rel_path}")
    print("="*60)
    print(report)
    print("="*60 + "\n")

    return report


# ═══════════════════════════════════════════════════════════════
# CrewAI @tool -kääre
# ═══════════════════════════════════════════════════════════════

@tool("test_file")
def test_file(path: str) -> str:
    """
    PÄÄTYÖKALU. Testaa Python-tiedoston kattavasti yhdellä kutsulla.

    Ajaa järjestyksessä: syntaksitarkistus → pylint → pytest + coverage.
    Palauttaa valmiin markdown-raportin joka tallennetaan write_file-työkalulla.

    Parametrit:
      path - Tiedostopolku projektin juuresta:
             'agentti/crew.py', 'src/app.py', 'agentti/tools/tester_agent.py'
    """
    return _run_test_file(path)


@tool("run_file")
def run_file(path: str) -> str:
    """
    Suorittaa Python-tiedoston skriptinä ja palauttaa stdout + stderr.
    Anna polku projektin juuresta, esim. 'src/main.py'.
    Lopetetaan 30 sekunnin jälkeen.
    """
    resolved = _resolve_path(path)
    if not resolved:
        return f"VIRHE: Tiedostoa '{path}' ei löydy."
    out, code = _run_cmd([sys.executable, str(resolved)], timeout=30)
    prefix = "✅ (exit 0)" if code == 0 else f"❌ (exit {code})"
    return f"{prefix}\n\n{out[:4000]}" if out else f"{prefix}\n(ei tulostetta)"


@tool("check_syntax")
def check_syntax(code: str) -> str:
    """
    Tarkistaa Python-koodin syntaksin ilman suoritusta.
    Syötä koodi MERKKIJONONA, ei tiedostopolkuna.
    Käytä test_file-työkalua jos haluat testata tiedostoa polulla.
    """
    if not code or not code.strip():
        return "VIRHE: Koodi on tyhjä."
    try:
        ast.parse(code)
        return "OK: Syntaksi on kunnossa."
    except SyntaxError as e:
        return f"SYNTAKSIVIRHE rivillä {e.lineno}: {e.msg}\n  {e.text!r}"


@tool("run_pylint")
def run_pylint(path: str) -> str:
    """
    Ajaa pylint-koodilaaturaportin tiedostopolulle.
    Anna polku projektin juuresta, esim. 'agentti/crew.py'.
    """
    resolved = _resolve_path(path)
    if not resolved:
        return f"VIRHE: Tiedostoa '{path}' ei löydy."
    out, _ = _run_cmd([
        sys.executable, "-m", "pylint", str(resolved),
        "--output-format=text", "--score=yes", "--disable=C0114,C0115,C0116",
    ], timeout=60)
    return out[:5000] or "(ei tulostetta)"


@tool("run_tests")
def run_tests(path: str) -> str:
    """
    Ajaa pytest + coverage tiedostopolulle tai hakemistolle.
    Anna polku projektin juuresta, esim. 'agentti/crew.py' tai 'tests/'.
    """
    resolved = _resolve_path(path)
    if not resolved:
        return f"VIRHE: Polkua '{path}' ei löydy."
    out, _ = _run_cmd([
        sys.executable, "-m", "pytest", str(resolved),
        "--tb=short", "-v", "--no-header",
        f"--cov={resolved.parent}", "--cov-report=term-missing",
    ], timeout=120)
    if "No module named pytest_cov" in out:
        out2, _ = _run_cmd([
            sys.executable, "-m", "pytest", str(resolved),
            "--tb=short", "-v", "--no-header",
        ], timeout=120)
        return out2[:5000] + "\n\n⚠️  Asenna pytest-cov: uv add pytest-cov"
    return out[:5000]


@tool("run_and_assert")
def run_and_assert(code: str, expected_output: str) -> str:
    """
    Ajaa Python-koodinpätkän ja vertaa tulostetta odotettuun arvoon.
    Parametrit: code (suoritettava koodi), expected_output (odotettu stdout).
    """
    try:
        ast.parse(code)
    except SyntaxError as e:
        return f"SYNTAKSIVIRHE rivillä {e.lineno}: {e.msg}"
    out, rc = _run_cmd([sys.executable, "-c", code], timeout=60)
    if rc != 0:
        return f"VIRHE (exit {rc}):\n{out[:2000]}"
    actual = out.strip()
    expected = expected_output.strip()
    if actual == expected:
        return f"✅ PASS\n  Tuloste: {actual!r}"
    return f"❌ FAIL\n  Odotettu: {expected!r}\n  Saatu:    {actual!r}"


@tool("run_coverage")
def run_coverage(path: str) -> str:
    """
    Ajaa pytest-cov-raportin tiedostopolulle tai hakemistolle.
    Anna polku projektin juuresta, esim. 'src/'.
    """
    resolved = _resolve_path(path)
    if not resolved:
        return f"VIRHE: Polkua '{path}' ei löydy."
    source = str(resolved.parent) if resolved.is_file() else str(resolved)
    out, _ = _run_cmd([
        sys.executable, "-m", "pytest", str(resolved),
        f"--cov={source}", "--cov-report=term-missing", "-q", "--no-header",
    ], timeout=120)
    return out[:5000]


# ═══════════════════════════════════════════════════════════════
# Suora terminaalikäyttö: python tester_agent.py <tiedosto>
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Aseta UTF-8 tuki Windows-terminaalille
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    if len(sys.argv) < 2:
        print("Kaytto:  python tester_agent.py <tiedostopolku>")
        print("Esim:    python tester_agent.py agentti/crew.py")
        print("Esim:    python tester_agent.py src/app.py")
        sys.exit(1)

    target = sys.argv[1]
    print(f"\n[TESTI] Testataan: {target}")
    result = _run_test_file(target)

    # Tallennetaan myös testitulokset.md-tiedostoon
    out_path = WORKSPACE / "testitulokset.md"
    out_path.write_text(result, encoding="utf-8")
    print(f"\n[OK] Raportti tallennettu: {out_path}")
