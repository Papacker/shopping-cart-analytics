import os
import glob
import duckdb
import pandas as pd
from pathlib import Path

# Tuodaan omat moduulit
from config.store_config import store_config
from src.processor import StoreDataCleaner

def initialize_database(con, schema_path):
    if os.path.exists(schema_path):
        with open(schema_path, 'r') as f:
            con.execute(f.read())
        print("✅ Tietokannan rakenteet varmistettu.")

def run_etl():
    BASE_DIR = Path(__file__).parent
    DB_PATH = str(BASE_DIR / "database" / "store.db")
    SCHEMA_PATH = str(BASE_DIR / "database" / "schema_duckdb.sql")
    RAW_DIR = BASE_DIR / "data" / "raw"
    PROCESSED_DIR = BASE_DIR / "data" / "processed"

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect(DB_PATH)
    initialize_database(con, SCHEMA_PATH)
    cleaner = StoreDataCleaner(store_config)

    raw_files = glob.glob(str(RAW_DIR / "*.csv"))
    
    if not raw_files:
        print("ℹ️ Ei käsiteltäviä tiedostoja.")
        con.close()
        return

    # --- LASKURIT RIVIMÄÄRILLE ---
    total_raw_rows = 0
    total_cleaned_rows = 0
    new_files_processed = 0

    print(f"📂 Aloitetaan {len(raw_files)} tiedoston tarkistus...")

    for file_path in raw_files:
        file_name = os.path.basename(file_path)
        parquet_path = PROCESSED_DIR / file_name.replace('.csv', '.parquet')

        # Ohitetaan, jos parquet on jo olemassa
        if parquet_path.exists():
            continue

        try:
            # 1. LUKU
            df_raw = con.execute(f"SELECT * FROM read_csv_auto('{file_path}')").df()
            file_raw_count = len(df_raw)
            total_raw_rows += file_raw_count

            # 2. PUHDISTUS
            df_spatial, _ = cleaner.clean_spatial(df_raw)
            df_sessionized = cleaner.sessionize(df_spatial)
            df_final, visit_metrics, quality_logs = cleaner.validate_sessions(df_sessionized)
            
            file_cleaned_count = len(df_final)
            total_cleaned_rows += file_cleaned_count

            # 3. TALLENNUS PARQUET
            if not df_final.empty:
                df_final.to_parquet(parquet_path, index=False)

            # 4. TALLENNUS TIETOKANTAAN
            con.execute("BEGIN TRANSACTION")
            if not df_final.empty:
                zone_df = df_final[['final_sid', 'x', 'y', 'timestamp']].rename(columns={'final_sid': 'visit_id'})
                con.execute("INSERT INTO Zone (visit_id, x, y, timestamp) SELECT * FROM zone_df")
            
            if not visit_metrics.empty:
                visit_metrics['duration_seconds'] = (visit_metrics['kesto_min'] * 60).astype(int)
                con.execute("""
                    INSERT INTO Visit (visit_id, node_id, start_time, end_time, duration_seconds) 
                    SELECT visit_id, node_id, start_time, end_time, duration_seconds FROM visit_metrics
                """)

            if not quality_logs.empty:
                con.execute("""
                    INSERT INTO Quality (node_id, is_valid, reason, more_info) 
                    SELECT node_id, is_valid, reason, more_info FROM quality_logs
                """)
            con.execute("COMMIT")
            
            new_files_processed += 1
            print(f"✅ {file_name}: {file_raw_count:,} -> {file_cleaned_count:,} riviä")

        except Exception as e:
            con.execute("ROLLBACK")
            print(f"❌ Virhe tiedostossa {file_name}: {e}")

    # --- LOPPURAPORTTI ---
    print("\n" + "="*40)
    print("📊 ETL-AJON YHTEENVETO (Uudet tiedostot)")
    print("="*40)
    if new_files_processed > 0:
        print(f"Käsitellyt tiedostot:      {new_files_processed} kpl")
        print(f"Raakarivejä yhteensä:     {total_raw_rows:,} kpl")
        print(f"Puhdistettuja rivejä:     {total_cleaned_rows:,} kpl")
        
        ratio = (total_cleaned_rows / total_raw_rows * 100) if total_raw_rows > 0 else 0
        print(f"Puhdistetun datan osuus kokonaismäärästä:         {ratio:.2f} %")
    else:
        print("Kaikki tiedostot oli jo prosessoitu aiemmin.")
    print("="*40)
    
    con.close()

if __name__ == "__main__":
    run_etl()