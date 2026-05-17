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
# pylint: disable=wrong-import-position, import-outside-toplevel, invalid-name, redefined-outer-name, too-many-locals, too-many-branches, too-many-statements, broad-exception-caught

# 1. PROJEKTIN JUURI + MODUULIEN LUOTTAMUS
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Repo-moduulit
from config.store_config import store_config
from scripts.reset_env import reset_env
from src.queries import get_table_counts

# Välilehdet
from src.tabs.tab1_health import render_tab_health
from src.tabs.tab2_traffic import render_tab_traffic
from src.tabs.tab3_checkout import render_tab_checkout
from src.tabs.tab4_dynamics import render_tab_dynamics
from src.tabs.tab5_heatmap import render_tab_heatmap
from src.tabs.tab6_advanced import render_tab_advanced
from src.tabs.tab7_insights import render_tab_insights


# 3. KONFIGURAATIO & PROFIILIT

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
    st.sidebar.divider()
    
    # === KIELIMALLIN VALINTA ===
    st.sidebar.markdown("### 🧠 Agentin Kielimalli")
    st.sidebar.caption("Valitse Ollama-kielimalli, jota Agenttiarkkitehtuuri käyttää analysointiin ja keskusteluun.")
    
    import requests
    # Käytä ympäristömuuttujaa tai oletuksena paikallista
    ollama_host = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
    
    # Haetaan kaikki mallit Ollama-palvelimelta
    available_models = ["qwen3.6:35b-a3b", "llama3.1:8b", "qwen2.5-coder:7b"]
    try:
        res = requests.get(f"{ollama_host}/api/tags", timeout=5)
        if res.status_code == 200:
            models_data = res.json().get("models", [])
            if models_data:
                available_models = [m["name"] for m in models_data]
    except Exception as e:
        st.sidebar.warning(f"Ei saada yhteyttä Ollamaan: {e}")

    # Suositukset eri käyttötarkoituksiin
    recommendations = {
        "qwen3.6": "💡 **qwen3.6:35b-a3b** = Paras yleisanalyysiin (suuri, pätevä)",
        "llama3.1": "💡 **llama3.1:8b** = Tasapainoinen vaihtoehto",
        "qwen2.5": "💡 **qwen2.5-coder:7b** = Koodianalyysiin"
    }
    
    # Näytä suositukset ENNEN valintaa
    st.sidebar.markdown("""
    **Suositukset:**
    - qwen3.6 = Yleisanalyysiin
    - llama3.1 = Tasapainoinen  
    - qwen2.5-coder = Koodiin
    """)
    
    # Oletusvalinta - valitse qwen3.6 jos löytyy, muuten ensimmäinen
    default_index = 0
    for i, m in enumerate(available_models):
        if "qwen3.6" in m:
            default_index = i
            break
    
    # Valinta
    st.session_state.selected_model = st.sidebar.selectbox(
        "Valitse kielimalli", 
        available_models, 
        index=default_index,
        label_visibility="collapsed"
    )
    
    # Näytä käytössä oleva malli
    current = st.session_state.selected_model
    st.sidebar.success(f"✅ **Käytössä:** `{current}`")
    
    st.sidebar.divider()
    st.sidebar.subheader("Järjestelmänhallinta")
    st.sidebar.caption("Täällä voit tyhjentää paikallisen tietokannan ja aloittaa datan käsittelyn puhtaalta pöydältä.")
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

    tab_health, tab_traffic, tab_checkout, tab_dynamics, tab_heatmap, tab_advanced, tab_insights = st.tabs([
        "🏥 Datan laatu",
        "🚶 Liikennevirrat",
        "🏪 Osastoanalyysi",
        "🛒 Kärrydynamiikka",
        "🔥 Heatmap",
        "🧠 Advanced insights",
        "✨ Asiakkaalle"
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
        render_tab_heatmap()

    with tab_advanced:
        render_tab_advanced()
        
    with tab_insights:
        render_tab_insights()



# --- ENTRY POINT ---
if st is not None:
    # --- Custom Premium CSS ---
    try:
        with open(PROJECT_ROOT / "src" / "style.css") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except Exception:
        pass

    main()
