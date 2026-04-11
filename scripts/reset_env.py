import os
import glob
from pathlib import Path

def reset_env():
    # 1. POLUT
    # Oletetaan, että skripti on projektin juuressa tai scripts-kansiossa
    BASE_DIR = Path(__file__).parent.parent
    DB_PATH = BASE_DIR / "database" / "store.db"
    PROCESSED_DIR = BASE_DIR / "data" / "processed"
    
    print("🧹 Käynnistetään ympäristön nollaus...")
    print("-" * 40)

    # 2. TIETOKANNAN POISTO
    if DB_PATH.exists():
        try:
            os.remove(DB_PATH)
            print(f"✅ Tietokanta poistettu: {DB_PATH}")
        except Exception as e:
            print(f"❌ Virhe tietokannan poistossa: {e}")
    else:
        print(f"ℹ️ Tietokantaa ei löytynyt (jo valmiiksi puhdas).")

    # 3. PROSESSOIDUN DATAN POISTO (Parquet & CSV)
    if PROCESSED_DIR.exists():
        # Etsitään kaikki tiedostot processed-kansiosta
        processed_files = glob.glob(str(PROCESSED_DIR / "*"))
        
        deleted_count = 0
        for f in processed_files:
            try:
                # Poistetaan vain tiedostot ja linkit, ei alikansioita
                if os.path.isfile(f) or os.path.islink(f):
                    os.remove(f)
                    deleted_count += 1
            except Exception as e:
                print(f"❌ Virhe tiedoston {f} poistossa: {e}")
        
        if deleted_count > 0:
            print(f"✅ Tyhjennetty processed-kansio: {deleted_count} tiedostoa poistettu.")
        else:
            print(f"ℹ️ Processed-kansio oli jo tyhjä.")
    else:
        print(f"⚠️ Varoitus: Kansiota {PROCESSED_DIR} ei löydy.")

    print("-" * 40)
    print("✨ Nollaus valmis. data/raw-kansion linkit ovat tallessa.")
    print("🚀 Voit nyt ajaa: uv run main.py")

if __name__ == "__main__":
    reset_env()