from pathlib import Path
import streamlit as st
import matplotlib.image as mpimg
from config.store_config import store_config
from src.queries import get_heatmap_sample
from src.charts import create_heatmap_chart

def cm_to_px(x_cm, y_cm, prof, real_w, real_h):
    """
    Muuntaa UWB-koordinaatit (cm) kuvan pikseleiksi.
    - ox, oy: Origon (0,0 cm) sijainti pikseleinä kuvan vasemmasta yläkulmasta.
    - invert_y: Jos True, UWB Y kasvaa ylöspäin (pikseli-Y pienenee). 
               Jos False, UWB Y kasvaa alaspäin (pikseli-Y kasvaa).
    """
    ref_w = prof.get('width_px', 1)
    ref_h = prof.get('height_px', 1)
    
    ratio_x = real_w / ref_w
    ratio_y = real_h / ref_h
    
    ox = prof['origin_x_px'] * ratio_x
    oy = prof['origin_y_px'] * ratio_y
    scale_val = prof['scale_cm_per_px']
    
    scale_x = scale_val / ratio_x
    scale_y = scale_val / ratio_y
    
    px_x = ox + x_cm / scale_x
    
    if prof.get('invert_y', False):
        px_y = oy - y_cm / scale_y
    else:
        px_y = oy + y_cm / scale_y
        
    return px_x, px_y

def render_tab_heatmap():
    st.subheader("🔥 5. Lämpökartat (Spatiaalinen käyttäytyminen)")

    PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
    PROFIILIT = store_config['geometry']['map_profiles']
    oletus_profiili = store_config['geometry']['active_profile']
    
    valikoima = list(PROFIILIT.keys())
    oletus_indeksi = valikoima.index(oletus_profiili) if oletus_profiili in valikoima else 0

    col_left, col_right = st.columns([3, 1])

    with col_right:
        st.markdown("### 🗺️ Karttapohja")
        valittu_avain = st.selectbox(
            "Valitse karttapohja",
            options=valikoima,
            index=oletus_indeksi
        )
        prof_base = PROFIILIT[valittu_avain]
        
        show_calib = st.checkbox("🛠️ Kalibrointitila", value=False)
        if show_calib:
            st.info("Säädä heatmap kohdalleen ja kopioi arvot talteen.")
            ox_val = st.slider("Origo X (px)", -500.0, 1500.0, float(prof_base['origin_x_px']), step=5.0)
            oy_val = st.slider("Origo Y (px)", -500.0, 1000.0, float(prof_base['origin_y_px']), step=5.0)
            scale_val = st.slider("Skaala (cm/px)", 1.0, 20.0, float(prof_base['scale_cm_per_px']), step=0.1)
            inv_y = st.checkbox("Käännä Y-akseli (invert_y)", value=prof_base.get('invert_y', False))
            
            profiili = {
                'origin_x_px': ox_val,
                'origin_y_px': oy_val,
                'scale_cm_per_px': scale_val,
                'invert_y': inv_y,
                'width_px': prof_base.get('width_px', 1222),
                'height_px': prof_base.get('height_px', 567)
            }
        else:
            profiili = prof_base

        filename_raw = profiili['filename'].replace("images/", "")
        polku_vaihtoehdot = [
            PROJECT_ROOT / "images" / filename_raw,
            PROJECT_ROOT / filename_raw
        ]
        
        IMAGE_PATH = polku_vaihtoehdot[0] 
        for p in polku_vaihtoehdot:
            if p.exists():
                IMAGE_PATH = p
                break

        st.markdown("### ✨ Näkymän säädöt")
        
        bins_val = st.slider(
            "📍 Yksityiskohtien tarkkuus", 
            50, 400, 200, step=25,
            help="Suurempi arvo näyttää tarkemmin yksittäiset polut, pienempi arvo näyttää yleiset trendit."
        )
        
        vmax_val = st.slider(
            "🔥 Värien voimakkuus", 
            0, 1000, 0, 
            help="Säädä tätä, jos kartta näyttää liian haalealta tai liian punaiselta."
        )

        with st.expander("⚙️ Lisäasetukset"):
            sample_pct = st.slider("Datan kattavuus (%)", 1, 100, 10)
            alpha_val = st.slider("Läpinäkyvyys", 0.1, 1.0, 0.75)
            colormap = st.selectbox(
                "Väriteema",
                ["YlOrRd", "hot", "plasma", "inferno", "RdYlGn_r"],
                index=0
            )

        st.markdown("---")
        st.markdown("### 🕒 Aika-rajaus")
        paivat = {
            "📅 Kaikki päivät": -1, 
            "Maanantai": 1, "Tiistai": 2, "Keskiviikko": 3, 
            "Torstai": 4, "Perjantai": 5, "Lauantai": 6, "Sunnuntai": 0
        }
        valittu_paiva = st.selectbox("Valitse viikonpäivä", list(paivat.keys()))
        tunnit_valinta = st.slider("Kellonaika (tunnit)", 0, 23, (8, 21))

    if not IMAGE_PATH.exists():
        with col_left:
            st.error(f"⚠️ Taustakarttaa ei löydy: {IMAGE_PATH}")
    else:
        # 1. Haetaan data ensin, jotta se on käytettävissä kaikkialla
        with st.spinner("Ladataan pisteitä..."):
            where_clauses = []
            if paivat[valittu_paiva] != -1:
                where_clauses.append(f"EXTRACT(dow FROM timestamp) = {paivat[valittu_paiva]}")
            where_clauses.append(f"EXTRACT(hour FROM timestamp) BETWEEN {tunnit_valinta[0]} AND {tunnit_valinta[1]}")
            df_zone = get_heatmap_sample(sample_pct, where_clauses)

        with col_left:
            if df_zone.empty:
                st.warning("Valituilla suodattimilla ei löytynyt dataa.")
            else:
                img = mpimg.imread(str(IMAGE_PATH))
                real_h, real_w = img.shape[0], img.shape[1]

                px_x, px_y = cm_to_px(
                    df_zone['x'].values, df_zone['y'].values,
                    profiili, real_w, real_h
                )

                mask = (px_x >= -300) & (px_x < real_w + 300) & (px_y >= -300) & (px_y < real_h + 300)
                px_x = px_x[mask]
                px_y = px_y[mask]

                fig = create_heatmap_chart(
                    img, px_x, px_y, bins_val, colormap, alpha_val, 
                    real_w, real_h, sample_pct, v_max=vmax_val
                )
                st.pyplot(fig, width='stretch')

                st.caption(
                    f"Aktiiviset arvot -> Origo X: {profiili['origin_x_px']}, Origo Y: {profiili['origin_y_px']}, Skaala: {profiili['scale_cm_per_px']} | "
                    f"Kuva: {real_w}×{real_h} px"
                )
