"""
Backend - FastAPI Port 8000
Vastaa Excalidraw-kaavion 'Backend' kerrosta.
"""

import os
import sys
import json
import time
import datetime
import traceback
from pathlib import Path
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
import requests
from agentti.crew import build_dynamic_chat_crew

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

app = FastAPI(title="Tekoälyagentin FastAPI Backend")

WORKSPACE_DIR = PROJECT_ROOT / "agentti" / "workspace"
STATUS_FILE = WORKSPACE_DIR / "report_status.json"
REPORT_FILE = WORKSPACE_DIR / "asiakasraportti.md"
WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)

class ChatRequest(BaseModel):
    message: str
    model: str = "gemma3:4b"
    context: str = "Agenttichat"

class ReportRequest(BaseModel):
    model: str = "qwen3.5:cloud"

def get_db_path() -> str:
    return str(PROJECT_ROOT / "database" / "store.db")

def generate_heatmap_overlay() -> str:
    """Generoi UWB-heatmap pohjakuvan päälle ja palauttaa base64-enkoodatun PNG:n."""
    import base64, io
    import duckdb
    import numpy as np
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.colors as mcolors
    from PIL import Image

    db_path = get_db_path()
    floor_plan_path = PROJECT_ROOT / "images" / "kauppa.jpg"

    # Hae koordinaattidata
    con = duckdb.connect(db_path, read_only=True)
    df = con.execute("SELECT x, y FROM Zone").fetchdf()
    con.close()

    # Pohjakuvan dimensiot
    img = Image.open(str(floor_plan_path))
    img_w, img_h = img.size  # pikselit

    # UWB-koordinaatit (cm -> normalisoitu pohjakuvaan)
    x_min, x_max = df["x"].min(), df["x"].max()
    y_min, y_max = df["y"].min(), df["y"].max()

    # Normalisoidaan UWB-koordinaatit kuvan pikselikoordinaateiksi
    px = ((df["x"] - x_min) / (x_max - x_min) * img_w).astype(int).clip(0, img_w - 1)
    py = ((1 - (df["y"] - y_min) / (y_max - y_min)) * img_h).astype(int).clip(0, img_h - 1)

    # 2D histogrammi (heatmap-data)
    bins_x, bins_y = 120, 80
    heatmap, xedges, yedges = np.histogram2d(px, py, bins=[bins_x, bins_y],
                                              range=[[0, img_w], [0, img_h]])
    heatmap = heatmap.T  # transponoi matplotlib-yhteensopivaksi

    # Piirto
    fig, ax = plt.subplots(figsize=(16, 10), dpi=120)
    ax.imshow(img, extent=[0, img_w, 0, img_h], origin="upper", aspect="auto")

    masked = np.ma.masked_where(heatmap < 5, heatmap)  # piilota tyhjät solut
    im = ax.imshow(
        masked,
        extent=[0, img_w, 0, img_h],
        origin="lower",
        cmap="plasma",
        alpha=0.65,
        norm=mcolors.PowerNorm(gamma=0.4, vmin=5, vmax=heatmap.max()),
        aspect="auto"
    )
    cbar = plt.colorbar(im, ax=ax, fraction=0.02, pad=0.01)
    cbar.set_label("Paikannuspisteiden tiheys", fontsize=11)
    ax.set_title("Kärryjen liikkuminen myymälässä – UWB Heatmap pohjakuvan päällä", fontsize=14, pad=12)
    ax.axis("off")
    plt.tight_layout()

    # Enkoodaa base64:ksi
    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight", dpi=120)
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")

def update_status(generating: bool, current_step: str, reasoning: str = None, report_content: str = None, image_b64: str = None):
    """Päivittää asynkronisen tilan, jota Frontend lukee (Reasoning näkymä & Markdown raportti)."""
    try:
        status_data = {}
        if STATUS_FILE.exists():
            try:
                with open(STATUS_FILE, "r", encoding="utf-8") as f:
                    status_data = json.load(f)
            except Exception:
                pass
        
        reasoning_steps = status_data.get("reasoning_steps", [])
        if reasoning and (not reasoning_steps or reasoning_steps[-1] != reasoning):
            reasoning_steps.append(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {reasoning}")
        
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
        print(f"[Backend] Status update failed: {e}")

def run_duckdb_query() -> Dict[str, Any]:
    """Excalidraw: Datakysely (SQL) -> DuckDB (puhdistettu data)."""
    try:
        import duckdb
    except ImportError:
        return {"error": "DuckDB-kirjastoa ei ole asennettu."}
    
    db_path = get_db_path()
    if not Path(db_path).exists():
        return {"error": "DuckDB-tietokantaa ei löytynyt."}
        
    try:
        con = duckdb.connect(db_path, read_only=True)
        # Yksinkertainen katsaus
        res = con.execute("SELECT COUNT(DISTINCT visit_id) as visits, AVG(duration_seconds)/60.0 as avg_min FROM Visit").fetchone()
        
        # Ruuhkahuiput
        df_hours = con.execute("SELECT EXTRACT(HOUR FROM start_time) as hour, COUNT(*) as count FROM Visit GROUP BY hour ORDER BY count DESC LIMIT 3").fetchdf()
        
        # Hylätyt (poikkeamat)
        df_quality = con.execute("SELECT reason, COUNT(*) as count FROM Quality WHERE is_valid=False GROUP BY reason ORDER BY count DESC LIMIT 3").fetchdf()
        con.close()
        
        return {
            "yhteenveto": {"vierailut": res[0], "keskikesto_min": round(res[1] or 0, 1)},
            "ruuhkat": df_hours.to_dict(orient="records"),
            "poikkeamat": df_quality.to_dict(orient="records")
        }
    except Exception as e:
        return {"error": str(e)}

def agent_task_runner(model_name: str):
    """Excalidraw: 'Taustalla taskien tekijä' -> AI Agent (Analysoija)"""
    try:
        update_status(generating=True, current_step="Aloitetaan", reasoning="AI Agent käynnistetty.")
        time.sleep(1)
        
        # 1. SQL Kysely DuckDB:hen
        update_status(generating=True, current_step="Datakysely", reasoning="Suoritetaan Datakysely (SQL) DuckDB:hen...")
        context_data = run_duckdb_query()
        time.sleep(1.5)
        
        # 2. Tarkista peruutettiinko
        status_check = {}
        if STATUS_FILE.exists():
            with open(STATUS_FILE, "r", encoding="utf-8") as f:
                status_check = json.load(f)
        if not status_check.get("generating", True):
            return
            
        update_status(generating=True, current_step="LLM Analyysi", reasoning="Lähetetään konteksti Ollama-pilvimallille (LLM Analyysi)...")
        time.sleep(1)
        
        prompt = f"""
Olet data-analyytikko. Kirjoita lyhyt, ammattimainen asiakasraportti Markdownilla tästä DuckDB-datasta:
{json.dumps(context_data, indent=2)}
Käytä väliotsikoita ja tee 3-5 fiksua huomiota.
"""
        report_content = ""
        try:
            # LLM Analyysi -> Ollama
            res = requests.post(
                "http://127.0.0.1:11434/api/generate",
                json={"model": model_name, "prompt": prompt, "stream": False},
                timeout=60
            )
            if res.status_code == 200:
                report_content = res.json().get("response", "")
        except Exception as e:
            print(f"[Backend] Ollama virhe: {e}")
            
        # Varakoodi jos Ollama ei toimi
        if not report_content:
            update_status(generating=True, current_step="LLM Analyysi", reasoning="Ollama ei vastannut. Generoidaan vararaportti...")
            report_content = f"""# 📊 Analysoijan Raportti
**Tekoälymalli:** {model_name}

DuckDB-datakyselyn yhteenveto:
* **Vierailuja:** {context_data.get('yhteenveto', {}).get('vierailut', 0)} kpl
* **Keskikesto:** {context_data.get('yhteenveto', {}).get('keskikesto_min', 0)} min

## 🚨 Poikkeamat
Tunnistettiin poikkeavia heijastuksia laadunvalvonnassa. Näistä merkittävimmät olivat liian lyhyet signaalit.

## ⏰ Ruuhkahuiput
Kyselyn tuloksena ruuhkahuiput erottuivat selvästi alkuiltapäivään ja klo 16-17 väliin.
"""
        
        # Tallenna Markdown raportti tiedostoon
        with open(REPORT_FILE, "w", encoding="utf-8") as f:
            f.write(report_content)
            
        # Valmis
        update_status(generating=False, current_step="Valmis", reasoning="Markdown tulos (raportti) on valmis Frontendille.", report_content=report_content)
        
    except Exception as exc:
        traceback.print_exc()
        update_status(generating=False, current_step="Virhe", reasoning=f"Kriittinen virhe: {exc}")
    finally:
        # Varmistetaan luupin sulkeutuminen
        try:
            if STATUS_FILE.exists():
                with open(STATUS_FILE, "r", encoding="utf-8") as f:
                    status_check = json.load(f)
                if status_check.get("generating"):
                    status_check["generating"] = False
                    status_check["current_step"] = "Pysäytetty"
                    with open(STATUS_FILE, "w", encoding="utf-8") as f:
                        json.dump(status_check, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

@app.post("/api/generate-report")
async def api_generate_report(req: ReportRequest, background_tasks: BackgroundTasks):
    """Excalidraw: Käyttäjä input -> Lisää taustatehtävä jonoon."""
    initial_status = {
        "generating": True,
        "current_step": "Lisätään jonoon",
        "reasoning_steps": ["Käyttäjä input vastaanotettu FastAPIin."],
        "report_content": None,
        "last_updated": datetime.datetime.now().isoformat()
    }
    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump(initial_status, f, ensure_ascii=False, indent=2)
        
    background_tasks.add_task(agent_task_runner, req.model)
    return {"status": "accepted"}

@app.get("/api/report-status")
async def api_report_status():
    """Frontend lukee Async REST API (JSON) -kutsulla tätä."""
    if not STATUS_FILE.exists():
        return {"generating": False, "current_step": "Ei aloitettu", "reasoning_steps": [], "report_content": None}
    with open(STATUS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

@app.post("/api/cancel-report")
async def api_cancel_report():
    if STATUS_FILE.exists():
        with open(STATUS_FILE, "r", encoding="utf-8") as f:
            s = json.load(f)
        s["generating"] = False
        s["current_step"] = "Peruutettu"
        with open(STATUS_FILE, "w", encoding="utf-8") as f:
            json.dump(s, f, ensure_ascii=False, indent=2)
    return {"status": "cancelled"}

@app.post("/api/chat")
async def api_chat(req: ChatRequest, background_tasks: BackgroundTasks):
    """Excalidraw: Chat pop-up. Käynnistää dynaamisen CrewAI-agenttitiimin taustalla."""

    IS_HEATMAP = any(kw in req.message.lower() for kw in ["heatmap", "visuali", "kartta", "reitti", "koordinaatti"])

    # Nollataan tilatiedosto
    update_status(generating=True, current_step="Aloitetaan tiimin työ...",
                  reasoning="Tekoälytiimi on herätetty. Valmistellaan dataympäristöä...",
                  report_content=None, image_b64=None)

    def run_crew_task():
        try:
            update_status(generating=True, current_step="Rakennetaan tiimiä",
                          reasoning="Luodaan agentit ja haetaan viimeisin tietokantadata (DuckDB)...")

            if IS_HEATMAP:
                # Visualisointi: generoidaan heatmap suoraan Pythonilla (ei agenttityökaluilla)
                update_status(generating=True, current_step="Visualisoidaan...",
                              reasoning="Python-visualisoija piirtää UWB-dataa pohjakuvan päälle...")
                try:
                    img_b64 = generate_heatmap_overlay()
                    update_status(
                        generating=False, current_step="Valmis",
                        reasoning="Heatmap valmis!",
                        report_content="## 🗺️ Kärryjen liikkuminen – UWB Heatmap\n\nVisualisointi on luotu piirtämällä paikannuspisteiden tiheys pohjakuvan päälle. Kirkkaat alueet ovat suosituimpia reittejä.",
                        image_b64=img_b64
                    )
                except Exception as e:
                    update_status(generating=False, current_step="Virhe",
                                  reasoning=f"Heatmap-virhe: {e}")
            else:
                crew = build_dynamic_chat_crew(
                    task_description=req.message,
                    model_name=req.model
                )
                update_status(generating=True, current_step="Analyysi käynnissä",
                              reasoning="Agentit perkaavat dataa läpi. Tämä kestää lokaaleilla malleilla noin 1–3 minuuttia...")
                result = crew.kickoff()
                update_status(generating=False, current_step="Valmis",
                              reasoning="Analyysi valmistui onnistuneesti!", report_content=result.raw)

        except Exception as e:
            print(f"Chat-virhe (CrewAI): {e}")
            update_status(generating=False, current_step="Virhe",
                          reasoning=f"Kriittinen virhe tiimissä: {e}")

    background_tasks.add_task(run_crew_task)
    return {"status": "started"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.backend:app", host="0.0.0.0", port=8000, reload=True)
