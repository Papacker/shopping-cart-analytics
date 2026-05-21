import streamlit as st
import pandas as pd
from src.queries import get_traffic_visits
from src.charts import create_duration_histogram, create_hourly_bar_chart, create_weekday_bar_chart

def render_tab_traffic():
    st.subheader("🌊 2. Liikennevirrat yleiskuva")

    df_visit = get_traffic_visits()

    if df_visit.empty:
        st.warning("Visit-taulussa ei ole dataa.")
    else:
        # Varmistetaan vaaditut sarakkeet
        required_cols = ['duration_seconds', 'tunti', 'viikonpaiva', 'node_id']
        missing = [c for c in required_cols if c not in df_visit.columns]
        if missing:
            st.error(f"⚠️ Puuttuvia sarakkeita datassa: {', '.join(missing)}")
            st.stop()

        df_visit['kesto_min'] = df_visit['duration_seconds'] / 60

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Vierailuja yhteensä", f"{len(df_visit):,}")
        m2.metric("Keskiarvo-asiointi", f"{df_visit['kesto_min'].mean():.1f} min")
        m3.metric("Pisin asiointiaika",   f"{df_visit['kesto_min'].max():.1f} min")
        m4.metric("Kärryjä yhteensä", f"{df_visit['node_id'].nunique():,}")

        st.divider()
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Asiointiajan jakauma**")
            fig1 = create_duration_histogram(df_visit, df_visit['kesto_min'].mean(), df_visit['kesto_min'].median())
            st.pyplot(fig1, width='stretch')

        with col2:
            st.markdown("**Ruuhkahuiput tunneittain**")
            tunnit = df_visit.groupby('tunti').size().reset_index(name='count')
            peak = tunnit['count'].max()
            fig2 = create_hourly_bar_chart(tunnit, peak)
            st.pyplot(fig2, width='stretch')

        st.markdown("**Vierailut viikonpäivittäin**")
        # DuckDB dow: 0=Sun, 1=Mon, ..., 6=Sat. Haluamme Ma->Su järjestyksen (1,2,3,4,5,6,0)
        paiva_nimet = {1: 'Maanantai', 2: 'Tiistai', 3: 'Keskiviikko', 4: 'Torstai', 5: 'Perjantai', 6: 'Lauantai', 0: 'Sunnuntai'}
        vp = df_visit.groupby('viikonpaiva').size().reset_index(name='count')
        
        # Luodaan järjestyssarake (Ma=0, ..., Su=6)
        vp['sort_order'] = vp['viikonpaiva'].map({1: 0, 2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 0: 6})
        vp = vp.sort_values('sort_order')
        vp['nimi'] = vp['viikonpaiva'].map(paiva_nimet)

        fig3 = create_weekday_bar_chart(vp)
        st.pyplot(fig3, width='stretch')
