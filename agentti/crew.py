import os
import sys
from crewai import LLM, Agent, Crew, Process, Task

# Tuodaan aiemmin optimoidut työkalut
from tools.code_tools import run_python, run_shell
from tools.duckdb_tools import query_duckdb, inspect_schema 
from tools.file_tools import list_files, read_file, write_file

# === LLM-konfiguraatio ===
MODEL_NAME = os.environ.get("OLLAMA_MODEL", "qwen3:8b")
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://host.docker.internal:11434")

llm = LLM(
    model=f"ollama/{MODEL_NAME}",
    base_url=OLLAMA_HOST,
    temperature=0.1, # Laskettu lämpötilaa tarkkuuden parantamiseksi
    max_tokens=4096,
)

# === Työkalusetit ===
koodaus_tools = [run_python, run_shell, read_file, write_file, list_files]
data_tools = [query_duckdb, inspect_schema, run_python, read_file, write_file, list_files]
hallinta_tools = [list_files, read_file, write_file]

# === Agentit projektikohtaisella taustatarinalla ===

projektipaallikko = Agent(
    role="UWB-projektipäällikkö",
    goal="Koordinoi myymäläanalytiikan kehitystä ja varmista datan laatu",
    backstory=(
        "Olet asiantuntija vähittäiskaupan analytiikkaprojekteissa. "
        "Tiedät, että projektissa on käytössä store.db (DuckDB) ja store_config.py. "
        "Varmistat, että koodaaja ja analyytikko noudattavat projektin rakenteita."
    ),
    llm=llm,
    tools=hallinta_tools,
    verbose=True,
    allow_delegation=True
)

koodaaja = Agent(
    role="Python-insinööri",
    goal="Toteuta puhdistuslogiikkaa ja laskentaskriptejä",
    backstory=(
        "Erikoistut Pythoniin ja datan muokkaamiseen. "
        "Käytät aina 'config/store_config.py' -tiedostoa koordinaattimuunnosten pohjana. "
        "Kirjoitat koodia 'workspace/'-kansioon ja testaat sen ennen luovutusta."
    ),
    llm=llm,
    tools=koodaus_tools,
    verbose=True
)

analyytikko = Agent(
    role="IoT-Data-analyytikko",
    goal="Analysoi asiakasvirtoja ja viipymäaikoja 'Zone'- ja 'Quality'-tauluista",
    backstory=(
        "Olet mestari SQL-kyselyissä. Tiedät, että 'Zone'-taulussa on raakadata (10M riviä) "
        "ja 'Quality'-taulussa on puhdistettu data. Osaat laskea viipymät (dwell time) "
        "ja tunnistaa ruuhkautuvat osastot."
    ),
    llm=llm,
    tools=data_tools,
    verbose=True
)

# === Tehtävien määrittely ===

def build_crew(task_description: str) -> Crew:
    suunnittelu = Task(
        description=(
            f"Luo suunnitelma tehtävälle: {task_description}. "
            "Tarkista ensin 'inspect_schema'-työkalulla tietokannan rakenne "
            "ja 'list_files'-työkalulla olemassa olevat skriptit."
        ),
        expected_output="Askel-askeleelta etenevä suunnitelma analyysille tai koodaukselle.",
        agent=projektipaallikko,
    )

    toteutus = Task(
        description=(
            "Suorita tarvittava koodaus tai SQL-analyysi. "
            "Jos kyseessä on analyysi, tallenna tulokset CSV-tiedostona workspaceen. "
            "Jos kyseessä on koodi, varmista että se importtaa store_config:in oikein."
        ),
        expected_output="Valmiit analyysitulokset tai toimiva skripti tallennettuna.",
        agent=koodaaja, # Koodaaja ja analyytikko voivat jakaa tätä riippuen tarpeesta
    )

    yhteenveto = Task(
        description=(
            "Tee loppuraportti. Kerro mitä havaintoja teit datasta (esim. vilkkaimmat osastot) "
            "ja missä tiedostot sijaitsevat."
        ),
        expected_output="Liiketoimintalähtöinen raportti tuloksista.",
        agent=analyytikko,
    )

    return Crew(
        agents=[projektipaallikko, koodaaja, analyytikko],
        tasks=[suunnittelu, toteutus, yhteenveto],
        process=Process.sequential,
        verbose=True,
    )

# ... (main-funktio pysyy samana kuin aiemmin) ...import os
import sys
from crewai import LLM, Agent, Crew, Process, Task

# Varmistetaan että importit löytyvät vaikka skripti ajetaan eri kansioista
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Tuodaan työkalut
from tools.code_tools import run_python, run_shell
from tools.duckdb_tools import query_duckdb, inspect_schema 
from tools.file_tools import list_files, read_file, write_file

# === LLM-konfiguraatio ===
# Huom: Jos ajat tätä natiivisti (ei Docker), localhost on yleensä oikea osoite
MODEL_NAME = os.environ.get("OLLAMA_MODEL", "qwen2.5-coder:7b") # Käytetään varmuudella olemassa olevaa mallia
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")

llm = LLM(
    model=f"ollama/{MODEL_NAME}",
    base_url=OLLAMA_HOST,
    temperature=0.1,
    max_tokens=4096,
)

# === Agentit ===
projektipaallikko = Agent(
    role="UWB-projektipäällikkö",
    goal="Koordinoi myymäläanalytiikan kehitystä ja varmista datan laatu",
    backstory="Asiantuntija joka tietää että projektissa on store.db ja store_config.py.",
    llm=llm,
    tools=[list_files, read_file, write_file],
    verbose=True,
    allow_delegation=True
)

koodaaja = Agent(
    role="Python-insinööri",
    goal="Toteuta puhdistuslogiikkaa ja laskentaskriptejä",
    backstory="Python-kehittäjä joka käyttää 'config/store_config.py' asetuksia.",
    llm=llm,
    tools=[run_python, run_shell, read_file, write_file, list_files],
    verbose=True
)

analyytikko = Agent(
    role="IoT-Data-analyytikko",
    goal="Analysoi asiakasvirtoja Zone- ja Quality-tauluista",
    backstory="SQL-mestari joka analysoi 10M rivin Zone-taulua.",
    llm=llm,
    tools=[query_duckdb, inspect_schema, run_python, read_file, write_file, list_files],
    verbose=True
)

def build_crew(task_description: str) -> Crew:
    return Crew(
        agents=[projektipaallikko, koodaaja, analyytikko],
        tasks=[
            Task(
                description=f"Suunnittele ja toteuta: {task_description}",
                expected_output="Valmis analyysi tai koodi ja yhteenveto tuloksista.",
                agent=projektipaallikko
            )
        ],
        process=Process.sequential,
        verbose=True,
    )

def main():
    # Kysytään tehtävä jos sitä ei annettu komentoriviltä
    if len(sys.argv) > 1:
        task = " ".join(sys.argv[1:])
    else:
        task = input("Mitä tiimin pitäisi tehdä? (esim. 'Listaa taulut') > ")
    
    if not task:
        print("Ei tehtävää, lopetetaan.")
        return

    print(f"\n🚀 Aloitetaan tehtävä: {task}\n")
    crew = build_crew(task)
    result = crew.kickoff()
    
    print("\n" + "="*50)
    print("LOPPUTULOS:")
    print(result)
    print("="*50)

if __name__ == "__main__":
    main()