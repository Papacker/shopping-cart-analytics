"""
Backend - FastAPI Port 8000
Vastaa Excalidraw-kaavion 'Backend' kerrosta.
"""

import base64
import datetime
import io
import json
import os
import sys
import time
import traceback
from pathlib import Path
from typing import Optional, List, Dict, Any

import duckdb
import matplotlib
import numpy as np
import requests
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
from pydantic import BaseModel

# Asetetaan Matplotlib backend ennen pyplotin tuontia
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

# Paikalliset tuonnit
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agentti.crew import build_dynamic_chat_crew


# ==========================================
# 1. VAKIOT JA KONFIGURAATIOT
# ==========================================

PROXY_PATH = "/@Papacker/team-2-laitetaan-parastamme.coder/apps/code-server/proxy/8000"
WORKSPACE_DIR = PROJECT_ROOT / "agentti" / "workspace"
STATUS_FILE = WORKSPACE_DIR / "report_status.json"
REPORT_FILE = WORKSPACE_DIR / "asiakasraportti.md"
DB_PATH = str(PROJECT_ROOT / "database" / "store.db")
FLOOR_PLAN_PATH = str(PROJECT_ROOT / "images" / "kauppa.jpg")
OLLAMA_API_URL = "http://127.0.0.1:11434/api/generate"

WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)

# ==========================================
# 2. FASTAPI ALUSTUS JA MALLIT
# ==========================================

app = FastAPI(
    title="Tekoälyagentin FastAPI Backend",
    root_path=PROXY_PATH,
    docs_url="/docs",
    openapi_url="/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    model: str = "llama3.1:8b" # Vaihdettu vastaamaan nykyistä mallianne
    context: str = "Agenttichat"

class ReportRequest(BaseModel):
    model: str = "qwen2.5-coder:7b" # Vaihdettu vastaamaan nykyistä mallianne

# ==========================================
# 3. APUFUNKTIOT (Services)
# ==========================================

def update_status(
    generating: bool, 
    current_step: str, 
    reasoning: str = None, 
    report_content: str = None, 
    image_b64: str = None
) -> None:
    """Päivittää asynkronisen tilan, jota Frontend lukee."""
    try:
        status_data = {}
        if STATUS_FILE.exists():
            try:
                with open(STATUS_FILE, "r", encoding="utf-8") as f:
                    status_data = json.load(f)
            except json.JSONDecodeError:
                pass # Jos tiedosto oli hetkellisesti tyhjä tai lukossa
        
        reasoning_steps = status_data.get("reasoning_steps", [])
        if reasoning and (not reasoning_steps or reasoning_steps[-1] != reasoning):
            # Lisätään aikaleima
            timestamp = datetime.datetime.now().strftime('%H:%M:%S')
            reasoning_steps.append(f"[{timestamp}] {reasoning}")
        
        new_status = {
            "generating": generating,
            "current_step": current_step,
            "reasoning_steps": reasoning_steps,
            "report_content": report_content or status_data.get("report_content"),
            "image_b64": image_b64 or status_data.get("image_b64"),
            "last_updated": datetime.datetime.now().isoformat()
        }
        
        with open(STATUS_FILE, "w", encoding="utf-8") as f:
            json.dump(new_status, f, ensure_ascii=False, indent=2)
            
    except Exception as e:
        print(f"[Backend] Tilan päivitys epäonnistui: {e}")

def run_duckdb_query() -> Dict[str, Any]:
    """Suorittaa analyysikyselyt DuckDB-tietokantaan."""
    if not Path(DB_PATH).exists():
        return {"error": "DuckDB-tietokantaa ei löytynyt."}
        
    try:
        with duckdb.connect(DB_PATH, read_only=True) as con:
            res = con.execute("SELECT COUNT(DISTINCT visit_id), AVG(duration_seconds)/60.0 FROM Visit").fetchone()
            df_hours = con.execute("SELECT EXTRACT(HOUR FROM start_time) as hour, COUNT(*) as count FROM Visit GROUP BY hour ORDER BY count DESC LIMIT 3").fetchdf()
            df_quality = con.execute("SELECT reason, COUNT(*) as count FROM Quality WHERE is_valid=False GROUP BY reason ORDER BY count DESC LIMIT 3").fetchdf()
            
        return {
            "yhteenveto": {"vierailut": res[0] or 0, "keskikesto_min": round(res[1] or 0, 1)},
            "ruuhkat": df_hours.to_dict(orient="records"),
            "poikkeamat": df_quality.to_dict(orient="records")
        }
    except Exception as e:
        return {"error": str(e)}

def generate_heatmap_overlay() -> str:
    """Generoi UWB-heatmapin ja palauttaa sen base64-enkoodattuna."""
    with duckdb.connect(DB_PATH, read_only=True) as con:
        df = con.execute("SELECT x, y FROM Zone").fetchdf()

    if df.empty:
        raise ValueError("Ei dataa heatmapin luontiin.")

    img = Image.open(FLOOR_PLAN_PATH)
    img_w, img_h = img.size

    x_min, x_max = df["x"].min(), df["x"].max()
    y_min, y_max = df["y"].min(), df["y"].max()

    px = ((df["x"] - x_min) / (x_max - x_min) * img_w).astype(int).clip(0, img_w - 1)
    py = ((1 - (df["y"] - y_min) / (y_max - y_min)) * img_h).astype(int).clip(0, img_h - 1)

    heatmap, _, _ = np.histogram2d(px, py, bins=[120, 80], range=[[0, img_w], [0, img_h]])
    heatmap = heatmap.T

    fig, ax = plt.subplots(figsize=(16, 10), dpi=120)
    ax.imshow(img, extent=[0, img_w, 0, img_h], origin="upper", aspect="auto")

    masked = np.ma.masked_where(heatmap < 5, heatmap) 
    im = ax.imshow(
        masked, extent=[0, img_w, 0, img_h], origin="lower",
        cmap="plasma", alpha=0.65,
        norm=mcolors.PowerNorm(gamma=0.4, vmin=5, vmax=heatmap.max()),
        aspect="auto"
    )
    
    plt.colorbar(im, ax=ax, fraction=0.02, pad=0.01).set_label("Paikannuspisteiden tiheys", fontsize=11)
    ax.set_title("Kärryjen liikkuminen myymälässä – UWB Heatmap", fontsize=14, pad=12)
    ax.axis("off")
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight", dpi=120)
    plt.close(fig)
    buf.seek(0)
    
    return base64.b64encode(buf.read()).decode("utf-8")

# ==========================================
# 4. TAUSTAPROSESSIT (Background Tasks)
# ==========================================

def agent_task_runner(model_name: str) -> None:
    """Taustatehtävä, joka hakee datan ja pyytää Ollamaa kirjoittamaan raportin."""
    try:
        update_status(generating=True, current_step="Aloitetaan", reasoning="AI Agent käynnistetty.")
        
        # 1. SQL Kysely
        update_status(generating=True, current_step="Datakysely", reasoning="Suoritetaan SQL-kysely DuckDB:hen...")
        context_data = run_duckdb_query()
        
        # 2. Tarkista peruutus
        with open(STATUS_FILE, "r", encoding="utf-8") as f:
            if not json.load(f).get("generating", True):
                return
            
        update_status(generating=True, current_step="LLM Analyysi", reasoning="Odotetaan Ollaman vastausta...")
        
        prompt = f"""Olet data-analyytikko. Kirjoita lyhyt asiakasraportti Markdownilla tästä datasta:
        {json.dumps(context_data, indent=2)}
        Käytä väliotsikoita ja tee 3-5 fiksua huomiota."""
        
        report_content = ""
        try:
            res = requests.post(
                OLLAMA_API_URL,
                json={"model": model_name, "prompt": prompt, "stream": False},
                timeout=120 # Nostettu aikakatkaisu paikallisille malleille
            )
            if res.status_code == 200:
                report_content = res.json().get("response", "")
        except requests.RequestException as e:
            print(f"[Backend] Ollama virhe: {e}")
            
        if not report_content:
            report_content = "## ⚠️ Virhe: Kielimalli ei vastannut ajoissa."
        
        with open(REPORT_FILE, "w", encoding="utf-8") as f:
            f.write(report_content)
            
        update_status(generating=False, current_step="Valmis", reasoning="Raportti on valmis.", report_content=report_content)
        
    except Exception as exc:
        traceback.print_exc()
        update_status(generating=False, current_step="Virhe", reasoning=f"Kriittinen virhe: {exc}")

# ==========================================
# 5. API-REITIT (Endpoints)
# ==========================================

@app.get("/")
async def root():
    return {"message": "Backend is online", "proxy_root": PROXY_PATH}

@app.post("/api/generate-report")
async def api_generate_report(req: ReportRequest, background_tasks: BackgroundTasks):
    update_status(generating=True, current_step="Lisätään jonoon", reasoning="Käyttäjä input vastaanotettu.")
    background_tasks.add_task(agent_task_runner, req.model)
    return {"status": "accepted"}

@app.get("/api/report-status")
async def api_report_status():
    if not STATUS_FILE.exists():
        return {"generating": False, "current_step": "Ei aloitettu", "reasoning_steps": [], "report_content": None}
    try:
        with open(STATUS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {"generating": True, "current_step": "Ladataan...", "reasoning_steps": []}

@app.post("/api/cancel-report")
async def api_cancel_report():
    update_status(generating=False, current_step="Peruutettu", reasoning="Käyttäjä peruutti toiminnon.")
    return {"status": "cancelled"}

@app.post("/api/chat")
async def api_chat(req: ChatRequest, background_tasks: BackgroundTasks):
    is_heatmap = any(kw in req.message.lower() for kw in ["heatmap", "visuali", "kartta", "reitti", "koordinaatti"])
    update_status(generating=True, current_step="Aloitetaan", reasoning="Tekoälytiimi on herätetty...")

    def run_crew_task():
        try:
            if is_heatmap:
                update_status(generating=True, current_step="Visualisoidaan", reasoning="Piirretään UWB-dataa...")
                img_b64 = generate_heatmap_overlay()
                update_status(
                    generating=False, current_step="Valmis", reasoning="Heatmap valmis!",
                    report_content="## 🗺️ UWB Heatmap\n\nKirkkaat alueet ovat suosituimpia reittejä.",
                    image_b64=img_b64
                )
            else:
                crew = build_dynamic_chat_crew(task_description=req.message, model_name=req.model)
                update_status(generating=True, current_step="Analyysi käynnissä", reasoning="Agentit perkaavat dataa...")
                result = crew.kickoff()
                update_status(generating=False, current_step="Valmis", reasoning="Analyysi valmistui!", report_content=result.raw)
        except Exception as e:
            update_status(generating=False, current_step="Virhe", reasoning=f"Kriittinen virhe: {e}")

    background_tasks.add_task(run_crew_task)
    return {"status": "started"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.backend:app", host="0.0.0.0", port=8000, reload=True)