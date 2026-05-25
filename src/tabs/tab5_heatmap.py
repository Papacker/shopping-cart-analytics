from pathlib import Path
import numpy as np
import streamlit as st
import matplotlib.image as mpimg
from config.store_config import store_config
from src.queries import fetch_data
from src.charts import create_heatmap_chart, create_routes_chart


def cm_to_px(x_cm, y_cm, prof, real_w, real_h):
    """Muuntaa UWB-koordinaatit (cm) kuvan pikseleiksi."""
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
    st.subheader("🔥 5. Myymälän liikennevirrat ja asiointianalyysi")

    PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
    PROFIILIT = store_config['geometry']['map_profiles']
    oletus_profiili = store_config['geometry']['active_profile']
    valikoima = list(PROFIILIT.keys())
    oletus_indeksi = valikoima.index(oletus_profiili) if oletus_profiili in valikoima else 0

    col_left, col_right = st.columns([3, 1])

    with col_right:
        st.markdown("### 📊 Näkymätyyppi")
        näkymä = st.radio(
            "Valitse kartta",
            ["🔥 Lämpökartta", "📍 Yksittäiset asiakasreitit"]
        )

        valitut_id_list = []
        where_sql = ""

        # Lämpökartta-kohtaiset suodattimet
        if "Lämpökartta" in näkymä:
            st.markdown("### ⚙️ Aikarajaus")
            paivat = {
                "📅 Kaikki päivät": -1,
                "Maanantai": 1, "Tiistai": 2, "Keskiviikko": 3,
                "Torstai": 4, "Perjantai": 5, "Lauantai": 6, "Sunnuntai": 0
            }
            valittu_paiva = st.selectbox("Viikonpäivä", list(paivat.keys()))
            tunnit_valinta = st.slider("Kellonaika", 8, 21, (8, 21))

            # SQL-ehdot valintojen mukaan
            where_clauses = []
            if paivat[valittu_paiva] != -1:
                where_clauses.append(f"EXTRACT(dow FROM CAST(v.start_time AS TIMESTAMP)) = {paivat[valittu_paiva]}")
            where_clauses.append(f"EXTRACT(hour FROM CAST(v.start_time AS TIMESTAMP)) BETWEEN {tunnit_valinta[0]} AND {tunnit_valinta[1]}")
            where_sql = "WHERE " + " AND ".join(where_clauses)
            
        else:
            # Reitit-kohtainen suodatin (nimenomaan VAIN kuratoidut priima-esimerkit, jotka ovat taatusti valideja ja siistejä)
            st.markdown("### 🎯 Valitse asioinnit")
            # Käytetään aitoja visit_id-tunnuksia, jotka todettiin ryhmässä visuaalisesti täysin virheettömiksi
            kuratoidut_reitit = [
                {"visit_id": "51968_3", "label": "Asiointi #1 (Lauantai Klo 12:06 | Kesto 22min)"},
                {"visit_id": "53936_4", "label": "Asiointi #2 (Torstai Klo 15:04 | Kesto 42min)"},
                {"visit_id": "52535_10", "label": "Asiointi #3 (Perjantai Klo 14:02 | Kesto 35min)"},
                {"visit_id": "52535_20", "label": "Asiointi #4 (Perjantai Klo 17:21 | Kesto 30min)"},
                {"visit_id": "51889_3", "label": "Asiointi #5 (Keskiviikko Klo 16:10 | Kesto 28min)"},
                {"visit_id": "53936_48", "label": "Asiointi #6 (Torstai Klo 11:27 | Kesto 25min)"},
                {"visit_id": "51889_37", "label": "Asiointi #7 (Keskiviikko Klo 13:02 | Kesto 21min)"},
                {"visit_id": "53011_7", "label": "Asiointi #8 (Tiistai Klo 17:50 | Kesto 18min)"},
                {"visit_id": "52535_86", "label": "Asiointi #9 (Perjantai Klo 09:21 | Kesto 15min)"},
                {"visit_id": "3200_26", "label": "Asiointi #10 (Lauantai Klo 13:59 | Kesto 12min)"},
                {"visit_id": "53924_28", "label": "Asiointi #11 (Torstai Klo 15:13 | Kesto 10min)"}
            ]
            
            labels = [x["label"] for x in kuratoidut_reitit]
            vids_mapped = [(x["label"], x["visit_id"]) for x in kuratoidut_reitit]
            
            valitut_labelit = st.multiselect(
                "Valitse esiteltävät asioinnit:",
                options=labels,
                default=labels[:1],  # Oletuksena valitaan ensimmäinen siisti asiointi
                help="Valittavana on vain esimääritetyt, visuaalisesti täysin validit ja kohinattomat asiointireitit."
            )
            
            valitut_id_list = [vid for lbl, vid in vids_mapped if lbl in valitut_labelit]

        st.markdown("### 🗺️ Karttapohja")
        valittu_avain = st.selectbox("Valitse karttapohja", options=valikoima, index=oletus_indeksi)
        profiili = PROFIILIT[valittu_avain]

        filename_raw = profiili['filename'].replace("images/", "")
        IMAGE_PATH = PROJECT_ROOT / "images" / filename_raw
        if not IMAGE_PATH.exists():
            IMAGE_PATH = PROJECT_ROOT / filename_raw

    if not IMAGE_PATH.exists():
        with col_left:
            st.error(f"⚠️ Taustakarttaa ei löydy: {IMAGE_PATH}")
        return

    img = mpimg.imread(str(IMAGE_PATH))
    real_h, real_w = img.shape[0], img.shape[1]

    if "Lämpökartta" in näkymä:
        with st.spinner("Haetaan lämpökarttadataa..."):
            query = f"""
                SELECT z.x, z.y, CAST(v.start_time AS DATE) as date
                FROM Zone z
                INNER JOIN Visit v ON z.visit_id = v.visit_id
                {where_sql} AND z.x >= 0 AND z.x <= 11206 AND z.y >= 0 AND z.y <= 5220
                USING SAMPLE 5 PERCENT (bernoulli)
            """
            df_zone = fetch_data(query)

        with col_left:
            if df_zone.empty:
                st.warning("Valituilla suodattimilla ei löytynyt dataa.")
                return

            px_x, px_y = cm_to_px(df_zone['x'].values, df_zone['y'].values, profiili, real_w, real_h)
            
            x_vals = df_zone['x'].values
            y_vals = df_zone['y'].values
            mask = (px_x >= 0) & (px_x < real_w) & (px_y >= 0) & (px_y < real_h) & \
                   (x_vals >= 0) & (x_vals <= 11206) & (y_vals >= 0) & (y_vals <= 5220)
            
            num_days = max(1, df_zone['date'].nunique()) if 'date' in df_zone.columns else 1
            
            fig = create_heatmap_chart(
                img, px_x[mask], px_y[mask], bins_val=130, colormap="turbo", alpha_val=0.6, 
                real_w=real_w, real_h=real_h, sample_pct=5, v_max=None, num_days=num_days
            )
            st.pyplot(fig, width='stretch')

    else:
        # Asiakasreitit näkymä
        with col_left:
            if len(valitut_id_list) == 0:
                st.info("💡 Valitse oikealta listalta numeroidut asiakaskäynnit, jotka haluat heijastaa myymäläkartalle.")
                fig = create_routes_chart(img, fetch_data("SELECT 1 WHERE FALSE"), cm_to_px, profiili, real_w, real_h, [])
                st.pyplot(fig, width='stretch')
            else:
                with st.spinner("Piirretään valittuja reittejä..."):
                    vids_sql = ", ".join([f"'{vid}'" for vid in valitut_id_list])
                    query = f"""
                        SELECT z.visit_id, z.zone_id, z.x, z.y
                        FROM Zone z
                        WHERE z.visit_id IN ({vids_sql})
                        ORDER BY z.visit_id, z.zone_id
                    """
                    df_route = fetch_data(query)
                    
                    fig = create_routes_chart(
                        img, df_route, cm_to_px, profiili, real_w, real_h, valitut_id_list
                    )
                    st.pyplot(fig, width='stretch')
                    st.caption("Vihreä pallo = Aloituspiste   ·  Pinkki neliö = Lopetuspiste")