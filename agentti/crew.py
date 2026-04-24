"""crew.py - CrewAI-agenttien kokoonpano ja käynnistys."""

import os
import sys
from dotenv import load_dotenv
from pathlib import Path

# Skripti on /agentti/crew.py -> .env on /
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent
env_path = project_root / ".env"

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
    test_file, run_file,
    run_tests, check_syntax, run_and_assert, run_pylint, run_coverage,
)
from tools.tester_agent import _run_test_file, WORKSPACE as TESTER_WORKSPACE
# pylint: enable=wrong-import-position

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

# 1. THE STRATEGIC LEADER
manager = Agent(
    role="UWB Analysis Manager",
    goal="Orchestrate the analysis process to identify shopping cart patterns and store bottlenecks.",
    backstory=(
        "You are the strategic lead. You MUST use 'inspect_schema' first to understand the data structure. "
        "You then share the relevant table and column names with the Analyst and Engineer. "
        "Your focus is on ensuring the workflow leads to actionable insights about customer flows."
    ),
    llm=llm,
    tools=pm_tools,
    verbose=True,
    allow_delegation=True # Essential for hierarchical logic
)

# 2. THE DATA MINER
analyst = Agent(
    role="Data Discovery Analyst",
    goal="Extract and aggregate UWB positioning data from DuckDB for specific store zones.",
    backstory=(
        "You are an expert in SQL. You receive the schema information from the Manager and "
        "perform complex queries to calculate session durations"
        "You provide structured data for the Python Engineer."
    ),
    llm=llm,
    tools=data_tools, 
    verbose=True,
    max_iter=3,
)
# 3. THE VISUALIZATION ENGINEER
engineer = Agent(
    role="Python Visualization Engineer",
    goal="Create high-quality heatmaps and flow diagrams from the analyzed data.",
    backstory=(
        "You use Pandas, Matplotlib, and Seaborn to transform data into visual heatmaps. "
        "You focus on visualizing checkout congestion and department-specific bottlenecks. "
        "You save all outputs to the 'workspace' folder."
    ),
    llm=llm,
    tools=code_tools,
    verbose=True
)

liiketoiminta_agentti = Agent(
    role="Ali Baba",
    goal="Toteuta laskentaa ja visualisointeja",
    backstory="Python-kehittaja. Tallennat tulokset workspace-kansioon.",
    llm=llm,
    tools=code_tools,
    verbose=True,
)

testaaja_agentti = Agent(
    role="Python-testaaja",
    goal=(
        "Testaa annettu Python-tiedosto kattavasti ja kirjoita "
        "markdown-raportti workspace/testitulokset.md-tiedostoon."
    ),
    backstory=(
        "Olet QA-insinoori. Paatyokalusi on 'test_file'. "
        "Kutsu sita tiedostopolulla (esim. 'agentti/crew.py'). "
        "Se ajaa syntaksitarkistuksen, pylintin, pytestin ja coveragen. "
        "Tallenna raportti write_file-tyokalulla polkuun 'testitulokset.md'. "
        "ALA kutsu muita testaustyokaluja erikseen."
    ),
    llm=llm,
    tools=code_tools,
    verbose=True,
    max_iter=5,
)

# === Crewit ===

def build_tester_crew(file_path: str) -> Crew:
    """
    Erillinen testaustiimi — vain testaaja_agentti, ilman DB-analyysia.
    Kayta tata kun haluat testata Python-tiedostoa CrewAI:n kautta.
    """
    tehtava = Task(
        description=(
            f"Testaa tiedosto: {file_path}\n\n"
            f"Kutsu test_file-tyokalua argumentilla '{file_path}'.\n"
            "Se palauttaa valmiin markdown-raportin.\n"
            "Tallenna raportti write_file-tyokalulla polkuun 'testitulokset.md'.\n"
            "Yksi test_file-kutsu riittaa."
        ),
        expected_output=(
            "Markdown-testitulokset tallennettuna tiedostoon "
            "workspace/testitulokset.md."
        ),
        agent=testaaja_agentti,
        output_file="agentti/workspace/testitulokset.md",
    )

    
    return Crew(
        agents=[manager, analyst, engineer],
        tasks=[tehtava],
        process=Process.sequential,
        verbose=True,
    )


def build_crew(task_description: str) -> Crew:
    """
    Taysi analyysitiimi: projektipaallikko, analyytikko, koodaaja, testaaja.
    Kayta tata tietokanta-analyysi- ja koodaustehtaviin.
    """
    analyysi_tehtava = Task(
        description=(
            f"TEHTAVA: {task_description}\n\n"
            "OHJEET:\n"
            "1. ALA etsi ./tmp tai ./temp hakemistoja.\n"
            "2. Kayta heti 'inspect_schema'-tyokalua nahdaksesi taulut.\n"
            "3. Suorita SQL-kyselyt ja anna selkea vastaus."
        ),
        expected_output="Selkea vastaus tai analyysiraportti tietokannan perusteella.",
        agent=manager,
        output_file="agentti/workspace/raportti.md",
    )

    koodaus_tehtava = Task(
        description=(
            "Kirjoita Python-koodi jonka projektipaallikko tai analyytikko tilasi. "
            "Tallenna valmis koodi workspace-kansioon write_file-tyokalulla. "
            "Anna koodatulle tiedostolle kuvaava nimi, esim. 'analyysi.py'."
        ),
        expected_output="Valmis Python-tiedosto workspace-kansiossa.",
        agent=engineer,
    )

    testaus_tehtava = Task(
        description=(
            "Testaa koodaajan kirjoittama tiedosto.\n"
            "1. Kayta list_files-tyokalua loyytaaksesi uusimman .py-tiedoston.\n"
            "2. Kutsu test_file-tyokalua loyytamallasi tiedostopolulla.\n"
            "3. Tallenna saatu raportti write_file-tyokalulla "
            "polkuun 'testitulokset.md'."
        ),
        expected_output=(
            "Markdown-testitulokset tallennettuna "
            "workspace/testitulokset.md-tiedostoon."
        ),
        agent=testaaja_agentti,
        output_file="agentti/workspace/testitulokset.md",
    )

    return Crew(
        agents=[manager, analyst, engineer, testaaja_agentti],
        tasks=[analyysi_tehtava, koodaus_tehtava, testaus_tehtava],
        process=Process.sequential,
        verbose=True,
    )


# === Kaynistys ===

# Avainsanat jotka reitittavat suoraan testausajoon (ilman LLM:aa)
_TESTI_AVAINSANAT = ("testaa ", "testa ", "test ", "pytest", "pylint", "coverage")


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
            print(result)
            print("=" * 60)
        except (RuntimeError, ValueError, OSError) as e:
            print(f"[VIRHE] {e}")


if __name__ == "__main__":
    main()
