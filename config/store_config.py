store_config = {
    # --- Kaupan fyysinen koko ja karttapohjan asetukset ---
    "geometry": {
        "store_max_x_cm": 11206,      # Myymälän kokonaispituus X-suunnassa (senttimetreinä)
        "store_max_y_cm": 5220,       # Myymälän kokonaisleveys Y-suunnassa (senttimetreinä)
        "active_profile": "default",
        "map_profiles": {
            "default": {
                "filename": "kauppa.jpg",
                "width_px": 1222,
                "height_px": 567,
                "scale_cm_per_px": 9.17,
                "origin_x_px": 87.2,
                "origin_y_px": 0.0,
                "invert_y": True
            },
            "osasto": {
                "filename": "kauppa_osasto.jpg",
                "width_px": 1222,
                "height_px": 567,
                "scale_cm_per_px": 9.17,
                "origin_x_px": 87.2,
                "origin_y_px": 0.0,
                "invert_y": True
            },
            "kauppa2": {
                "filename": "kauppa2.jpg",
                "width_px": 1428,
                "height_px": 722,
                "scale_cm_per_px": 8.15, 
                "origin_x_px": 121.0, 
                "origin_y_px": 25.0,  
                "invert_y": True
            },
        },
        "timezone": "Europe/Helsinki"
    },

    # --- Vyöhykemääritykset: Portit ja hylättävät alueet ---
    "spatial_zones": {
        "gates": {
            "sisäänkäynti": {"coords": (0, 1790, 2350, 2975), "color": "lime", "type": "inbound"},
            "kassa": {"coords": (0, 700, 0, 2000), "color": "red", "type": "outbound"}
        },
        "dead_zones": {
            "varasto": (0, 1450, 3031, 5220),
            "lastaus": (8392, 10406, 0, 505),
            "lovi": (9902, 10406, 4659, 5220),
            "latauspiste_1": (0, 200, 2350, 2650),
            "latauspiste_2": (750, 1050, 3450, 3750)
        },
        "departments": {
        "1-2 Kirjat": {"coords": (1500, 2685, 3800, 5220), "color": "red"},
        "3-9 Vaatteet": {"coords": (2685, 5800, 3800, 5220), "color": "blue"},
        "10-11 Lasten ruoka": {"coords": (5800, 6900, 3800, 5220), "color": "orange"},
        "12 Snacks": {"coords": (6900, 7700, 3750, 5220), "color": "green"},
        "13-19 Juomat": {"coords": (7700, 10406, 3750, 5220), "color": "purple"},
        "Kausitori": {"coords": (450, 2050, 2350, 2650), "color": "cyan"},
        "20-25 Kauneus": {"coords": (2050, 3800, 2350, 3300), "color": "pink"},
        "26-34 Jalkineet": {"coords": (3800, 6490, 2350, 3300), "color": "brown"},
        "35-36 Elektroniikka": {"coords": (6490, 7105, 2350, 3300), "color": "cyan"},
        "37-42 Hevi": {"coords": (7105, 8895, 2350, 3300), "color": "lime"},
        "43-46 Leipomo": {"coords": (9300, 10406, 2220, 3550), "color": "gold"},
        "47 Liha/Kala": {"coords": (8325, 10406, 505, 2220), "color": "darkred"},
        "48-50 Pakasteet": {"coords": (6250, 8325, 0, 800), "color": "lightblue"},
        "61-63 Pakasteet": {"coords": (6250, 8325, 1050, 2220), "color": "lightblue"},
        "51-54 Maitotuotteet": {"coords": (4100, 6250, 0, 800), "color": "yellow"},
        "55-59 Lelut": {"coords": (3000, 4100, 0, 1000), "color": "magenta"},
        "60 Urheilu": {"coords": (1678, 3000, 0, 1000), "color": "silver"},
        "64-66 Kuivat": {"coords": (5600, 6250, 1050, 2220), "color": "darkgreen"},
        "66-69 Kuivat": {"coords": (4532, 5600, 1250, 2220), "color": "darkgreen"},
        "70 Lemmikit": {"coords": (4100, 4532, 1250, 2220), "color": "coral"},
        "71-72 Keittiö": {"coords": (3200, 4100, 1250, 2220), "color": "navy"},
        "73 Sesonki": {"coords": (2350, 3200, 1250, 2220), "color": "olive"},
        "74-75 Tekstiilit": {"coords": (1678, 2350, 1250, 2220), "color": "teal"},
        "76 Kukat": {"coords": (700, 1678, 0, 1000), "color": "indigo"},
        "77 Kukat": {"coords": (700, 1678, 1400, 2220), "color": "indigo"}
        },
        "checkouts": {
            "Kassa 8": {"coords": (-200, 700, 0, 275), "color": "red"},
            "Kassa 7": {"coords": (-200, 700, 275, 525), "color": "grey"},
            "Kassa 6": {"coords": (-200, 700, 525, 730), "color": "red"},
            "Kassa 5": {"coords": (-200, 700, 730, 975), "color": "grey"},
            "Kassa 4": {"coords": (-200, 700, 975, 1200), "color": "red"},
            "Kassa 3": {"coords": (-200, 700, 1200, 1425), "color": "grey"},
            "Kassa 2": {"coords": (-200, 700, 1425, 1700), "color": "red"},
            "Kassa 1": {"coords": (-200, 700, 1700, 2000), "color": "grey"}
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