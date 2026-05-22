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
            ["🔥 Liikennevirrat (Lämpökartta)", "📍 Yksittäiset asiakasreitit"]
        )

        st.markdown("### ⚙️ Aikarajaus")
        paivat = {
            "📅 Kaikki päivät": -1,
            "Maanantai": 1, "Tiistai": 2, "Keskiviikko": 3,
            "Torstai": 4, "Perjantai": 5, "Lauantai": 6, "Sunnuntai": 0
        }
        valittu_paiva = st.selectbox("Viikonpäivä", list(paivat.keys()))
        tunnit_valinta = st.slider("Kellonaika", 8, 21, (8, 21))

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

    # SQL-ehdot valintojen mukaan
    where_clauses = []
    if paivat[valittu_paiva] != -1:
        where_clauses.append(f"EXTRACT(dow FROM CAST(v.start_time AS TIMESTAMP)) = {paivat[valittu_paiva]}")
    where_clauses.append(f"EXTRACT(hour FROM CAST(v.start_time AS TIMESTAMP)) BETWEEN {tunnit_valinta[0]} AND {tunnit_valinta[1]}")
    where_sql = "WHERE " + " AND ".join(where_clauses)

    label_paiva = valittu_paiva
    label_tunnit = f"{tunnit_valinta[0]}–{tunnit_valinta[1]}"

    img = mpimg.imread(str(IMAGE_PATH))
    real_h, real_w = img.shape[0], img.shape[1]

    if "Lämpökartta" in näkymä:
        with st.spinner("Haetaan lämpökarttadataa..."):
            query = f"""
                SELECT z.x, z.y
                FROM Zone z
                INNER JOIN Visit v ON z.visit_id = v.visit_id
                {where_sql}
                USING SAMPLE 5 PERCENT (bernoulli)
            """
            df_zone = fetch_data(query)

        with col_left:
            if df_zone.empty:
                st.warning("Valituilla suodattimilla ei löytynyt dataa.")
                return

            px_x, px_y = cm_to_px(df_zone['x'].values, df_zone['y'].values, profiili, real_w, real_h)
            mask = (px_x >= 0) & (px_x < real_w) & (px_y >= 0) & (px_y < real_h)
            
            fig = create_heatmap_chart(
                img, px_x[mask], px_y[mask], bins_val=40, colormap="YlOrRd", alpha_val=0.65, 
                real_w=real_w, real_h=real_h, sample_pct=5, v_max=60
            )
            st.pyplot(fig, width='stretch')

    else:
        with st.spinner("Haetaan validoituja asiointitietoja..."):
            # Haetaan pohjadata kaikista aikavälin asioinneista
            valid_visits_query = f"""
                SELECT DISTINCT v.visit_id, v.start_time
                FROM Visit v
                INNER JOIN Zone z ON z.visit_id = v.visit_id
                {where_sql.replace('z.', 'v.')}
                ORDER BY v.start_time ASC
            """
            df_all_visits = fetch_data(valid_visits_query)

        with col_right:
            st.markdown("### 🎯 Valitse asioinnit")
            if df_all_visits.empty:
                st.warning("Ei asiointeja valitulla aikavälillä.")
                valitut_id_list = []
            else:
                sallitut_indeksit = {11, 12, 17, 18, 20, 22, 26, 32, 36, 39, 40}
                
                labels = []
                vids_mapped = []
                
                # Käydään läpi aikavälin asioinnit ja poimitaan vain sallitut numerot
                for idx, row in enumerate(df_all_visits.itertuples(), 1):
                    if idx in sallitut_indeksit:
                        klo = str(row.start_time)[11:16]
                        lyhyt_id = str(row.visit_id)[:6]
                        label_txt = f"Asiointi {idx} (Klo {klo} | ID: {lyhyt_id})"
                        
                        labels.append(label_txt)
                        vids_mapped.append((label_txt, row.visit_id))
                
                if not labels:
                    st.info("Valitut asioinnit (11, 12...) eivät osu tälle kellonajalle tai päivälle. Säädä suodattimia.")
                    valitut_id_list = []
                else:
                    valitut_labelit = st.multiselect(
                        "Valitse esiteltävät asioinnit:",
                        options=labels,
                        help="Valittavana on vain esimääritetyt, visuaalisesti validit asiointireitit."
                    )
                    
                    # Haetaan visit_id-tunnukset valittujen tekstien perusteella
                    valitut_id_list = [vid for lbl, vid in vids_mapped if lbl in valitut_labelit]

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
                    """
                    df_route = fetch_data(query)
                    
                    fig = create_routes_chart(
                        img, df_route, cm_to_px, profiili, real_w, real_h, valitut_id_list
                    )
                    st.pyplot(fig, width='stretch')
                    st.caption("Vihreä pallo = Aloituspiste   ·  Pinkki neliö = Lopetuspiste ")