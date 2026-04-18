"""
Streamlit App: Kaupan UWB-paikannusdata 
"""

import sys
from pathlib import Path

# 1. PROJEKTIN JUURI + MODUULIEN LUOTTAMUS
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# 2. MODUULIEN IMPORTIT 
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import duckdb
import pandas as pd

# Repo-moduulit
from config.store_config import store_config
from main import run_etl
from scripts.reset_env import reset_env

# 3. KONFIGURAATIO & PROFIILIT
DB_PATH = PROJECT_ROOT / "database" / "store.db"

# Sallitaan profiilin vaihto lennosta
PROFIILIT = store_config['geometry']['map_profiles']
oletus_profiili = store_config['geometry']['active_profile']

st.sidebar.subheader("🗺️ Kartan asetukset")
valittu_avain = st.sidebar.selectbox(
    "Valitse karttapohja", 
    options=list(PROFIILIT.keys()),
    index=list(PROFIILIT.keys()).index(oletus_profiili)
)

profiili = PROFIILIT[valittu_avain]
IMAGE_FILENAME = profiili['filename']
IMAGE_PATH = PROJECT_ROOT / IMAGE_FILENAME

CLEAN_TABLE = "Zone"

def fetch_data(query):
    """Suorittaa SQL-kyselyn turvallisesti ilman tiedostolukkoja."""
    if not DB_PATH.exists():
        return pd.DataFrame()
    try:
        with duckdb.connect(str(DB_PATH), read_only=True) as con:
            return con.execute(query).df()
    except Exception as e:
        st.error(f"Tietokantavirhe: {e}")
        return pd.DataFrame()

# 4. KÄYTTÖLIITTYMÄ
st.set_page_config(page_title="UWB laitetaan parastamme", layout="wide")
st.title("🛒 Laitetaan parastamme - UWB-paikannnusdata")

# SIDEBAR
st.sidebar.header("⚙️ Hallinta")

# 1. AJA ETL
if st.sidebar.button("🚀 Aja ETL-putki"):
    with st.spinner("ETL-putki ajetaan..."):
        try:
            run_etl()
            st.sidebar.success("✅ ETL valmis!")
            st.rerun()
        except Exception as e:
            st.sidebar.error(f"❌ Virhe: {e}")
st.sidebar.divider() # Selkeyden vuoksi

# 2. TYHJENNYS 
st.sidebar.subheader("Vaaralliset toiminnot")
varmistus = st.sidebar.checkbox("Salli tietokannan poisto")
if st.sidebar.button("🗑️ Tyhjennä tietokanta", disabled=not varmistus):
    try:
        # Pakotetaan DuckDB sulkemaan kaikki yhteydet ennen poistoa
        duckdb.connect().close() 
        
        reset_env()
        st.sidebar.success("✅ Ympäristö tyhjennetty!")
        st.rerun()
    except Exception as e:
        st.sidebar.error(f"Poisto epäonnistui: {e}")

# KUVAN NÄYTTÖ 
st.header("🗺️ Kaupan pohjakuva")

if not IMAGE_PATH.exists():
    st.error(f"⚠️ Kuvaa ei löydy: {IMAGE_PATH}")
else:
    img = mpimg.imread(str(IMAGE_PATH))
    fig, ax = plt.subplots(figsize=(15, 8))
    ax.imshow(img)
    ax.set_title("Kaupan pohjakuva", fontsize=14)
    ax.axis("off")
    st.pyplot(fig)
    
    # Lisätietoa
    c1, c2, c3 = st.columns(3)
    c1.text(f"Tiedosto: {IMAGE_FILENAME}")
    c2.text(f"Koko: {img.shape[1]} x {img.shape[0]} px")
    c3.text(f"Skaala: {profiili['scale_cm_per_px']} cm/px")

    

#  TIETOKANNAN TILA
st.header("📊 Tietokannan tila")

if DB_PATH.exists():
    con = duckdb.connect(str(DB_PATH), read_only=True)
    tables = con.execute("SHOW TABLES").fetchall()
    st.success(f"✅ Tietokanta olemassa ({len(tables)} taulua)")
    
    for t in tables:
        table_name = t[0]
        count = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        st.text(f"  • {table_name}: {count:,} riviä")
    con.close()
else:
    st.warning("⚠️ Tietokantaa ei ole (ajaa ETL ensin)")

# =============================================================================
# 5. LIIKETOIMINTA-ANALYTIIKKA
# =============================================================================
st.divider()
st.header("📈 Liiketoiminta-analytiikka")

if DB_PATH.exists():
    # Luodaan välilehdet valmiiksi, mutta täytetään nyt vain ensimmäinen
    tab_heatmap, tab_time, tab_queue = st.tabs([
        "🔥 Ruuhkat heatmap",
        "⏰ Aika-analyysi", 
        "💸 Kassa ja Jonot"
    ])
