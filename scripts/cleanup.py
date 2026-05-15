"""
Skripti järjestelmän välimuistien ja väliaikaisten tiedostojen puhdistamiseen.
Tämä vastaa kaavion 'Cleanup.py' kerrosta.
"""

import os
import shutil
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def clean_pycache():
    """Poistaa kaikki __pycache__ -hakemistot koko projektista."""
    print("🧹 Etsitään ja poistetaan __pycache__ -hakemistoja...")
    count = 0
    for root, dirs, files in os.walk(PROJECT_ROOT):
        for dir_name in dirs:
            if dir_name == "__pycache__":
                dir_path = os.path.join(root, dir_name)
                try:
                    shutil.rmtree(dir_path)
                    count += 1
                except Exception as e:
                    print(f"  Virhe poistaessa {dir_path}: {e}")
    print(f"✅ Poistettiin {count} välimuistihakemistoa.")

def clean_task_workspace():
    """Tyhjentää agentti/workspace -kansion väliaikaiset tulostiedostot."""
    print("🗑️ Tyhjennetään agentin työtila (Taskien ylläpito)...")
    workspace_dir = PROJECT_ROOT / "agentti" / "workspace"
    if workspace_dir.exists():
        count = 0
        for file in workspace_dir.iterdir():
            if file.is_file():
                try:
                    file.unlink()
                    count += 1
                except Exception as e:
                    print(f"  Virhe poistaessa {file}: {e}")
        print(f"✅ Tyhjennettiin {count} väliaikaistiedostoa työtilasta.")
    else:
        print("  Työtilaa ei löytynyt, ei puhdistettavaa.")

def clean_streamlit_cache():
    """Poistaa Streamlitin lokaalin välimuistin ~/.streamlit/cache."""
    print("🧼 Tyhjennetään Streamlitin välimuisti...")
    home = Path.home()
    streamlit_cache = home / ".streamlit" / "cache"
    if streamlit_cache.exists():
        try:
            shutil.rmtree(streamlit_cache)
            print("✅ Streamlit välimuisti poistettu.")
        except Exception as e:
            print(f"  Virhe poistaessa Streamlit välimuistia: {e}")
    else:
        print("  Streamlit välimuistia ei löytynyt.")

def main():
    print("="*50)
    print("JÄRJESTELMÄN PUHDISTUS (Cleanup.py)")
    print("="*50)
    clean_pycache()
    clean_task_workspace()
    clean_streamlit_cache()
    print("✨ Kaikki puhdistettu!")

if __name__ == "__main__":
    main()
