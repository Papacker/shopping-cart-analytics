import streamlit as st
import pandas as pd
from config.store_config import store_config
from src.queries import get_all_zone_stats
from src.charts import create_departments_bar_chart, create_checkout_bar_chart


def render_tab_checkout():
    """Renderöi kassa- ja osastoanalytiikan välilehden."""
    st.subheader("🏪 3. Kassa- ja osastoanalytiikka")
    st.info(
        "Analyysi perustuu ETL-putkessa valmiiksi laskettuun ZoneVisit-tauluun, "
        "joka tiivistää miljoonat sijaintipisteet aidoiksi osastokäynneiksi.",
        icon="ℹ️"
    )

    with st.spinner("Haetaan osastotilastoja..."):
        df_all = get_all_zone_stats()

    if df_all.empty:
        st.warning("ZoneVisit-taulussa ei ole vielä dataa. Aja ETL-putki ensin.")
        return

    # Erotellaan osastot ja kassat configin perusteella
    dep_names = list(store_config['spatial_zones']['departments'].keys())
    checkout_names = list(store_config['spatial_zones']['checkouts'].keys())

    df_dep_all = df_all[df_all['zone'].isin(dep_names)].copy()
    df_kassa_all = df_all[df_all['zone'].isin(checkout_names)].copy()

    # Korvataan sarakkeiden nimet visualisointiin
    df_dep_all = df_dep_all.rename(columns={'uniikit_asiakkaat': 'käynnit'})
    df_kassa_all = df_kassa_all.rename(columns={'uniikit_asiakkaat': 'käynnit'})

    # Näytetään myymälän pohjakartta expanderissa (kuin popup)
    with st.expander("🗺️ Näytä myymälän osastokartta"):
        col_map_img, col_map_text = st.columns([2, 1])
        with col_map_img:
            st.image("kauppa_osasto.jpg", width='stretch')
        with col_map_text:
            st.markdown("**Osastojen sijainti**")
            st.info("Voit käyttää tätä karttaa viitekehyksenä alla oleville tilastoille.")
            if not df_dep_all.empty:
                st.write(f"Suosituin osasto: **{df_dep_all.iloc[0]['zone']}**")

    st.divider()

    col_dep, col_kassa = st.columns(2)

    with col_dep:
        st.markdown("### 🏬 Suosituimmat osastot")
        st.caption("Uniikit asiakkaat osastoittain.")
        df_dep_top = df_dep_all.head(15)
        
        if not df_dep_top.empty:
            fig_dep = create_departments_bar_chart(df_dep_top)
            st.pyplot(fig_dep, width='stretch')
        else:
            st.write("Ei osastovierailuja.")

    with col_kassa:
        st.markdown("### 💳 Kassapisteiden kuormitus")
        st.caption("Uniikit asiakkaat kassapisteittäin.")
        
        if not df_kassa_all.empty:
            # Lajitellaan kassat nimen mukaan (Kassa 1, 2, jne.)
            df_kassa_all = df_kassa_all.sort_values('zone')
            fig_kassa = create_checkout_bar_chart(df_kassa_all)
            st.pyplot(fig_kassa, width='stretch')
        else:
            st.write("Ei kassadataa.")

    st.divider()
    st.info(
        "💡 **Mitä luvut tarkoittavat?** 'Uniikit asiakkaat' laskee kunkin asiakassession vain kerran per osasto. "
        "Aiemmat suuret luvut olivat teknisiä 'osumia', jotka kertyivät koko asioinnin ajan.",
        icon="📊"
    )

    st.divider()
    st.markdown("**Osastovierailujen tarkat tiedot**")
    
    # Muotoillaan taulukko luettavammaksi
    if not df_dep_all.empty:
        df_display = df_dep_all.copy()
        df_display['avg_time'] = (df_display['avg_seconds'] / 60).round(1).astype(str) + " min"
        df_display = df_display.rename(columns={
            'zone': 'Osasto',
            'käynnit': 'Vierailut (kpl)',
            'avg_time': 'Keskimääräinen viipymä'
        })
        
        st.dataframe(
            df_display[['Osasto', 'Vierailut (kpl)', 'Keskimääräinen viipymä']],
            width='stretch',
            height=400
        )
