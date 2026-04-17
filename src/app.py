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

# Repo-moduulit
from config.store_config import store_config
from main import run_etl
from scripts.reset_env import reset_env

# 3. KONFIGURAATIO
DB_PATH = PROJECT_ROOT / "database" / "store.db"
IMAGE_FILENAME = "kauppa.jpg"
IMAGE_PATH = PROJECT_ROOT / IMAGE_FILENAME

# 4. KÄYTTÖLIITTYMÄ
st.set_page_config(page_title="UWB Platform v1", layout="wide")
st.title("🛒 Tokmannin UWB-paikannusdata")

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
    st.text(f"Kuva: {IMAGE_FILENAME}")
    st.text(f"Koko: {img.shape[1]} x {img.shape[0]} px")

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