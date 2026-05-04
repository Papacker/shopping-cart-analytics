import streamlit as st
import matplotlib.image as mpimg
from src.queries import get_heatmap_sample
from src.charts import create_heatmap_chart

def cm_to_px(x_cm, y_cm, prof, real_w, real_h, manual_invert_y=False, m_ox=None, m_oy=None, m_scale=None):
    """
    Muuntaa UWB-koordinaatit (cm) kuvan pikseleiksi.
    """
    ref_w = prof.get('width_px', 1)
    ref_h = prof.get('height_px', 1)
    
    ratio_x = real_w / ref_w
    ratio_y = real_h / ref_h
    
    # Käytetään joko manuaalista tai konfiguraation arvoa
    ox = (m_ox if m_ox is not None else prof['origin_x_px']) * ratio_x
    oy = (m_oy if m_oy is not None else prof['origin_y_px']) * ratio_y
    scale_val = m_scale if m_scale is not None else prof['scale_cm_per_px']
    
    scale_x = scale_val / ratio_x
    scale_y = scale_val / ratio_y
    
    px_x = ox + x_cm / scale_x
    
    # Huomioidaan sekä profiilin että manuaalinen kääntö
    should_invert = prof.get('invert_y', False)
    if manual_invert_y:
        should_invert = not should_invert

    if should_invert:
        px_y = real_h - (oy + y_cm / scale_y)
    else:
        px_y = oy + y_cm / scale_y
        
    return px_x, px_y

def render_tab_heatmap(IMAGE_PATH, profiili, valittu_avain):
    st.subheader("🔥 5. Lämpökartat (Spatiaalinen käyttäytyminen)")

    if not IMAGE_PATH.exists():
        st.error(f"⚠️ Kuvaa ei löydy: {IMAGE_PATH}")
    else:
        col_left, col_right = st.columns([3, 1])

        with col_right:
            st.markdown("### 🛠️ Kalibrointi")
            manual_invert_y = st.checkbox("Peilaa pystysuunnassa", value=False)
            
            with st.expander("🎯 Hienosäätö (Vain kalibrointi)"):
                m_ox = st.slider("Origo X", -500, 1000, int(profiili['origin_x_px']))
                m_oy = st.slider("Origo Y", -500, 1000, int(profiili['origin_y_px']))
                m_scale = st.slider("Skaala (cm/px)", 1.0, 30.0, float(profiili['scale_cm_per_px']), step=0.1)
                st.info("💡 Säädä näitä, kunnes heatmap istuu hyllyihin. Kerro sitten luvut minulle!")

            sample_pct = st.slider(
                "Näytteistysprosentti (%)", 1, 100, 10,
                help="Kuinka suuri osa pisteistä piirretään (koko kanta = 100%)"
            )
            colormap = st.selectbox(
                "Värikartta",
                ["YlOrRd", "hot", "plasma", "inferno", "RdYlGn_r"],
                index=0
            )
            alpha_val = st.slider("Läpinäkyvyys", 0.3, 1.0, 0.75, step=0.05)
            bins_val  = st.slider("Tarkkuus (bins)", 50, 400, 200, step=25)
            
            st.markdown("### 🕒 Suodattimet")
            paivat = {"Kaikki": -1, "Maanantai": 1, "Tiistai": 2, "Keskiviikko": 3, "Torstai": 4, "Perjantai": 5, "Lauantai": 6, "Sunnuntai": 0}
            valittu_paiva = st.selectbox("Viikonpäivä", list(paivat.keys()))
            tunnit_valinta = st.slider("Kellonaika", 0, 23, (8, 21))

        # 1. Haetaan data ensin, jotta se on käytettävissä kaikkialla
        with st.spinner("Ladataan pisteitä..."):
            where_clauses = []
            if paivat[valittu_paiva] != -1:
                where_clauses.append(f"EXTRACT(dow FROM timestamp) = {paivat[valittu_paiva]}")
            where_clauses.append(f"EXTRACT(hour FROM timestamp) BETWEEN {tunnit_valinta[0]} AND {tunnit_valinta[1]}")
            df_zone = get_heatmap_sample(sample_pct, where_clauses)

        # 2. Piirretään diagnostiikka (nyt df_zone on olemassa)
        with col_right:
            with st.expander("🔍 Tekninen diagnostiikka"):
                st.write(f"Profiili: `{valittu_avain}`")
                st.write(f"Scale: `{profiili['scale_cm_per_px']}`")
                st.write(f"Origin: `({profiili['origin_x_px']}, {profiili['origin_y_px']})`")
                st.write(f"Invert Y: `{profiili['invert_y']}`")
                if not df_zone.empty:
                    st.write(f"Data X: `{df_zone['x'].min():.0f} - {df_zone['x'].max():.0f}`")
                    st.write(f"Data Y: `{df_zone['y'].min():.0f} - {df_zone['y'].max():.0f}`")

        with col_left:
            if df_zone.empty:
                st.warning("Valituilla suodattimilla ei löytynyt dataa.")
            else:
                img = mpimg.imread(str(IMAGE_PATH))
                real_h, real_w = img.shape[0], img.shape[1]

                px_x, px_y = cm_to_px(
                    df_zone['x'].values, df_zone['y'].values,
                    profiili, real_w, real_h,
                    manual_invert_y, m_ox, m_oy, m_scale
                )

                mask = (px_x >= -300) & (px_x < real_w + 300) & (px_y >= -300) & (px_y < real_h + 300)
                px_x = px_x[mask]
                px_y = px_y[mask]

                fig = create_heatmap_chart(img, px_x, px_y, bins_val, colormap, alpha_val, real_w, real_h, sample_pct)
                st.pyplot(fig, width='stretch')

                st.caption(
                    f"Aktiiviset arvot -> Origo X: {m_ox}, Origo Y: {m_oy}, Skaala: {m_scale} | "
                    f"Kuva: {real_w}×{real_h} px"
                )
