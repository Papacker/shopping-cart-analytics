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
    max_iter=3
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
    backstory="Python-kehittäjä. Tallennat tulokset workspace-kansioon.",
    llm=llm,
    tools=koodaus_tools,
    verbose=True
)
testaaja_agentti = Agent(
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
        agent=manager,
        output_file="agentti/workspace/raportti.md"
    )

    jls_extract_var = [manager, analyst, engineer]
    return Crew(
        agents=jls_extract_var,
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