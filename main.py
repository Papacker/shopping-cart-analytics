import os
import glob
import time
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor

import duckdb
import pandas as pd

# Tuodaan omat moduulit
from config.store_config import store_config
from src.processor import StoreDataCleaner


def initialize_database(db_path, schema_path):
    """Alustaa tietokannan rakenteet vain jos tarpeen."""
    if not os.path.exists(schema_path):
        return

    import time
    for i in range(5):
        try:
            with duckdb.connect(db_path, config={'access_mode': 'read_write'}) as con:
                with open(schema_path, 'r') as f:
                    con.execute(f.read())
            print("✅ Tietokannan rakenteet varmistettu.")
            return
        except Exception as e:
            if i < 4:
                time.sleep(0.5)
                continue
            print(f"⚠️ Tietokannan alustus herjaa (voi johtua lukituksesta): {e}")


def process_file_task(file_path, config, df_categories, processed_dir):
    """
    Yksittäisen tiedoston käsittelylogiikka rinnakkaisajoa varten.
    Suoritetaan omassa prosessissaan.
    """
    file_name = os.path.basename(file_path)
    cleaner = StoreDataCleaner(config)
    processed_dir = Path(processed_dir)

    try:
        # 1. LUKU (Käytetään in-memory DuckDB:tä nopeaan lukemiseen)
        con_mem = duckdb.connect()
        con_mem.execute("SET enable_progress_bar = false") # Terminaalihygienia
        con_mem.execute("SET threads = 4") # Rajoitetaan säikeet per prosessi
        df_raw = con_mem.execute(f"SELECT * FROM read_csv_auto('{file_path}')").df()
        file_raw_count = len(df_raw)
        con_mem.close()

        if df_raw.empty:
            return None

        # 2. PUHDISTUS
        df_spatial, _ = cleaner.clean_spatial(df_raw)
        df_sessionized = cleaner.sessionize(df_spatial)
        df_motion_cleaned = cleaner.clean_motion(df_sessionized)
        df_final, visit_metrics, quality_logs = cleaner.validate_sessions(df_motion_cleaned)

        # Lasketaan osastovierailut
        df_zone_visits = cleaner.calculate_zone_visits(df_final, df_categories)

        # 3. TALLENNUS (Tehdään rinnakkain tässä prosessissa)
        if not df_final.empty:
            parquet_path = processed_dir / file_name.replace('.csv', '.parquet')
            df_final.to_parquet(parquet_path, index=False)

        # Kerätään hylkäyssyyt tilastointia varten
        rejections = {}
        if not quality_logs.empty:
            rejections = quality_logs[quality_logs['is_valid'] == False]['reason'].value_counts().to_dict()

        return {
            "file_name": file_name,
            "df_final": df_final,
            "visit_metrics": visit_metrics,
            "quality_logs": quality_logs,
            "df_zone_visits": df_zone_visits,
            "raw_count": file_raw_count,
            "cleaned_count": len(df_final),
            "rejections": rejections
        }
    except Exception as e:
        return {"file_name": file_name, "error": str(e)}


def run_etl():
    """
    Pääohjelma, joka hallitsee koko ETL-prosessia:
    Rinnakkaisajo, Parquet-tallennus ja lopullinen atominen tietokantakirjoitus.
    Palauttaa dict:n tilastoilla tai None virheen sattuessa.
    """
    start_time_total = time.time()
    BASE_DIR = Path(__file__).parent
    DB_PATH = str(BASE_DIR / "database" / "store.db")
    SCHEMA_PATH = str(BASE_DIR / "database" / "schema_duckdb.sql")
    RAW_DIR = BASE_DIR / "data" / "raw"
    PROCESSED_DIR = BASE_DIR / "data" / "processed"

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Alustetaan kanta ja päivitetään kategoriat
    initialize_database(DB_PATH, SCHEMA_PATH)

    cleaner = StoreDataCleaner(store_config)
    df_categories = cleaner.get_categories_df()

    with duckdb.connect(DB_PATH) as con:
        con.execute("DELETE FROM Categories")
        if not df_categories.empty:
            # Muutetaan sarakkeet vastaamaan skeemaa (x1->x_min, jne.)
            df_cats_to_db = df_categories.rename(columns={
                'x1': 'x_min', 'x2': 'x_max',
                'y1': 'y_min', 'y2': 'y_max'
            })
            con.execute("INSERT INTO Categories SELECT * FROM df_cats_to_db")

    # 2. Etsitään tiedostot
    all_files = glob.glob(str(RAW_DIR / "*.csv"))
    raw_files = []
    for f in all_files:
        p_path = PROCESSED_DIR / os.path.basename(f).replace('.csv', '.parquet')
        if not p_path.exists():
            raw_files.append(f)

    if not raw_files:
        # Tarkistetaan onko kanta oikeasti tyhjä (jos on, pakotetaan ajo)
        try:
            with duckdb.connect(DB_PATH) as con:
                count = con.execute("SELECT COUNT(*) FROM Visit").fetchone()[0]
            if count > 0:
                print("ℹ️ Kaikki tiedostot on jo prosessoitu.")
                return {"status": "already_processed", "new_files_processed": 0}
            else:
                print("⚠️ Tietokanta on tyhjä. Pakotetaan kaikkien tiedostojen uudelleenkäsittely...")
                raw_files = all_files
        except:
            # Jos taulua ei ole vielä olemassa, sekin tarkoittaa että pitää ajaa
            raw_files = all_files

    num_workers = min(len(raw_files), os.cpu_count(), 6)
    if num_workers < 1:
        num_workers = 1

    print(f"🚀 Aloitetaan rinnakkaisajo (spawn): {len(raw_files)} tiedostoa, {num_workers} prosessia käytössä...", flush=True)

    # Kerätään kaikki tulokset listoihin ennen tallennusta
    all_df_final = []
    all_visit_metrics = []
    all_quality_logs = []
    all_df_zone_visits = []

    summary_stats = {
        "new_files_processed": 0,
        "total_raw_rows": 0,
        "total_cleaned_rows": 0,
        "rejections": {}
    }

    # 3. RINNAKKAISLASKENTA (CPU-intensiivinen osuus)
    import multiprocessing
    ctx = multiprocessing.get_context('spawn')

    with ProcessPoolExecutor(max_workers=num_workers, mp_context=ctx) as executor:
        futures = [executor.submit(process_file_task, f, store_config, df_categories, str(PROCESSED_DIR)) for f in raw_files]

        for future in futures:
            try:
                result = future.result()
            except Exception as e:
                print(f"❌ Kriittinen virhe prosessissa: {e}")
                continue
            if result is None or "error" in result:
                if result and "error" in result:
                    print(f"❌ Virhe tiedostossa {result['file_name']}: {result['error']}")
                continue

            file_name = result["file_name"]

            # Kerätään dataframet listoihin
            if not result["df_final"].empty:
                all_df_final.append(result["df_final"])

            if not result["visit_metrics"].empty:
                all_visit_metrics.append(result["visit_metrics"])

            if not result["quality_logs"].empty:
                all_quality_logs.append(result["quality_logs"])

            if not result["df_zone_visits"].empty:
                all_df_zone_visits.append(result["df_zone_visits"])

            # Tilastot
            summary_stats["new_files_processed"] += 1
            summary_stats["total_raw_rows"] += result["raw_count"]
            summary_stats["total_cleaned_rows"] += result["cleaned_count"]
            for reason, count in result["rejections"].items():
                summary_stats["rejections"][reason] = summary_stats["rejections"].get(reason, 0) + count

            print(f"⏳ Prosessoitu: {file_name}", flush=True)
            print(f"   📊 Rivejä: {result['raw_count']:,} -> {result['cleaned_count']:,}", flush=True)
            print(f"   🛒 Visit: {len(result['visit_metrics'])} | 📍 ZoneVisit: {len(result['df_zone_visits'])}", flush=True)
            if result.get("rejections"):
                rej_str = ", ".join([f"{k}: {v} kpl" for k, v in result["rejections"].items()])
                print(f"   ⚠️ Hylätyt: {rej_str}", flush=True)
            print("-" * 30, flush=True)

    # 4. ATOMINEN TALLENNUS (Vain yksi lyhyt tietokantalukko lopuksi)
    if summary_stats["new_files_processed"] > 0:
        print(f"\n💾 Tallennetaan tulokset tietokantaan...", flush=True)
        max_db_retries = 10
        save_success = False
        for db_i in range(max_db_retries):
            try:
                with duckdb.connect(DB_PATH, config={'access_mode': 'read_write'}) as con:
                    con.execute("BEGIN TRANSACTION")

                    if all_df_final:
                        df_final_all = pd.concat(all_df_final)
                        zone_df = df_final_all[['final_sid', 'x', 'y', 'timestamp']].rename(columns={'final_sid': 'visit_id'})
                        con.execute("INSERT INTO Zone (visit_id, x, y, timestamp) SELECT * FROM zone_df")

                        node_ids = df_final_all[['node_id']].drop_duplicates()
                        node_ids['description'] = 'kärry_' + node_ids['node_id'].astype(str)
                        con.execute("INSERT OR IGNORE INTO ShoppingCart (node_id, description) SELECT node_id, description FROM node_ids")

                    if all_visit_metrics:
                        visit_metrics_all = pd.concat(all_visit_metrics)
                        con.execute("""
                            INSERT INTO Visit (visit_id, node_id, start_time, end_time, duration_seconds)
                            SELECT visit_id, node_id, start_time, end_time, duration_seconds FROM visit_metrics_all
                        """)

                    if all_quality_logs:
                        quality_logs_all = pd.concat(all_quality_logs)
                        con.execute("""
                            INSERT INTO Quality (node_id, is_valid, reason, more_info)
                            SELECT node_id, is_valid, reason, more_info FROM quality_logs_all
                        """)

                    if all_df_zone_visits:
                        zone_visits_all = pd.concat(all_df_zone_visits)
                        con.execute("""
                            INSERT INTO ZoneVisit (visit_id, category_id, start_time, end_time)
                            SELECT visit_id, category_id, start_time, end_time FROM zone_visits_all
                        """)

                    con.execute("COMMIT")
                print("✅ Kaikki tulokset tallennettu onnistuneesti.", flush=True)
                save_success = True
                break
            except Exception as e:
                if "lock" in str(e).lower() or "configuration" in str(e).lower():
                    if db_i < max_db_retries - 1:
                        time.sleep(1)
                        continue
                print(f"❌ Kriittinen tallennusvirhe: {e}")
                return None
        if not save_success:
            return None

    # --- LOPPURAPORTTI ---
    end_time_total = time.time()
    total_duration = end_time_total - start_time_total

    summary_stats["duration"] = total_duration
    summary_stats["status"] = "success"

    print("\n" + "="*45)
    print("📊 BATCH ETL-AJON YHTEENVETO")
    print("="*45)
    print(f"Suoritusaika:              {total_duration:.1f} sekuntia")
    print(f"Käsitellyt tiedostot:      {summary_stats['new_files_processed']} kpl")
    print(f"Raakarivejä yhteensä:     {summary_stats['total_raw_rows']:,} kpl")
    print(f"Hyväksyttyjä rivejä:      {summary_stats['total_cleaned_rows']:,} kpl")

    if summary_stats["rejections"]:
        print("-" * 45)
        print("Hylkäyssyyt (Sessiot yhteensä):")
        for reason, count in summary_stats["rejections"].items():
            print(f"  • {reason:25}: {count} kpl")
    print("="*45 + "\n")

    return summary_stats


if __name__ == "__main__":
    import multiprocessing
    # 'spawn' on vakaampi DuckDB:n kanssa Linuxilla
    try:
        multiprocessing.set_start_method('spawn', force=True)
    except RuntimeError:
        pass
    run_etl()