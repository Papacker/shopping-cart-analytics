# config/store_config.py
store_config = {
    "geometry": {
        "store_max_x_cm": 10406,
        "store_max_y_cm": 5220,
        "image": {
            "filename": "kauppa.jpg",
            "width_px": 1280,
            "height_px": 617,
            "scale_cm_per_px": 8.11015,
            "origin_x_px": 50.0,
            "origin_y_px": 45.0,
            "invert_y": True
        },
        "timezone": "Europe/Helsinki"
    },
    "spatial_zones": {
        "gates": {
            "kassa": {"coords": (0, 800, 0, 2150), "color": "yellow", "type": "outbound"},
            "sisäänkäynti": {"coords": (0, 500, 2150, 3000), "color": "lime", "type": "inbound"}
        },
        "dead_zones": {
            "varasto": (0, 1500, 3000, 5220),
            "lastaus": (8500, 10406, 0, 500),
            "lovi": (9830, 10406, 4700, 5220),
            "latauspiste_1": (0, 300, 2300, 2700),
            "latauspiste_2": (700, 1100, 3400, 3800)
        }
    },
    "session_logic": {
        "gap_threshold_s": 300,
        "min_points": 50,
        "min_dist_m": 50.0,
        "max_dist_m": 5000.0,
        "min_time_s": 120,
        "max_time_s": 5400,
        "min_store_penetration_x": 500
    },
    "motion_filters": {
        "max_jump_speed_ms": 2.78,
        "max_avg_speed_ms": 1.5,
        "min_avg_speed_ms": 0.12
    },
    "operational_hours": {
        "mon-sat": (8, 21),
        "sun": (9, 20)
    }
}

# Varmistus (voit poistaa lopulta)
print("✅ Kaupan geometrinen konfiguraatio ladattu")