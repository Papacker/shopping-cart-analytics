import pytest
import duckdb
import os
from main import initialize_database

def test_initialize_database(tmp_path):
    # Luodaan väliaikainen tietokanta ja skeematiedosto
    db_path = tmp_path / "test_store.db"
    schema_path = tmp_path / "schema.sql"
    
    schema_content = """
    CREATE TABLE IF NOT EXISTS Visit (visit_id VARCHAR, node_id VARCHAR);
    """
    schema_path.write_text(schema_content)
    
    con = duckdb.connect(str(db_path))
    initialize_database(con, str(schema_path))
    
    # Tarkistetaan, että taulu luotiin
    tables = con.execute("SHOW TABLES").fetchall()
    assert ('Visit',) in tables
    con.close()