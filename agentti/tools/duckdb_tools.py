"""
DuckDB-tietokantatyökalut CrewAI-agentille.

Tämä moduuli tarjoaa kaksi työkalua:
  1. inspect_schema – näyttää tietokannan taulut ja sarakkeet
  2. query_duckdb – suorittaa SQL-kyselyn ja palauttaa tulokset listana
"""

import os
import sys
from crewai.tools import tool
from pydantic import BaseModel
from typing import Optional

# Varmistetaan, että duckdb on asennettu
try:
    import duckdb
except ImportError:
    print("Asennetaan duckdb...")
    os.system(f"{sys.executable} -m pip install duckdb -q")
    import duckdb


# Tietokannan polku – oletuksena projektin juuressa oleva database/store.db
def _get_db_path() -> str:
    """
    Päättele store.db:n sijainti.

    Prioriteetti:
      1. STORE_DB_PATH-ympäristömuuttuja
      2. ./database/store.db (agentti-kansion sisältä)
      3. ../database/store.db (projektin juuressa)
    """
    # 1. Ympäristömuuttuja
    env_path = os.environ.get("STORE_DB_PATH")
    if env_path and os.path.isfile(env_path):
        return os.path.abspath(env_path)

    # 2. ./database/store.db – tämä skripti luultavasti ajetaan agentti-kansiosta
    candidate = os.path.join(os.getcwd(), "database", "store.db")
    if os.path.isfile(candidate):
        return os.path.abspath(candidate)

    # 3. ../database/store.db – projektin juuri
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidate2 = os.path.join(script_dir, "..", "database", "store.db")
    if os.path.isfile(candidate2):
        return os.path.abspath(candidate2)

    # 4. Viimeinen oljenkorsi – absoluuttinen polku projektin juureen
    candidate3 = "/home/Papacker/code/projektiopinnot-1-datan-hallinta-laitetaan-parastamme/database/store.db"
    if os.path.isfile(candidate3):
        return candidate3

    # 5. Jos ei löydy, palautetaan oletus – duckdb luo uuden
    fallback = os.path.join(script_dir, "..", "database", "store.db")
    print(
        f"VAROITUS: store.db ei löytynyt. "
        f"Luodaan uusi: {os.path.abspath(fallback)}"
    )
    return os.path.abspath(fallback)


DB_PATH = _get_db_path()
print(f"--- DEBUG: DuckDB kytkeytyy polkuun: {DB_PATH} ---")


# ---------------------------------------------------------------------------
# CrewAI Tool -yhteensopivat funktiot
# ---------------------------------------------------------------------------

class InspectSchemaInput(BaseModel):
    pass

@tool("inspect_schema")
def inspect_schema() -> str:
    """
    Hakee DuckDB-tietokannan taulujen nimet ja sarakkeet.

    Returns:
        str: Ihmisluettava kuvaus tietokannan rakenteesta.
    """
    try:
        con = duckdb.connect(DB_PATH)
        # Haetaan taulujen nimet
        tables = con.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'main'"
        ).fetchall()

        if not tables:
            return "Tietokannassa ei ole tauluja."

        result_lines = ["Tietokannan taulut ja sarakkeet:\n"]
        for (table_name,) in tables:
            result_lines.append(f"\n📋 Taulu: {table_name}")
            columns = con.execute(
                f"SELECT column_name, data_type "
                f"FROM information_schema.columns "
                f"WHERE table_name = '{table_name}'"
            ).fetchall()
            for col_name, col_type in columns:
                result_lines.append(f"   - {col_name} ({col_type})")

        con.close()
        return "\n".join(result_lines)
    except Exception as e:
        return f"Virhe tietokannan rakenteen haussa: {e}"


class QueryDuckDBInput(BaseModel):
    sql: str

@tool("query_duckdb")
def query_duckdb(sql: str) -> str:
    """
    Suorittaa SQL-kyselyn DuckDB-tietokantaan ja palauttaa tulokset.

    Args:
        sql: SQL-kysely merkkijonona.

    Returns:
        str: Kyselyn tulokset muotoiltuna merkkijonona.
    """
    try:
        con = duckdb.connect(DB_PATH)
        result = con.execute(sql)
        rows = result.fetchall()

        if not rows:
            con.close()
            return "Kysely palautti 0 riviä."

        col_names = [desc[0] for desc in result.description]
        # Muotoillaan tulokset siistiksi taulukoksi
        output = []
        output.append(" | ".join(col_names))
        output.append("-" * len(" | ".join(col_names)))
        for row in rows:
            output.append(" | ".join(str(val) for val in row))

        con.close()
        return "\n".join(output)
    except Exception as e:
        return f"Virhe SQL-kyselyssä: {e}"
