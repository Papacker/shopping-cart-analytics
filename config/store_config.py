store_config = {
    # --- Kaupan fyysinen koko ja karttapohjan asetukset ---
    "geometry": {
        "store_max_x_cm": 10406,      # Myymälän kokonaispituus X-suunnassa (senttimetreinä)
        "store_max_y_cm": 5220,       # Myymälän kokonaisleveys Y-suunnassa (senttimetreinä)
        "image": {
            "filename": "kauppa.jpg",  # Taustakuvana käytettävä pohjapiirros
            "width_px": 1280,          # Pohjakuvan leveys pikseleinä
            "height_px": 617,          # Pohjakuvan korkeus pikseleinä
            "scale_cm_per_px": 0.11015, # Kalibrointikerroin: kuinka monta cm yksi pikseli edustaa
            "origin_x_px": 108.7,      # Koordinaatiston nollapisteen (0,0) X-sijainti kuvassa
            "origin_y_px": 22.0,       # Koordinaatiston nollapisteen (0,0) Y-sijainti kuvassa
            "invert_y": True           # Käännetäänkö Y-akseli (kuvakoordinaatit vs. reaalimaailma)
        },
        "timezone": "Europe/Helsinki"  # Aikavyöhyke oikeaoppiseen ajan käsittelyyn
    },

    # --- Vyöhykemääritykset: Portit ja hylättävät alueet ---
    "spatial_zones": {
        "gates": {
            # Kassa-alue: koordinaattirajat (x1, x2, y1, y2), väri ja tyyppi (ulosmeno)
            "kassa": {"coords": (0, 800, 0, 2150), "color": "yellow", "type": "outbound"},
            # Sisäänkäynti: koordinaattirajat, väri ja tyyppi (sisääntulo)
            "sisäänkäynti": {"coords": (0, 500, 2150, 3000), "color": "lime", "type": "inbound"}
        },
        "dead_zones": {
            # Alueet, joista tuleva data suodatetaan pois 
            "varasto": (0, 1500, 3000, 5220),
            "lastaus": (8500, 10406, 0, 500),
            "lovi": (9830, 10406, 4700, 5220),
            "latauspiste_1": (0, 300, 2300, 2700),
            "latauspiste_2": (700, 1100, 3400, 3800)
        }
    },

    # --- Sessio-logiikka: Kriteerit, joilla asiointitapahtuma hyväksytään ---
    "session_logic": {
        "gap_threshold_s": 300,          # Jos datassa on >5 min tauko, aloitetaan uusi sessio
        "min_points": 50,                # Minimimäärä datapisteitä hyväksytylle reissulle
        "min_dist_m": 50.0,              # Asiakkaan on liikuttava vähintään 50 metriä
        "max_dist_m": 5000.0,            # Yläraja kuljetulle matkalle (suodattaa virheet)
        "min_time_s": 120,               # Asioinnin on kestettävä vähintään 2 minuuttia
        "max_time_s": 5400,              # Maksimikesto 1.5 tuntia
        "min_store_penetration_x": 500   # Kuinka monta cm myymälään on mentävä (estää "pikapyörähdykset")
    },

    # --- Liikesuodattimet: Sensorikohinan ja hyppyjen siivous ---
    "motion_filters": {
        "max_jump_speed_ms": 2.78,       # Maksiminopeus pisteiden välillä (n. 10 km/h)
        "max_avg_speed_ms": 1.5,         # Sallittu keskinopeus koko reissun aikana
        "min_avg_speed_ms": 0.12         # Miniminopeus (suodattaa paikalleen jätetyt kärryt)
    },

    # --- Operatiiviset tunnit: Milloin data on validia ---
    "operational_hours": {
        "mon-sat": (8, 21),              # Kaupan aukioloajat arkisin ja lauantaisin
        "sun": (9, 20)                   # Kaupan aukioloajat sunnuntaisin
    }
}

print("✅ Tiukennetut asetukset ladattu")