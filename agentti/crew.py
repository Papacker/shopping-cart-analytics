import os
import sys
from crewai import LLM, Agent, Crew, Process, Task

# Lisätään polku, jotta tools-kansio löytyy varmasti
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Tuodaan aiemmin optimoidut työkalut
from tools import (
    run_python, run_shell, 
    query_duckdb, inspect_schema, 
    list_files, read_file, write_file
)

# === LLM-konfiguraatio ===
MODEL_NAME = os.environ.get("OLLAMA_MODEL", "qwen2.5-coder:7b")
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
koodaus_tools = [run_python, run_shell, read_file, write_file, list_files]

projektipaallikko = Agent(
    role="UWB-analyysijohtaja",
    goal="Hae taulujen nimet ja tilastot suoraan tietokannasta.",
    backstory=(
        "Olet analyysijohtaja. Sinulla on suora yhteys tietokantaan. "
        "ÄLÄ yritä etsiä store.db-tiedostoa list_files-työkalulla. "
        "Käytä AINA 'inspect_schema'-työkalua nähdäksesi taulut."
    ),
    llm=llm,
    tools=pm_tools, 
    verbose=True,
    allow_delegation=True
)

analyytikko = Agent(
    role="UWB-analyytikko",
    goal="Listaa taulut tietokannasta",
    backstory="Olet robotti joka käyttää vain query_duckdb-työkalua. Älä etsi tiedostoja.",
    llm=llm,
    tools=[query_duckdb, inspect_schema], 
    verbose=True,
    max_iter=3
)
koodaaja = Agent(
    role="Python-insinööri",
    goal="Toteuta laskentaa ja visualisointeja",
    backstory="Python-kehittäjä. Tallennat tulokset workspace-kansioon.",
    llm=llm,
    tools=koodaus_tools,
    verbose=True
)

liiketoiminta-agentti = Agent( 
    role="Ali Baba",
    goal="Toteuta laskentaa ja visualisointeja",
    backstory="Python-kehittäjä. Tallennat tulokset workspace-kansioon.",
    llm=llm,
    tools=koodaus_tools,
    verbose=True
)
testaaja-agentti = Agent(
    role="Testaaja",
    goal="Testaa koodaajan koodia, eli varmista että se toimii ja tuottaa halutun tuloksen",
    backstory="Testaaja. Tallennat tulokset workspace-kansioon.",
    llm=llm,
    tools=koodaus_tools,
    verbose=True
)

# === Tehtävän hallinta ===

def build_crew(task_description: str) -> Crew:
    tehtava = Task(
        description=(
            f"TEHTÄVÄ: {task_description}\n\n"
            "OHJEET:\n"
            "1. ÄLÄ etsi ./tmp tai ./temp hakemistoja.\n"
            "2. Käytä heti 'inspect_schema'-työkalua nähdäksesi taulut.\n"
            "3. Suorita SQL-kyselyt ja anna selkeä vastaus."
        ),
        expected_output="Selkeä vastaus tai analyysiraportti tietokannan perusteella.",
        agent=projektipaallikko,
        output_file="agentti/workspace/raportti.md"
    )

    return Crew(
        agents=[projektipaallikko, analyytikko, koodaaja],
        tasks=[tehtava],
        process=Process.sequential,
        verbose=True,
    )

def main():
    if len(sys.argv) > 1:
        task = " ".join(sys.argv[1:])
    else:
        task = input("Mitä tiimin pitäisi tehdä? > ")
    
    if not task:
        return

    print(f"\n🚀 Käynnistetään UWB-analyysi osoitteessa {OLLAMA_HOST}...")
    crew = build_crew(task)
    
    try:
        result = crew.kickoff()
        print("\n" + "="*50)
        print("LOPPUTULOS:")
        print(result)
        print("="*50)
    except Exception as e:
        print(f"💥 Virhe: {e}")

if __name__ == "__main__":
    main()