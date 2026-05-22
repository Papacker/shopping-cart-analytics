import streamlit as st
import pandas as pd
from config.store_config import store_config
from src.queries import get_department_flow, get_daily_visits, get_table_counts
from src.charts import create_horizontal_bar_chart, create_weather_correlation_chart

def render_tab_advanced():
    st.subheader("🧠 6. Syvälliset havainnot")
    st.markdown("Syvällisempiä liiketoimintahavaintoja: Osastojen vetovoima, viipymäanalyysi ja ulkoisen säädatan vaikutus.")
    
    # 1. KPI-rivi: Konversio ja yleiskuva
    counts = get_table_counts()
    total_visits = counts.get('Visit', 0)
    
    col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
    col_kpi1.metric("Kokonaiskäynnit", f"{total_visits:,}")
    
    departments = store_config['spatial_zones']['departments']
    
    with st.spinner("Lasketaan osastojen vetovoimaa..."):
        df_flow = get_department_flow(departments)
        
    if not df_flow.empty:
        avg_dwell = df_flow['avg_dwell_min'].mean()
        col_kpi2.metric("Keskimääräinen viipymä / osasto", f"{avg_dwell:.1f} min")
        
        total_dept_hits = df_flow['unique_visits'].sum()
        avg_depts_per_visit = total_dept_hits / total_visits if total_visits > 0 else 0
        col_kpi3.metric("Osastoläpäisy (kpl / käynti)", f"{avg_depts_per_visit:.1f}")
    
    st.divider()
    
    # 2. Viipymät - vain yksi sarake (osastotiedot jo tab3_checkout.py:ssä)
    col_dwell = st.columns(1)
    
    if not df_flow.empty:
        with col_dwell[0]:
            st.markdown("### ⏳ Pisimmät viipymät osastoittain")
            st.caption("Keskimääräinen aika osastolla (min) - Top 8 pisintä")
            viipyma = df_flow.sort_values('avg_dwell_min').tail(8)
            df_plot_dwell = viipyma.rename(columns={'zone': 'Osasto', 'avg_dwell_min': 'Osumat'})
            fig_dwell = create_horizontal_bar_chart(df_plot_dwell, '#4cc9f0', x_label='Aika (min)')
            st.pyplot(fig_dwell, width='stretch')

    st.divider()

    # 3. Alarivi: Sääkorrelaatio (Koko leveys)
    st.markdown("### 🌧️ Sääkorrelaatio ja kävijämäärät")
    st.info("Miten ulkoiset olosuhteet vaikuttavat myymälän kokonaisliikenteeseen?")
    
    with st.spinner("Haetaan säätietoja..."):
        df_daily_visits = get_daily_visits()
        
        if df_daily_visits.empty:
            st.warning("Ei dataa sääkorrelaation laskentaan.")
        else:
            try:
                import requests
                min_date = df_daily_visits['date'].min()
                max_date = df_daily_visits['date'].max()
                
                min_str = min_date.strftime('%Y-%m-%d') if hasattr(min_date, 'strftime') else str(min_date)
                max_str = max_date.strftime('%Y-%m-%d') if hasattr(max_date, 'strftime') else str(max_date)
                
                # Järvenpää koordinaatit: latitude=60.4731, longitude=25.0863
                url = f"https://archive-api.open-meteo.com/v1/archive?latitude=60.4731&longitude=25.0863&start_date={min_str}&end_date={max_str}&daily=precipitation_sum,temperature_2m_max&timezone=Europe/Helsinki"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    weather_data = response.json()
                    daily = weather_data['daily']
                    
                    # Korjattu DatetimeIndex käsittely
                    df_weather = pd.DataFrame({
                        'date': pd.to_datetime(daily['time']).date,
                        'temperature': daily['temperature_2m_max'],
                        'precipitation': daily['precipitation_sum']
                    })
                    
                    # Varmistetaan että molemmat ovat date-muodossa
                    df_daily_visits['date'] = pd.to_datetime(df_daily_visits['date']).dt.date
                    
                    df_merged = pd.merge(df_daily_visits, df_weather, on='date', how='inner')
                    
                    if not df_merged.empty:
                        fig_w = create_weather_correlation_chart(df_merged)
                        st.pyplot(fig_w, width='stretch')
                        st.caption("Lähde: Open-Meteo Historical Weather API (Järvenpää)")
                    else:
                        st.warning("⚠️ Säädataa ei löytynyt vastaaville päiville (Merge tyhjä).")
                else:
                    st.error(f"Säärajapinta ei vastaa: {response.status_code}")
            except Exception as e:
                st.error(f"Virhe säädatan haussa: {e}")

    # 4. Alin osa: Viipymätaulukko (ei osastosuorituskykyä - katso tab3)
    with st.expander("📊 Näytä tarkat viipymätiedot osastoittain"):
        if not df_flow.empty:
            df_all = df_flow.copy()
            df_all = df_all.sort_values('avg_dwell_min', ascending=False)
            st.dataframe(
                df_all.rename(columns={
                    'zone': 'Osasto', 
                    'unique_visits': 'Kävijät', 
                    'avg_dwell_min': 'Viipymä (min)'
                }),
                width='stretch'
            )
