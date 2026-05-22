import streamlit as st
import pandas as pd
from src.queries import (
    get_cart_utilization_stats, get_cart_rotation_index, 
    get_cart_idle_stats, get_hourly_cart_utilization, 
    get_cart_distances, get_cart_popularity_history
)
from src.charts import (
    create_usage_heatmap
)


def render_tab_dynamics():
    """Renderöi kärrydynamiikan ja kalustonhallinnan välilehden."""
    st.subheader("🛒 4. Kärrydynamiikka ja kalustonhallinta")
    st.markdown(
        "Tämä välilehti analysoi 21 ostoskärryn käyttöastetta, kulumista ja rotaatiota. "
        "Tavoitteena on varmistaa tasainen käyttö ja ennakoida huoltotarpeet."
    )

    # 1. HAETAAN DATA
    with st.spinner("Analysoidaan kaluston tilaa..."):
        df_util = get_cart_utilization_stats()
        df_rotation = get_cart_rotation_index()
        df_idle = get_cart_idle_stats()
        df_hourly = get_hourly_cart_utilization()
        df_dist = get_cart_distances()
        df_pop_hist = get_cart_popularity_history()

    # 2. KPI-KORTIT
    col1, col2, col3 = st.columns(3)
    
    balance_pct = 100
    if not df_rotation.empty:
        top_20_share = df_rotation['top_20_pct_share'].iloc[0]
        balance_pct = max(0, 100 - (top_20_share - 20) * 1.66)

    with col1:
        st.metric("Aktiiviset kärryt", f"{len(df_util)} / 21")
        st.caption("Kaluston aktiiviset laitteet.")
    
    with col2:
        st.metric("Kaluston tasapaino", f"{balance_pct:.1f} %")
        st.caption("Kuinka tasaisesti käyttö jakautuu.")

    with col3:
        avg_km = df_dist['total_distance_km'].mean() if not df_dist.empty else 0
        st.metric("Keskimääräinen kuluma", f"{avg_km:.2f} km")
        st.caption("Keskimääräinen ajettu matka per kärry.")

    st.info(
        "💡 **Mitä 'Kaluston tasapaino' tarkoittaa?** Jos luku on korkea, kaikkia kärryjä käytetään tasaisesti. "
        "Jos luku laskee, asiakkaat poimivat vain tiettyjä kärryjä, mikä johtaa niiden ennenaikaiseen kulumiseen.",
        icon="⚖️"
    )

    if df_util.empty:
        st.warning("Dataa ei ole vielä kertynyt analyysia varten.")
        return

    st.divider()

    # 3. KÄYTTÖASTE JA ROTAATIO
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("### 🗓️ Käyttöasteen aikajakauma")
        st.caption("Milloin kärryjä käytetään eniten? (Puhdistettu aukioloajat 8-21)")
        fig_heat = create_usage_heatmap(df_hourly)
        st.pyplot(fig_heat, width='stretch')

    with col_right:
        st.markdown("### 📊 Kärryjen suosio")
        st.caption("Kunkin ostoskärryn (Node ID) tekemien asiakasmatkojen kokonaismäärä koko historian ajalta.")
        
        # Varmistetaan että ID esitetään tekstinä, jotta pylväät ovat siistejä
        df_pop_chart = df_pop_hist.copy()
        df_pop_chart['node_id'] = df_pop_chart['node_id'].astype(str)
        st.bar_chart(df_pop_chart.set_index('node_id')['total_trips'], color="#4cc9f0", width='stretch')

    st.divider()

    # 4. MATKAMITTARI
    st.markdown("### 🛣️ Kärryjen matkamittari")
    st.caption("Tämä mittari kertoo, kuinka monta kilometriä kukin kärry on todellisuudessa rullannut asiakkaiden mukana.")
    
    # Lajitellaan kärryt matkan mukaan ja siistitään ID:t tekstiksi
    df_sorted = df_dist.sort_values('total_distance_km', ascending=False).copy()
    df_sorted['node_id'] = df_sorted['node_id'].astype(str)
    
    st.bar_chart(df_sorted.set_index('node_id')['total_distance_km'], color="#f72585", horizontal=True, width='stretch')

    st.divider()

    # 5. TOIMINTALISTA (Action List)
    st.markdown("### 🔍 Kaluston toimivuus ja tila")
    
    col_a1, col_a2 = st.columns(2)

    with col_a1:
        st.markdown("**🛑 Pitkät lepoajat**")
        st.caption("Kärryt, joiden lepoaika sessioiden välillä on poikkeuksellisen pitkä (yli 6h).")
        df_stuck = df_idle[df_idle['median_idle_min'] > 360].copy()
        if not df_stuck.empty:
            df_stuck['Tunnit'] = (df_stuck['median_idle_min'] / 60).round(1)
            st.table(df_stuck[['node_id', 'Tunnit']].rename(columns={'node_id': 'Kärry ID', 'Tunnit': 'Lepo (h)'}))
        else:
            st.success("Kaikki kärryt ovat olleet aktiivisessa kierrossa! ✅")
        
    with col_a2:
        st.markdown("**⭐ Suosituimmat työjuhdat**")
        st.caption("Kärryt, joilla on ajettu eniten sessioita historian aikana.")
        df_top = df_pop_hist.head(5).copy()
        st.table(df_top.rename(columns={'node_id': 'Kärry ID', 'total_trips': 'Matkat yhteensä'}))

    with st.expander("Näytä koko kaluston tarkat tiedot (Node ID -kohtaisesti)"):
        st.dataframe(df_sorted.rename(columns={
            'node_id': 'Kärry ID', 'total_distance_km': 'Matka (km)', 'total_trips': 'Sessioita'
        }), width='stretch')