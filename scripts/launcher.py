"""
Yhteinen käynnistin (launcher.py).
Vastaa Excalidraw-kaavion 'launcher.py' kerrosta.
"""

import sys
import time
import atexit
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

backend_process = None
frontend_process = None

def cleanup():
    """Sulkee prosessit skriptin poistuessa."""
    print("\n🛑 Varmistetaan rinnakkaisprosessien sulkeutuminen...")
    if backend_process and backend_process.poll() is None:
        backend_process.kill()
    if frontend_process and frontend_process.poll() is None:
        frontend_process.kill()
    print("✅ Prosessit suljettu.")

atexit.register(cleanup)

def free_port(port: int):
    """Vapauttaa macOS/Linux -ympäristössä roikkuvat portit."""
    try:
        res = subprocess.run(["lsof", "-ti", f":{port}"], capture_output=True, text=True)
        pids = res.stdout.strip().split()
        for pid in pids:
            if pid:
                print(f"⚠️ Vapautetaan varattu portti {port} (pid {pid})...")
                subprocess.run(["kill", "-9", pid], capture_output=True)
                time.sleep(0.5)
    except Exception:
        pass

def main():
    global backend_process, frontend_process

    print("🚀 LAUNCHER KÄYNNISTYY...")
    free_port(8000)
    free_port(8501)

    # Backend
    print("⚡ Käynnistetään FastAPI Backend (Port 8000)...")
    backend_cmd = [sys.executable, "-m", "uvicorn", "src.backend:app", "--host", "127.0.0.1", "--port", "8000", "--reload"]
    backend_process = subprocess.Popen(backend_cmd, cwd=str(PROJECT_ROOT))
    time.sleep(2)

    # Frontend
    print("🎨 Käynnistetään Streamlit Frontend (Port 8501)...")
    frontend_cmd = [sys.executable, "-m", "streamlit", "run", "src/app.py", "--server.port", "8501", "--server.address", "127.0.0.1"]
    frontend_process = subprocess.Popen(frontend_cmd, cwd=str(PROJECT_ROOT))
    
    print("\n✨ Järjestelmä on valmis! Voit sulkea sen painamalla Ctrl+C.")
    
    try:
        while True:
            time.sleep(1)
            if backend_process.poll() is not None or frontend_process.poll() is not None:
                print("⚠️ Jompikumpi prosessi kaatui. Sammutetaan...")
                break
    except KeyboardInterrupt:
        print("\n🛑 Pysäytetään...")

if __name__ == "__main__":
    main()
