store_config = {
    # --- Kaupan fyysinen koko ja karttapohjan asetukset ---
    "geometry": {
        "store_max_x_cm": 10406,      # Myymälän kokonaispituus X-suunnassa (senttimetreinä)
        "store_max_y_cm": 5220,       # Myymälän kokonaisleveys Y-suunnassa (senttimetreinä)
        "image": {
            "filename": "kauppa.jpg",  # Taustakuvana käytettävä pohjapiirros
            "width_px": 1280,          # Pohjakuvan leveys pikseleinä
            "height_px": 617,          # Pohjakuvan korkeus pikseleinä
            "scale_cm_per_px": 9.096,  # KALIBROITU: 10406 cm / (1252.7 - 108.7) px
            "origin_x_px": 108.7,      # Koordinaatiston nollapisteen (0,0) X-sijainti kuvassa
            "origin_y_px": 22.0,       # Koordinaatiston nollapisteen (0,0) Y-sijainti kuvassa
            "floor_plan_width_px": 1144.0,  # Leveys pisteestä 0 reunaan 10406
            "floor_plan_height_px": 572.0,  # Korkeus pisteestä 0 reunaan 5220
            "invert_y": True           # Käännetäänkö Y-akseli
        },
        "timezone": "Europe/Helsinki"
    },

    # --- Vyöhykemääritykset: Portit ja hylättävät alueet ---
    "spatial_zones": {
        "gates": {
            "sisäänkäynti": {"coords": (0, 1790, 2357, 2975), "color": "lime", "type": "inbound"},
            "kassa": {"coords": (0, 700, 0, 2021), "color": "red", "type": "outbound"}
        },
        "dead_zones": {
            "varasto": (0, 1566, 3031, 5220),
            "lastaus": (8392, 10406, 0, 505),
            "lovi": (9902, 10406, 4659, 5220),
            "latauspiste_1": (0, 200, 2350, 2650),
            "latauspiste_2": (750, 1050, 3450, 3750)
        },
        "departments": {
        "1-2 Kirjat": {"coords": (1566, 2685, 3536, 5220), "color": "red"},
        "3-9 Vaatteet": {"coords": (2685, 5800, 3536, 5220), "color": "blue"},
        "10-11 Lasten ruoka": {"coords": (5800, 6900, 3536, 5220), "color": "orange"},
        "12 Snacks": {"coords": (6900, 7700, 3536, 5220), "color": "green"},
        "13-19 Juomat": {"coords": (7700, 10406, 3536, 5220), "color": "purple"},
        "20-25 Kauneus": {"coords": (1790, 3850, 2357, 3536), "color": "pink"},
        "26-34 Jalkineet": {"coords": (3850, 6490, 2357, 3536), "color": "brown"},
        "35-36 Elektroniikka": {"coords": (6490, 7105, 2357, 3536), "color": "cyan"},
        "37-42 Hevi": {"coords": (7105, 8895, 2357, 3536), "color": "lime"},
        "43-46 Leipomo": {"coords": (8895, 10406, 2245, 3536), "color": "gold"},
        "47 Liha/Kala": {"coords": (8392, 10406, 505, 2245), "color": "darkred"},
        "48-50 & 61-63 Pakasteet": {"coords": (6250, 8392, 0, 2245), "color": "lightblue"},
        "51-54 Maitotuotteet": {"coords": (4150, 6250, 0, 898), "color": "yellow"},
        "55-59 Lelut": {"coords": (3000, 4150, 0, 1066), "color": "magenta"},
        "60 Urheilu": {"coords": (1678, 3000, 0, 1066), "color": "silver"},
        "64-69 Kuivat": {"coords": (4532, 6250, 898, 2245), "color": "darkgreen"},
        "70 Lemmikit": {"coords": (4150, 4532, 898, 2245), "color": "coral"},
        "71-72 Keittiö": {"coords": (3200, 4150, 1066, 2245), "color": "navy"},
        "73 Sesonki": {"coords": (2350, 3200, 1066, 2245), "color": "olive"},
        "74-75 Tekstiilit": {"coords": (1678, 2350, 1066, 2245), "color": "teal"},
        "76-77 Kukat": {"coords": (700, 1678, 0, 2245), "color": "indigo"}
        },
        "checkouts": {
            "Kassa 8": {"coords": (0, 700, 0, 337), "color": "red"},
            "Kassa 7": {"coords": (0, 700, 337, 539), "color": "grey"},
            "Kassa 6": {"coords": (0, 700, 539, 769), "color": "red"},
            "Kassa 5": {"coords": (0, 700, 769, 999), "color": "grey"},
            "Kassa 4": {"coords": (0, 700, 999, 1235), "color": "red"},
            "Kassa 3": {"coords": (0, 700, 1235, 1448), "color": "grey"},
            "Kassa 2": {"coords": (0, 700, 1448, 1740), "color": "red"},
            "Kassa 1": {"coords": (0, 700, 1740, 2021), "color": "grey"},
            "Info": {"coords": (0, 559, 2021, 2498), "color": "yellow"}
        }
    },

    # --- Sessio-logiikka: Kriteerit, joilla asiointitapahtuma hyväksytään ---
    "session_logic": {
        "gap_threshold_s": 300,
        "min_points": 50,
        "min_dist_m": 50.0,
        "max_dist_m": 5000.0,
        "min_time_s": 120,
        "max_time_s": 5400,
        "min_store_penetration_x": 500
    },

    # --- Liikesuodattimet: Sensorikohinan ja hyppyjen siivous ---
    "motion_filters": {
        "max_jump_speed_ms": 2.78,
        "max_avg_speed_ms": 1.5,
        "min_avg_speed_ms": 0.12
    },

    # --- Operatiiviset tunnit: Milloin data on validia ---
    "operational_hours": {
        "mon-sat": (8, 21),
        "sun": (10, 20)
    }
}

print("✅ Tiukennetut asetukset ladattu")