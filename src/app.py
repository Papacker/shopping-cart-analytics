"""
Streamlit App: Kaupan UWB-paikannusdata 
"""

import os
import sys
import logging
import warnings
import multiprocessing

# Vain pääprosessi lataa Streamlitin ja tekee UI-konfiguroinnit
# Tämä estää lapsiprosesseja (ETL) lataamasta Streamlitiä ja antamasta varoituksia
if multiprocessing.current_process().name == 'MainProcess':
    import streamlit as st
    st.set_page_config(
        page_title="Tokmanni Järvenpää - Fleet Analytics",
        page_icon="🛒",
        layout="wide"
    )
    # Terminaalihygienia: Hiljennetään Streamlit täysin
    os.environ["STREAMLIT_GLOBAL_LOG_LEVEL"] = "error"
    logging.getLogger("streamlit.runtime.scriptrunner_utils").setLevel(logging.ERROR)
    warnings.filterwarnings("ignore", message=".*missing ScriptRunContext.*")
else:
    # Lapsiprosesseissa (workerit) emme halua Streamlitiä lainkaan
    st = None

from pathlib import Path
import duckdb

# 1. PROJEKTIN JUURI + MODUULIEN LUOTTAMUS
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Repo-moduulit
from config.store_config import store_config
from main import run_etl
from scripts.reset_env import reset_env
from src.queries import get_table_counts, DB_PATH

# Välilehdet
from src.tabs.tab1_health import render_tab_health
from src.tabs.tab2_traffic import render_tab_traffic
from src.tabs.tab3_checkout import render_tab_checkout
from src.tabs.tab4_dynamics import render_tab_dynamics
from src.tabs.tab5_heatmap import render_tab_heatmap
from src.tabs.tab6_advanced import render_tab_advanced

# 3. KONFIGURAATIO & PROFIILIT
PROFIILIT = store_config['geometry']['map_profiles']
oletus_profiili = store_config['geometry']['active_profile']

def main():
    # 3. UI:N RAKENTAMINEN
    st.title("🛒 Laitetaan parastamme — UWB-paikannusdata")

    # Sidebar: Hallinta
    st.sidebar.header("⚙️ Hallinta")

    # ETL-nappi
    if st.sidebar.button("🚀 Aja ETL-putki"):
        with st.spinner("ETL-putki ajetaan..."):
            try:
                import importlib
                import main
                importlib.reload(main)
                summary = main.run_etl()
                if summary:
                    if summary.get("status") == "already_processed":
                        st.sidebar.info("ℹ️ Kaikki tiedostot on jo prosessoitu.")
                    else:
                        st.sidebar.success(f"✅ ETL valmis! ({summary['duration']:.1f}s)")
                        with st.sidebar.expander("📊 Ajon yhteenveto", expanded=True):
                            st.write(f"📁 Tiedostoja: {summary['new_files_processed']}")
                            st.write(f"📝 Rivejä: {summary['total_raw_rows']:,}")
                            st.write(f"✅ Hyväksytty: {summary['total_cleaned_rows']:,}")
                            if summary["rejections"]:
                                st.write("---")
                                st.write("Hylkäykset:")
                                for reason, count in summary["rejections"].items():
                                    st.write(f"- {reason}: {count}")
                    st.rerun()
                else:
                    st.sidebar.error("❌ ETL epäonnistui. Katso terminaali.")
            except Exception as e:
                st.sidebar.error(f"❌ Kriittinen virhe: {e}")

    st.sidebar.divider()

    st.sidebar.subheader("🗺️ Kartan asetukset")
    valittu_avain = st.sidebar.selectbox(
        "Valitse karttapohja",
        options=list(PROFIILIT.keys()),
        index=list(PROFIILIT.keys()).index(oletus_profiili)
    )
    profiili = PROFIILIT[valittu_avain]
    IMAGE_PATH = PROJECT_ROOT / profiili['filename']

    st.sidebar.divider()
    st.sidebar.subheader("Vaaralliset toiminnot")
    varmistus = st.sidebar.checkbox("Salli tietokannan poisto")
    if st.sidebar.button("🗑️ Tyhjennä tietokanta", disabled=not varmistus):
        with st.spinner("Nollataan ympäristö..."):
            try:
                reset_env()
                st.sidebar.success("✅ Ympäristö tyhjennetty!")
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.sidebar.error(f"Poisto epäonnistui: {e}")

    # --- DATAN LATAUS ---
    st.header("Tietokannan tila")

    counts = get_table_counts()
    if counts:
        if 'Visit' in counts:
            st.success(f"✅ Tietokanta olemassa ({len(counts)} taulua)")
            cols = st.columns(len(counts))
            for i, (table, count) in enumerate(counts.items()):
                cols[i].metric(table, f"{count:,}")
        else:
            st.warning("⚠️ Tietokanta on olemassa, mutta tauluja ei löytynyt. Aja ETL.")
    else:
        st.warning("⚠️ Tietokantaa ei ole — aja ETL ensin")
        st.stop()

    st.divider()

    # --- ANALYTIIKKA-OSIO ---
    st.header("Liiketoiminta-analytiikka")

    tab_health, tab_traffic, tab_checkout, tab_dynamics, tab_heatmap, tab_advanced = st.tabs([
        "🏥 Datan laatu", 
        "🚶 Liikennevirrat", 
        "🏪 Osastoanalyysi", 
        "🛒 Kärrydynamiikka", 
        "🔥 Heatmap",
        "🧠 Advanced insights"
    ])

    with tab_health:
        render_tab_health()

    with tab_traffic:
        render_tab_traffic()

    with tab_checkout:
        render_tab_checkout()

    with tab_dynamics:
        render_tab_dynamics()

    with tab_heatmap:
        render_tab_heatmap(IMAGE_PATH, profiili, valittu_avain)

    with tab_advanced:
        render_tab_advanced()

# --- ENTRY POINT ---
if st is not None:
    # --- Custom Premium CSS ---
    try:
        with open(PROJECT_ROOT / "src" / "style.css") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except Exception:
        pass
    
    main()
