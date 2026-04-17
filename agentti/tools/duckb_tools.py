"""
duckdb_tools.py - Agenttien yhteys projektin store.db-tietokantaan.
"""

import duckdb
import os
from pathlib import Path
from crewai.tools import tool

# 1. MÄÄRITETÄÄN POLKU PROJEKTIN TIETOKANTAAN
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "database" / "store.db"

def get_connection():
    """
    Avaa yhteyden olemassa olevaan tietokantaan.
    Käytetään read_only=True, jotta Streamlit ja agentit voivat käyttää kantaa yhtä aikaa.
    """
    if not DB_PATH.exists():
        # Jos kantaa ei ole, luodaan uusi (esim. testejä varten)
        return duckdb.connect(str(DB_PATH))
    return duckdb.connect(str(DB_PATH), read_only=True)

@tool("query_duckdb")
def query_duckdb(sql: str) -> str:
    """
    Ajaa SQL-kyselyn projektin 'store.db'-tietokannassa. 
    Käytä tätä analysoimaan 'Zone'-taulua (10M riviä) ja 'Quality'-taulua.
    Palauttaa tulokset tekstimuodossa.
    """
    try:
        # Avataan ja suljetaan yhteys per kysely, jotta vältetään lukitukset
        with get_connection() as con:
            result = con.execute(sql)
            if result.description:
                columns = [d[0] for d in result.description]
                rows = result.fetchmany(50) # Rajataan 50 riviin, ettei agentti huku dataan
                
                header = " | ".join(columns)
                lines = [header, "-" * len(header)]
                for row in rows:
                    lines.append(" | ".join(str(v) for v in row))
                
                if len(rows) == 50:
                    lines.append("\n... (näytetään vain 50 ensimmäistä riviä huomautuksena)")
                return "\n".join(lines)
            return "OK: Komento suoritettu (ei palautettuja rivejä)."
    except Exception as e:
        return f"SQL VIRHE: {e}"

@tool("inspect_schema")
def inspect_schema() -> str:
    """
    Palauttaa tietokannan taulut ja niiden sarakkeet. 
    Käytä tätä aina ensimmäisenä, jotta tiedät mitä dataa on saatavilla.
    """
    try:
        with get_connection() as con:
            tables = con.execute("SHOW TABLES").fetchall()
            if not tables:
                return "Tietokanta on tyhjä."
            
            output = []
            for (table_name,) in tables:
                cols = con.execute(f"DESCRIBE {table_name}").fetchall()
                col_info = ", ".join([f"{c[0]} ({c[1]})" for c in cols])
                output.append(f"Taulu: {table_name}\nSarakkeet: {col_info}\n")
            return "\n".join(output)
    except Exception as e:
        return f"VIRHE skeeman tarkistuksessa: {e}"