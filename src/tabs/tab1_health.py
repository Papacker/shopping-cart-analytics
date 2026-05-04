import streamlit as st
import pandas as pd
from src.queries import get_health_metrics, get_dt_metrics, get_quality_reasons
from src.charts import create_pie_chart

def render_tab_health():
    st.subheader("🛠️ 1. ETL Audit & Data Quality")
    st.info("💡 **Miksi näytämme tämän?** Tämä välilehti tekee läpinäkyväksi ETL-putkemme toiminnan. UWB-raakadata sisältää valtavasti laitekohinaa ja paikallaan olevia kärryjä. Oheinen korkea hylkäysprosentti todistaa, että laitekohina on onnistuneesti eristetty puhtaasta datasta. Muut välilehdet käyttävät vain 100% puhtaita, validoituja asiakaskierroksia.")
    
    col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
    
    df_q_count, df_v_count = get_health_metrics()
    
    # Haetaan rivitiedot (pisteet) yleiskuvaa varten
    total_points_cleaned = int(df_v_count['points_sum'].iloc[0]) if not df_v_count.empty else 0
    
    if not df_q_count.empty and not df_v_count.empty:
        q_cnt = int(df_q_count['cnt'].iloc[0])
        v_cnt = int(df_v_count['cnt'].iloc[0])
        total_sessions = q_cnt + v_cnt
        outlier_freq = (q_cnt / total_sessions * 100) if total_sessions > 0 else 0
        
        col_kpi1.metric("Hylätyt sessiot (Outliers)", f"{q_cnt:,}")
        col_kpi2.metric("Hyväksytyt sessiot", f"{v_cnt:,}")
        col_kpi3.metric("Hyväksytyt pisteet (Rivit)", f"{total_points_cleaned/1e6:.1f} M")
    
    with st.spinner("Lasketaan näytevälin (dt) hajontaa..."):
        df_dt = get_dt_metrics()
        if not df_dt.empty and not pd.isna(df_dt['avg_dt'].iloc[0]):
            avg_dt = df_dt['avg_dt'].iloc[0]
            std_dt = df_dt['std_dt'].iloc[0]
            st.info(f"**Näytevälin (dt) tekninen tasaisuus:** Keskiarvo **{avg_dt:.2f} s** | Keskihajonta **±{std_dt:.2f} s**\n\n💡 *Tämä tarkoittaa, että hyväksytyn datan sijainti on päivittynyt keskimäärin n. {avg_dt:.1f} sekunnin välein. Pieni hajonta ({std_dt:.1f} s) viestii laadukkaasta seurannasta.*")
    
    st.divider()
    
    df_quality = get_quality_reasons()
    if not df_quality.empty:
        # Muodostetaan suppilodata (Funnel)
        # Järjestys: Raw -> Points -> Hours -> Temporal -> Engagement -> Gates -> Final
        reasons = {r: c for r, c in zip(df_quality['reason'], df_quality['count'])}
        
        total_rejected = df_quality['count'].sum()
        raw_total = v_cnt + total_rejected
        
        funnel_data = [
            {'stage': 'Raakadata (Kaikki sessiot)', 'count': raw_total},
            {'stage': 'Aktiivisuus-suodatin', 'count': raw_total - reasons.get('TOO_FEW_POINTS', 0)},
            {'stage': 'Aukioloaika-suodatin', 'count': raw_total - reasons.get('TOO_FEW_POINTS', 0) - reasons.get('OUTSIDE_OPERATIONAL_HOURS', 0)},
            {'stage': 'Kesto-suodatin', 'count': raw_total - reasons.get('TOO_FEW_POINTS', 0) - reasons.get('OUTSIDE_OPERATIONAL_HOURS', 0) - reasons.get('SESSION_TOO_LONG', 0) - reasons.get('SESSION_TOO_SHORT', 0)},
            {'stage': 'Läpäisy-suodatin (Penetration)', 'count': v_cnt + reasons.get('INVALID_GATES', 0) + reasons.get('TOO_SHORT_DISTANCE', 0)},
            {'stage': 'Hyväksytyt vierailut', 'count': v_cnt}
        ]
        df_funnel = pd.DataFrame(funnel_data)

        st.markdown("### 🌪️ Data Cleaning Funnel")
        st.caption("Visualisointi näyttää datan jalostumisen raakamassasta puhtaaksi tiedoksi. Jokainen porras karsii virheellistä tai epärelevanttia dataa.")
        
        from src.charts import create_etl_funnel
        fig_f = create_etl_funnel(df_funnel)
        st.pyplot(fig_f, width='stretch')

        with st.expander("Näytä tarkat hylkäyssyyt taulukkona"):
            df_quality['reason_fi'] = df_quality['reason'].map({
                'TOO_FEW_POINTS': 'Laitekohina / Liian vähän pisteitä',
                'INVALID_GATES': 'Väärä sisään/uloskäynti',
                'OUTSIDE_OPERATIONAL_HOURS': 'Aukioloaikojen ulkopuolella',
                'LOW_PENETRATION': 'Kävi vain ovella',
                'SESSION_TOO_SHORT': 'Kesto liian lyhyt (<60s)',
                'SESSION_TOO_LONG': 'Kesto liian pitkä (>90min)',
                'TOO_SHORT_DISTANCE': 'Liikkunut liian vähän'
            }).fillna(df_quality['reason'])
            st.table(df_quality[['reason_fi', 'count']].rename(columns={'reason_fi': 'Syy', 'count': 'Määrä'}))
