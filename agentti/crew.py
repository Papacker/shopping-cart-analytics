"""crew.py - CrewAI-agenttien kokoonpano ja käynnistys."""

import os
import sys
from dotenv import load_dotenv
from pathlib import Path
import pandas as pd
import matplotlib as plt
import seaborn as sns



# Skripti on /agentti/crew.py -> .env on /
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent
env_path = project_root / ".env"
load_dotenv(dotenv_path=env_path)

# Lisätään polku, jotta tools-kansio löytyy varmasti
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# pylint: disable=wrong-import-position
from crewai import LLM, Agent, Crew, Process, Task
from tools import (
    run_python, run_shell,
    query_duckdb, inspect_schema,
    list_files, read_file, write_file,
)


# === LLM-konfiguraatio ===
MODEL_NAME = os.environ.get("APP_OLLAMA_MODEL", "qwen2.5-coder:14b")
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")

llm = LLM(
    model=f"ollama/{MODEL_NAME}",
    base_url=OLLAMA_HOST,
    temperature=0.1,
    max_tokens=4096,
)

# === Agentit ===

# Annetaan kaikille agenteille pääsy tietokantatyökaluihin, jotta kukaan ei hämmenny
pm_tools = [query_duckdb, inspect_schema] 
data_tools = [query_duckdb, inspect_schema, list_files, read_file, write_file]
code_tools = [run_python, run_shell, read_file, write_file, list_files]

# 1. ANALYYSIPAALLIKKO
manager = Agent(
    role="Kauppa-analyysin johtaja",
    goal="Koordinoi analyysitiimia ja varmista etta kaupan kayntidatasta saadaan selkeita oivalluksia.",
    backstory=(
        "Olet analyysipaallikko joka johtaa kauppadatan tutkimista. "
        "Kaupassa seurataan ostoskaryjen liikkeita UWB-paikannuksella. "
        "Kaytat query_duckdb-tyokalua SQL-kyselyihin ja raportoit tulokset suomeksi."
    ),
    llm=llm,
    tools=pm_tools,
    verbose=True,
    max_iter=5,
    allow_delegation=True
)

# 2. DATA-ANALYYTIKKO
analyst = Agent(
    role="Kauppadatan analyytikko",
    goal="Tutki kaupan kayntidataa SQL-kyselyilla ja laadi selkea raportti suomeksi.",
    backstory=(
        "Olet SQL-asiantuntija joka tutkii kaupan ostoskaryjen kayntidataa. "
        "Tietokannassa seurataan ostoskaryjen (ShoppingCart) reitteja kaupassa (Visit, Zone). "
        "Kaytat query_duckdb-tyokalua kyselyihin ja write_file-tyokalua raportin tallentamiseen."
    ),
    llm=llm,
    tools=data_tools,
    verbose=True,
    max_iter=5,
)
# 3. VISUALISOIJA
engineer = Agent(
    role="Python-visualisoija",
    goal="Luo selkeita kaavioita ja heatmappeja kaupan kayntidatasta.",
    backstory=(
        "Olet Python-kehittaja joka kayttaa Pandas, Matplotlib ja Seaborn -kirjastoja. "
        "Visualisoit ostoskaryjen reitteja ja kaupan alueita heatmappeina. "
        "Tallennat tulokset workspace-kansioon."
    ),
    llm=llm,
    tools=code_tools,
    verbose=True,
    max_iter=5,
)

liiketoiminta_agentti = Agent(
    role="Ali Baba",
    goal="Toteuta laskentaa ja visualisointeja",
    backstory="Python-kehittaja. Tallennat tulokset workspace-kansioon.",
    llm=llm,
    tools=code_tools,
    verbose=True,
)
# === Crew ===

def build_crew(task_description: str) -> Crew:
    """
    Kauppadatan analyysicrew: analyytikko tutkii kayntidatan ja kirjoittaa raportin suomeksi.
    """
    db_path = str(project_root / "database" / "store.db")
    output_path = str(project_root / "agentti" / "workspace" / "raportti.md")

    # Valmiiksi testatut SQL-kyselyt — agentti ajaa nämä sellaisenaan
    sql_kaynteja_per_karry = (
        "SELECT sc.description, COUNT(v.visit_id) AS kaynteja, "
        "ROUND(AVG(v.duration_seconds) / 60, 1) AS keski_kesto_min "
        "FROM Visit v "
        "JOIN ShoppingCart sc ON v.node_id = sc.node_id "
        "GROUP BY sc.description "
        "ORDER BY kaynteja DESC"
    )
    sql_kaynteja_per_paiva = (
        "SELECT CAST(start_time AS DATE) AS paiva, COUNT(*) AS kaynteja "
        "FROM Visit "
        "GROUP BY CAST(start_time AS DATE) "
        "ORDER BY paiva"
    )
    sql_pisimmat = (
        "SELECT sc.description, ROUND(MAX(v.duration_seconds) / 60.0, 1) AS pisin_min "
        "FROM Visit v "
        "JOIN ShoppingCart sc ON v.node_id = sc.node_id "
        "GROUP BY sc.description "
        "ORDER BY pisin_min DESC "
        "LIMIT 5"
    )

    analyysi_tehtava = Task(
        description=(
            f"TEHTAVA: {task_description}\n\n"
            f"TIETOKANTA: {db_path}\n\n"
            "KONTEKSTI: Kyseessa on KAUPPA jossa seurataan ostoskaryjen liikkeita.\n"
            "Karry = ostoskarry, visit = yksi kauppakaynti, node_id = korryn tunniste.\n\n"
            "AJA NAMAT KOLME SQL-KYSELYA TASSA JARJESTYKSESSA query_duckdb-tyokalulla.\n"
            "TARKEA: Kayda kyselyt TASMALLLEEN alla olevassa muodossa, ala muuta niita:\n\n"
            f"KYSELY 1 - Kaynteja per karry:\n{sql_kaynteja_per_karry}\n\n"
            f"KYSELY 2 - Kaynteja per paiva:\n{sql_kaynteja_per_paiva}\n\n"
            f"KYSELY 3 - Pisimmat kayntiajat:\n{sql_pisimmat}\n\n"
            "Kun olet ajanut kyselyt, kirjoita tuloksista markdown-raportti SUOMEKSI.\n"
            f"Tallenna raportti write_file-tyokalulla polkuun: {output_path}"
        ),
        expected_output=(
            "Markdown-raportti suomeksi jossa on:\n"
            "- # Kaupan käyntiraportti -otsikko\n"
            "- Taulukko: ostoskarry | käyntejä | keski kesto (min)\n"
            "- Käyntejä per päivä -taulukko\n"
            "- Yhteenveto: mitkä kärrit tekevät eniten kauppakäyntejä"
        ),
        agent=analyst,
        output_file=output_path,
    )

    return Crew(
        agents=[analyst],
        tasks=[analyysi_tehtava],
        process=Process.sequential,
        verbose=True,
    )


# === Testausapu ===


_TESTI_AVAINSANAT = ["testaa", "test ", "aja testit", "run tests"]
TESTER_WORKSPACE = Path(current_dir) / "workspace"


def _run_test_file(file_path: str) -> str:
    """Ajaa pytest-testit annetulle tiedostolle ja palauttaa raportin markdown-muodossa."""
    import subprocess  # pylint: disable=import-outside-toplevel
    cmd = [
        "python", "-m", "pytest", file_path,
        "-v", "--tb=short", "--no-header"
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    output = proc.stdout + proc.stderr
    status = "✅ PASS" if proc.returncode == 0 else "❌ FAIL"
    return (
        f"# Testitulokset: `{file_path}`\n\n"
        f"**Tila:** {status}\n\n"
        f"```\n{output.strip()}\n```\n"
    )


# === Kaynistys ===

def main():
    """Paaohjelma: lukee tehtavan ja reittaa sen oikealle crewille."""
    if len(sys.argv) > 1:
        task = " ".join(sys.argv[1:])
    else:
        task = input("Mita tiimin pitaisi tehda? > ")

    if not task:
        return

    task_lower = task.lower()

    if any(task_lower.startswith(kw) for kw in _TESTI_AVAINSANAT):
        # Poimitaan tiedostopolku avainsanan jalkeen
        file_path = task.strip()
        for kw in _TESTI_AVAINSANAT:
            if file_path.lower().startswith(kw):
                file_path = file_path[len(kw):].strip()
                break

        if not file_path:
            file_path = input(
                "Anna testattava tiedostopolku (esim. agentti/crew.py): > "
            ).strip()

        print(f"\n[TESTAUS] Ajetaan testit tiedostolle: {file_path}")
        print("(Suora ajo, LLM:aa ei tarvita)\n")

        report = _run_test_file(file_path)

        out_path = TESTER_WORKSPACE / "testitulokset.md"
        out_path.write_text(report, encoding="utf-8")
        print(f"\n[OK] Raportti tallennettu: {out_path}")

    else:
        print(f"\n[ANALYYSI] Kaynnistetaan UWB-analyysi osoitteessa {OLLAMA_HOST}...")
        crew = build_crew(task)
        try:
            result = crew.kickoff()
            print("\n" + "=" * 60)
            print("LOPPUTULOS:")
            print(result.raw)
            print("=" * 60)
        except (RuntimeError, ValueError, OSError) as e:
            print(f"[VIRHE] {e}")


if __name__ == "__main__":
    main()
