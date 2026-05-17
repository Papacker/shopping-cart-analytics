"""crew.py - CrewAI-agenttien kokoonpano ja käynnistys."""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Skripti on /agentti/crew.py -> .env on /
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent
env_path = project_root / ".env"
load_dotenv(dotenv_path=env_path)
os.environ["OPENAI_API_KEY"] = "NA"
os.environ["OPENAI_API_BASE"] = f"{os.environ.get('OLLAMA_HOST', 'http://127.0.0.1:11434')}/v1"
os.environ["OTEL_SDK_DISABLED"] = "true"
os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "true"

# Lisätään polku, jotta tools-kansio löytyy varmasti
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
# Projektin juuri sys.pathiin jotta store_config löytyy
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# pylint: disable=wrong-import-position
from crewai import LLM, Agent, Crew, Process, Task
from tools import (
    run_python, run_shell,
    query_duckdb, inspect_schema,
    list_files, read_file, write_file,
)
from config.store_config import store_config  # pylint: disable=import-error


# === LLM-konfiguraatio ===
MODEL_NAME = os.environ.get("APP_OLLAMA_MODEL", "llama3.1:8b")
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")

llm = LLM(
    model=MODEL_NAME, # Poistettu ollama/-prefiksi
    base_url=f"{OLLAMA_HOST}/v1", # Käytetään OpenAI-yhteensopivaa endpointia
    api_key="NA",
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
# === Konfigurointipohjaiset SQL-generaattorit ===

def _build_department_sql() -> str:
    """
    Generoi osastoanalyysi-SQL dynaamisesti store_config.departments-maarityksista.
    Kayttaa Zone-taulun koordinaatteja ja vertaa niita osastojen koordinaattilaatikoihin.
    """
    departments = store_config["spatial_zones"]["departments"]
    cases = []
    for name, dept in departments.items():
        x_min, x_max, y_min, y_max = dept["coords"]
        escaped = name.replace("'", "''")
        cases.append(
            f"        WHEN z.x BETWEEN {x_min} AND {x_max} "
            f"AND z.y BETWEEN {y_min} AND {y_max} THEN '{escaped}'"
        )
    case_block = "\n".join(cases)
    return (
        "SELECT\n"
        "    CASE\n"
        f"{case_block}\n"
        "        ELSE 'Muu / kaytava'\n"
        "    END AS osasto,\n"
        "    COUNT(DISTINCT z.visit_id) AS uniikkeja_kaynteja,\n"
        "    COUNT(*) AS paikannuspisteet,\n"
        "    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS osuus_pct\n"
        "FROM Zone z\n"
        "GROUP BY osasto\n"
        "ORDER BY paikannuspisteet DESC"
    )


def _build_checkout_sql() -> str:
    """
    Generoi kassaruuhka-SQL dynaamisesti store_config.checkouts-maarityksista.
    """
    checkouts = store_config["spatial_zones"]["checkouts"]
    cases = []
    where_parts = []
    for name, info in checkouts.items():
        x_min, x_max, y_min, y_max = info["coords"]
        escaped = name.replace("'", "''")
        cases.append(
            f"        WHEN z.x BETWEEN {x_min} AND {x_max} "
            f"AND z.y BETWEEN {y_min} AND {y_max} THEN '{escaped}'"
        )
        where_parts.append(
            f"(z.x BETWEEN {x_min} AND {x_max} AND z.y BETWEEN {y_min} AND {y_max})"
        )
    case_block = "\n".join(cases)
    where_block = "\n    OR ".join(where_parts)
    return (
        "SELECT\n"
        "    CASE\n"
        f"{case_block}\n"
        "    END AS kassa,\n"
        "    COUNT(DISTINCT z.visit_id) AS kaynteja,\n"
        "    COUNT(*) AS paikannuspisteet\n"
        "FROM Zone z\n"
        f"WHERE (\n    {where_block}\n)\n"
        "GROUP BY kassa\n"
        "ORDER BY paikannuspisteet DESC"
    )


# === Datan esihaku (luotettava Python-lahestymistapa) ===

def _fetch_all_data(db_path: str) -> dict:
    """
    Hakee kaikki analyysidatat suoraan DuckDB:sta ennen agenttia.
    Peruskyselyt ovat kovakoodattu tahan, osasto- ja kassakyselyt
    generoidaan dynaamisesti store_config.py:sta.
    """
    try:
        import duckdb  # pylint: disable=import-outside-toplevel
    except ImportError:
        return {"virhe": "duckdb ei ole asennettu"}

    if not Path(db_path).exists():
        return {"virhe": f"Tietokantaa ei loydy: {db_path}"}

    queries: dict = {
        "yleiskatsaus": (
            "SELECT COUNT(DISTINCT visit_id) AS kaynteja_yhteensa, "
            "COUNT(DISTINCT node_id) AS aktiivisia_karyja, "
            "ROUND(AVG(duration_seconds)/60.0,1) AS keski_kesto_min, "
            "ROUND(MIN(duration_seconds)/60.0,1) AS lyhin_min, "
            "ROUND(MAX(duration_seconds)/60.0,1) AS pisin_min, "
            "ROUND(SUM(duration_seconds)/3600.0,1) AS yhteisaika_h "
            "FROM Visit"
        ),
        "kaynteja_per_karry": (
            "SELECT sc.description AS karry, COUNT(v.visit_id) AS kaynteja, "
            "ROUND(AVG(v.duration_seconds)/60.0,1) AS keski_min, "
            "ROUND(MAX(v.duration_seconds)/60.0,1) AS pisin_min, "
            "ROUND(SUM(v.duration_seconds)/3600.0,1) AS yht_h "
            "FROM Visit v JOIN ShoppingCart sc ON v.node_id = sc.node_id "
            "GROUP BY sc.description ORDER BY kaynteja DESC"
        ),
        "kaynteja_per_paiva": (
            "SELECT CAST(start_time AS DATE) AS paiva, COUNT(*) AS kaynteja, "
            "ROUND(AVG(duration_seconds)/60.0,1) AS keski_min "
            "FROM Visit GROUP BY CAST(start_time AS DATE) ORDER BY paiva"
        ),
        "kaynteja_per_tunti": (
            "SELECT CAST(EXTRACT(HOUR FROM start_time) AS INTEGER) AS tunti, "
            "COUNT(*) AS kaynteja, ROUND(AVG(duration_seconds)/60.0,1) AS keski_min "
            "FROM Visit GROUP BY tunti ORDER BY tunti"
        ),
        "kaynteja_per_viikonpaiva": (
            "SELECT CASE EXTRACT(DOW FROM start_time) "
            "WHEN 0 THEN '0 Sunnuntai' WHEN 1 THEN '1 Maanantai' "
            "WHEN 2 THEN '2 Tiistai' WHEN 3 THEN '3 Keskiviikko' "
            "WHEN 4 THEN '4 Torstai' WHEN 5 THEN '5 Perjantai' "
            "WHEN 6 THEN '6 Lauantai' END AS viikonpaiva, "
            "COUNT(*) AS kaynteja, ROUND(AVG(duration_seconds)/60.0,1) AS keski_min "
            "FROM Visit GROUP BY viikonpaiva ORDER BY viikonpaiva"
        ),
        "kesto_luokat": (
            "SELECT CASE WHEN duration_seconds < 600 THEN '1. alle 10 min' "
            "WHEN duration_seconds < 1800 THEN '2. 10-30 min' "
            "WHEN duration_seconds < 3600 THEN '3. 30-60 min' "
            "WHEN duration_seconds < 7200 THEN '4. 1-2 tuntia' "
            "ELSE '5. yli 2 tuntia' END AS kestoluokka, "
            "COUNT(*) AS kaynteja, "
            "ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS osuus_pct "
            "FROM Visit GROUP BY kestoluokka ORDER BY kestoluokka"
        ),
        "laatu_syyt": (
            "SELECT is_valid, reason, COUNT(*) AS maara, "
            "ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS osuus_pct "
            "FROM Quality GROUP BY is_valid, reason "
            "ORDER BY is_valid DESC, maara DESC LIMIT 15"
        ),
        "zone_kattavuus": (
            "SELECT ROUND(MIN(x),0) AS x_min, ROUND(MAX(x),0) AS x_max, "
            "ROUND(MIN(y),0) AS y_min, ROUND(MAX(y),0) AS y_max, "
            "COUNT(*) AS paikannuspisteet_yht, COUNT(DISTINCT visit_id) AS kaynneissa "
            "FROM Zone"
        ),
        "top_pisin_yksittainen": (
            "SELECT sc.description AS karry, "
            "CAST(v.start_time AS DATE) AS paiva, "
            "ROUND(v.duration_seconds / 60.0, 1) AS kesto_min "
            "FROM Visit v JOIN ShoppingCart sc ON v.node_id = sc.node_id "
            "ORDER BY v.duration_seconds DESC LIMIT 10"
        ),
        # Konfiguraatiopohjaiset kyselyt — generoidaan store_config.py:sta
        "osastoanalyysi": _build_department_sql(),
        "kassaruuhka": _build_checkout_sql(),
    }

    results: dict = {}
    try:
        con = duckdb.connect(db_path, read_only=True)
        for name, sql in queries.items():
            try:
                df = con.execute(sql).fetchdf()
                results[name] = df.to_string(index=False)
            except Exception as exc:  # pylint: disable=broad-except
                results[name] = f"[Virhe kyselyssa '{name}']: {exc}"
        con.close()
    except Exception as exc:  # pylint: disable=broad-except
        results["yhteyden_virhe"] = str(exc)

    return results


# === Crew ===

def build_crew(task_description: str) -> Crew:
    """
    Kauppadatan analyysicrew: Python pre-hakee datan store_configin perusteella,
    agentti kirjoittaa markdown-raportin valmiista datasta.
    """
    db_path = str(project_root / "database" / "store.db")
    output_path = str(project_root / "agentti" / "workspace" / "raportti.md")

    print("\n[DATA] Haetaan tietokantadata ja generoidaan kyselyt store_configista...")
    data = _fetch_all_data(db_path)

    if "virhe" in data:
        print(f"[VAROITUS] {data['virhe']}")
        data_teksti = f"TIETOKANTAVIRHE: {data['virhe']}\n"
    else:
        data_teksti = "\n\n".join(
            f"=== {nimi.upper().replace('_', ' ')} ===\n{tulos}"
            for nimi, tulos in data.items()
        )
        print(f"[DATA] Haettu {len(data)} datasettia (osastot store_config.py:sta).")

    dept_names = list(store_config["spatial_zones"]["departments"].keys())
    dept_lista = ", ".join(dept_names[:6]) + f" ... ({len(dept_names)} osastoa)"

    analyysi_tehtava = Task(
        description=(
            f"TEHTAVA: {task_description}\n\n"
            "KONTEKSTI: Kaupan ostoskaryjen UWB-paikannusdata.\n"
            f"Kaupassa on {len(dept_names)} osastoa: {dept_lista}\n\n"
            "ALLA ON VALMIIKSI HAETTU DATA — EI TARVITSE AJAA SQL:AA:\n\n"
            f"{data_teksti}\n\n"
            "KIRJOITA kattava markdown-raportti SUOMEKSI:\n"
            "1. # Kaupan UWB-kayntiraportti\n"
            "2. ## Yleiskatsaus\n"
            "3. ## Kaynteja per ostoskarry\n"
            "4. ## Aikasarjat (paiva, viikonpaiva, tunti)\n"
            "5. ## Kayntiajat ja kestoluokat\n"
            "6. ## Osastoanalyysi (store_configin osastot)\n"
            "7. ## Kassaruuhka\n"
            "8. ## Datan laatu\n"
            "9. ## Yhteenveto\n\n"
            f"Tallenna write_file-tyokalulla: {output_path}"
        ),
        expected_output=(
            "Kattava markdown-raportti suomeksi, 9 osaa, "
            "taulukot | col | col | muodossa."
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
def build_dynamic_chat_crew(task_description: str, model_name: str) -> Crew:
    """
    UI:n chatin käyttämä tiimi. Reitittää pyynnön oikealle asiantuntijalle
    ja käyttää UI:sta valittua kielimallia.
    """
    # 1. Luodaan aivot valitulla mallilla
    chat_llm = LLM(
        model=model_name,
        base_url=f"{OLLAMA_HOST}/v1",
        api_key="NA",
        temperature=0.1
    )

    db_path = str(project_root / "database" / "store.db")
    fetched_data = _fetch_all_data(db_path)

    # 2. Suodatetaan oikea konteksti (Estää mallin sekoamisen liian isoon dataan)
    context_parts = []
    task_low = task_description.lower()

    if any(kw in task_low for kw in ["osasto", "suosituin", "department", "hylly"]):
        if "osastoanalyysi" in fetched_data:
            context_parts.append(f"=== SUOSITUIMMAT OSASTOT ===\n{fetched_data['osastoanalyysi']}")

    if any(kw in task_low for kw in ["kassa", "ruuhka", "checkout", "jonotus"]):
        if "kassaruuhka" in fetched_data:
            context_parts.append(f"=== KASSARUUHKA ===\n{fetched_data['kassaruuhka']}")

    if any(kw in task_low for kw in ["reitti", "kartta", "heatmap", "koordinaatti", "visuali"]):
        if "zone_kattavuus" in fetched_data:
            context_parts.append(f"=== ZONE-KATTAVUUS ===\n{fetched_data['zone_kattavuus']}")

    # Jos ei spesifiä pyyntöä, annetaan yleisdata
    if not context_parts and "virhe" not in fetched_data:
        context_parts = [f"=== YLEISKATSAUS ===\n{fetched_data.get('yleiskatsaus', '')}"]

    data_context = "\n\n".join(context_parts) if context_parts else "Tietokanta on tyhjä tai siihen ei saatu yhteyttä."

    # 3. Älykäs Agentin reititys UI-painikkeiden perusteella
    # Luodaan agentti lennosta kopioiden alkuperäiset tavoitteet, mutta uudella LLM:llä ja oikeilla työkaluilla!

    if "osastoanalyysi" in task_low:
        # Päätyy tänne, kun UI:ssa painetaan: "LUO OSASTOANALYYSI (DATA-ANALYYTIKKO)"
        active_agent = Agent(
            role=analyst.role, goal=analyst.goal, backstory=analyst.backstory,
            llm=chat_llm, tools=data_tools, verbose=True, allow_delegation=False
        )
    elif "kassaruuhkat" in task_low or "kassaruuhka" in task_low:
        # Päätyy tänne, kun UI:ssa painetaan: "ANALYSOI KASSARUUHKAT (ALI BABA)"
        active_agent = Agent(
            role=liiketoiminta_agentti.role, goal=liiketoiminta_agentti.goal, backstory=liiketoiminta_agentti.backstory,
            llm=chat_llm, tools=code_tools, verbose=True, allow_delegation=False
        )
    elif any(kw in task_low for kw in ["visuali", "python", "reitit"]):
        # Päätyy tänne, kun UI:ssa painetaan: "KÄRRYREITIT PYTHONILLA (VISUALISOIJA)"
        active_agent = Agent(
            role=engineer.role, goal=engineer.goal, backstory=engineer.backstory,
            llm=chat_llm, tools=code_tools, verbose=True, allow_delegation=False
        )
    else:  
        # Vapaa chat-viesti: Analyysipäällikkö hoitaa yleisluontoiset vastaukset
        active_agent = Agent(
            role=manager.role, goal=manager.goal, backstory=manager.backstory,
            llm=chat_llm, tools=pm_tools, verbose=True, allow_delegation=False
        )

    # 4. Määritetään itse tehtävä
    task_prompt = (
        f"KÄYTTÄJÄN PYYNTÖ: {task_description}\n\n"
        f"KÄYTETTÄVISSÄ OLEVA TIETOKANTADATA:\n{data_context}\n\n"
        "Vastaa käyttäjän pyyntöön asiantuntevasti roolisi mukaisesti. Muotoile vastaus selkeällä Markdownilla."
    )

    chat_task = Task(
        description=task_prompt,
        expected_output="Asiantunteva, tiivis suomenkielinen analyysi Markdownilla.",
        agent=active_agent
    )

    return Crew(
        agents=[active_agent],
        tasks=[chat_task],
        process=Process.sequential,
        verbose=True
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
