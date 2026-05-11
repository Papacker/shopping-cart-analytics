import pandas as pd
import duckdb
from pathlib import Path

# Poistettu top-level streamlit import terminaalivaroitusten välttämiseksi

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "database" / "store.db"


def fetch_data(query):
    """
    Suorittaa SQL-kyselyn turvallisesti ja yrittää uudelleen jos kanta on lukittu.
    Puhdistettu kaikista Streamlit-viittauksista terminaalivaroitusten välttämiseksi.
    """
    if not DB_PATH.exists():
        return pd.DataFrame()

    import time

    max_retries = 5
    for i in range(max_retries):
        try:
            # Käytetään explicit read_only modea ja estetään rinnakkaisongelmat
            with duckdb.connect(str(DB_PATH), config={'access_mode': 'read_only'}) as con:
                return con.execute(query).df()
        except duckdb.ConnectionException as e:
            if "different configuration" in str(e) or "lock" in str(e).lower():
                if i < max_retries - 1:
                    time.sleep(0.5)
                    continue
            print(f"❌ Tietokantavirhe (Kysely): {e}")
            return pd.DataFrame()
        except Exception as e:
            print(f"❌ Odottamaton virhe (Kysely): {e}")
            return pd.DataFrame()
    return pd.DataFrame()


def get_table_counts():
    """Hakee taulujen rivimäärät ja yrittää uudelleen jos kanta on lukittu."""
    counts = {}
    if not DB_PATH.exists():
        return counts

    query = """
        SELECT 'Zone' as table_name, COUNT(*) as count FROM Zone
        UNION ALL
        SELECT 'Visit', COUNT(*) FROM Visit
        UNION ALL
        SELECT 'ShoppingCart', COUNT(*) FROM ShoppingCart
        UNION ALL
        SELECT 'Quality', COUNT(*) FROM Quality
        UNION ALL
        SELECT 'Categories', COUNT(*) FROM Categories
        UNION ALL
        SELECT 'ZoneVisit', COUNT(*) FROM ZoneVisit
    """
    df = fetch_data(query)
    if not df.empty:
        return dict(zip(df['table_name'], df['count']))
    return counts


def get_health_metrics():
    """Hakee laadunvalvontatilastot (hylätyt vs hyväksytyt)."""
    q_count = fetch_data("SELECT COUNT(*) as cnt FROM Quality")
    v_count = fetch_data("SELECT COUNT(*) as cnt, (SELECT COUNT(*) FROM Zone) as points_sum FROM Visit")
    return q_count, v_count


def get_dt_metrics():
    """Laskee näytevälin (dt) keskiarvon ja hajonnan."""
    return fetch_data("""
        SELECT AVG(dt) as avg_dt, STDDEV(dt) as std_dt
        FROM (
            SELECT DATEDIFF('second', LAG(timestamp) OVER (PARTITION BY visit_id ORDER BY timestamp), timestamp) as dt
            FROM Zone
        ) WHERE dt IS NOT NULL AND dt < 60
    """)


def get_quality_reasons():
    """Hakee tarkat hylkäyssyyt Quality-taulusta."""
    return fetch_data("SELECT reason, COUNT(*) as count FROM Quality GROUP BY reason ORDER BY count DESC")


def get_traffic_visits():
    """Hakee vierailutiedot ja erottelee tunnit ja viikonpäivät analyysia varten."""
    return fetch_data("""
        SELECT *,
               EXTRACT(hour FROM start_time) as tunti,
               EXTRACT(dow FROM start_time) as viikonpaiva
        FROM Visit
    """)


def get_visit_metrics():
    """Hakee kaikki vierailutiedot."""
    return fetch_data("SELECT * FROM Visit")


def get_quality_stats():
    """Hakee hylkäyssyyt ja niiden määrät."""
    return fetch_data("SELECT reason, is_valid, COUNT(*) as count FROM Quality GROUP BY reason, is_valid")


def get_zone_sample(pct=10):
    """Hakee prosentuaalisen näytteen Zone-taulusta analytiikkaa varten."""
    return fetch_data(f"SELECT * FROM Zone USING SAMPLE {pct} PERCENT")


def get_all_zone_stats():
    """
    Hakee kaikkien kategorioiden vierailutilastot ZoneVisit-taulusta.
    Laskee nyt uniikit asiakkaat (sessiot) ja keskimääräisen viipymän.
    """
    return fetch_data("""
        SELECT
            c.name as zone,
            COUNT(DISTINCT zv.visit_id) as uniikit_asiakkaat,
            COUNT(zv.zone_visit_id) as osumat,
            AVG(DATEDIFF('second', zv.start_time, zv.end_time)) as avg_seconds
        FROM ZoneVisit zv
        JOIN Categories c ON zv.category_id = c.category_id
        GROUP BY c.name
        ORDER BY uniikit_asiakkaat DESC
    """)


def get_shopping_carts():
    """Hakee kaikki ostoskärrytiedot."""
    return fetch_data("SELECT * FROM ShoppingCart")


def get_active_carts_count():
    """Laskee aktiivisten kärryjen määrän."""
    df = fetch_data("SELECT COUNT(DISTINCT node_id) as count FROM Visit")
    return int(df['count'].iloc[0]) if not df.empty else 0


def get_avg_duration():
    """Laskee keskimääräisen asiointiajan minuutteina."""
    df = fetch_data("SELECT AVG(duration_seconds)/60.0 as avg_min FROM Visit")
    return float(df['avg_min'].iloc[0]) if not df.empty else 0.0


def get_total_distance():
    """Laskee kaikkien vierailujen yhteispituuden metreinä (HUOM: vaatisi total_distance_m sarakkeen)."""
    # Palautetaan 0 tai lasketaan Zone-taulusta jos tarpeen, mutta toistaiseksi estetään virhe
    return 0.0


def get_top_carts(limit=10):
    """Hakee eniten asioineet kärryt."""
    return fetch_data(f"""
        SELECT node_id, COUNT(*) as visit_count, SUM(duration_seconds)/60.0 as total_min
        FROM Visit
        GROUP BY node_id
        ORDER BY visit_count DESC
        LIMIT {limit}
    """)


def get_visit_details():
    """Hakee vierailujen yksityiskohdat ja kuvaukset."""
    return fetch_data("""
        SELECT v.visit_id, v.node_id, v.start_time, v.duration_seconds/60.0 as duration_min,
               c.description
        FROM Visit v
        JOIN ShoppingCart c ON v.node_id = c.node_id
        ORDER BY v.start_time DESC
    """)


def get_category_stats():
    """Laskee osastokohtaiset vierailutilastot."""
    return fetch_data("""
        SELECT c.name, COUNT(zv.visit_id) as visit_count,
               AVG(DATEDIFF('second', zv.start_time, zv.end_time)) as avg_stay_sec
        FROM Categories c
        LEFT JOIN ZoneVisit zv ON c.category_id = zv.category_id
        GROUP BY c.name
        ORDER BY visit_count DESC
    """)


def get_zone_visit_flow():
    """Hakee osastovierailujen polun (flow)."""
    return fetch_data("""
        SELECT zv.visit_id, c.name as category_name, zv.start_time
        FROM ZoneVisit zv
        JOIN Categories c ON zv.category_id = c.category_id
        ORDER BY zv.visit_id, zv.start_time
    """)


def get_heatmap_sample(sample_pct, where_clauses):
    """Hakee näytteen koordinaateista lämpökarttaa varten."""
    where_sql = " AND ".join(where_clauses)
    if where_sql:
        query = f"SELECT x, y FROM (SELECT x, y FROM Zone WHERE {where_sql}) USING SAMPLE {sample_pct} PERCENT (bernoulli)"
    else:
        query = f"SELECT x, y FROM Zone USING SAMPLE {sample_pct} PERCENT (bernoulli)"
    return fetch_data(query)


def get_daily_visits():
    """Hakee päivittäiset vierailumäärät."""
    return fetch_data("""
        SELECT CAST(start_time AS DATE) as date, COUNT(*) as visits
        FROM Visit
        GROUP BY date
        ORDER BY date
    """)


def get_cart_utilization_stats():
    """Laskee kärrykohtaiset käyttöasteet (sessiot/päivä, aktiiviset tunnit)."""
    return fetch_data("""
        WITH visit_days AS (
            SELECT
                node_id,
                CAST(start_time AS DATE) AS d,
                COUNT(*) AS visits_per_day,
                SUM(duration_seconds) AS active_seconds
            FROM Visit
            GROUP BY 1, 2
        )
        SELECT
            node_id,
            COUNT(*) AS active_days,
            AVG(visits_per_day) AS avg_visits_per_day,
            AVG(active_seconds) / 3600.0 AS avg_active_hours_per_day
        FROM visit_days
        GROUP BY 1
        ORDER BY avg_visits_per_day DESC
    """)


def get_cart_rotation_index():
    """Laskee rotaatioindeksin (kuinka suuren osan sessioista top 20% kärryistä hoitaa)."""
    return fetch_data("""
        WITH cart_visits AS (
            SELECT node_id, COUNT(*) AS visit_count
            FROM Visit
            GROUP BY 1
        ),
        ranked AS (
            SELECT
                node_id,
                visit_count,
                ROW_NUMBER() OVER (ORDER BY visit_count DESC) AS rn,
                COUNT(*) OVER () AS total_carts,
                SUM(visit_count) OVER () AS total_visits
            FROM cart_visits
        )
        SELECT
            SUM(visit_count) * 100.0 / FIRST(total_visits) AS top_20_pct_share
        FROM ranked
        WHERE rn <= CEIL(0.2 * total_carts)
    """)


def get_cart_idle_stats():
    """Laskee kärryjen idle-ajat (aika sessioiden välissä) per kärry."""
    return fetch_data("""
        WITH ordered_visits AS (
            SELECT
                node_id,
                visit_id,
                start_time,
                end_time,
                LAG(end_time) OVER (PARTITION BY node_id ORDER BY start_time) AS prev_end_time
            FROM Visit
        ),
        gaps AS (
            SELECT
                node_id,
                date_diff('minute', prev_end_time, start_time) AS idle_minutes
            FROM ordered_visits
            WHERE prev_end_time IS NOT NULL
        )
        SELECT
            node_id,
            COUNT(*) AS gap_count,
            MEDIAN(idle_minutes) AS median_idle_min,
            AVG(idle_minutes) AS avg_idle_min,
            MAX(idle_minutes) AS max_idle_min
        FROM gaps
        GROUP BY 1
        ORDER BY median_idle_min DESC
    """)


def get_hourly_cart_utilization():
    """Laskee aktiivisten kärryjen määrän tunneittain (käyttöaste)."""
    return fetch_data("""
        WITH hourly_spine AS (
            SELECT bucket_start
            FROM (
                SELECT MIN(start_time) as min_t, MAX(end_time) as max_t FROM Visit
            ) v,
            generate_series(
                date_trunc('day', v.min_t),
                date_trunc('day', v.max_t) + interval 1 day,
                interval 1 hour
            ) AS t(bucket_start)
        ),
        cart_hour_usage AS (
            SELECT
                h.bucket_start,
                COUNT(DISTINCT v.node_id) AS active_carts
            FROM hourly_spine h
            LEFT JOIN Visit v
                ON v.start_time < h.bucket_start + interval 1 hour
               AND v.end_time >= h.bucket_start
            GROUP BY 1
        )
        SELECT
            bucket_start,
            active_carts,
            active_carts * 1.0 / (SELECT COUNT(*) FROM ShoppingCart) AS utilization_rate
        FROM cart_hour_usage
        ORDER BY 1
    """)


def get_cart_anomalies():
    """Tunnistaa poikkeavat kärryt (ylikäyttö, alikäyttö) Z-scoren avulla."""
    return fetch_data("""
        WITH cart_stats AS (
            SELECT
                node_id,
                COUNT(*) AS visits,
                AVG(duration_seconds / 60.0) AS avg_visit_min
            FROM Visit
            GROUP BY 1
        ),
        summary AS (
            SELECT
                AVG(visits) AS mean_visits,
                STDDEV_SAMP(visits) AS sd_visits
            FROM cart_stats
        )
        SELECT
            c.node_id,
            c.visits,
            c.avg_visit_min,
            (c.visits - s.mean_visits) / NULLIF(s.sd_visits, 0) AS zscore_visits
        FROM cart_stats c
        CROSS JOIN summary s
        WHERE ABS((c.visits - s.mean_visits) / NULLIF(s.sd_visits, 0)) >= 1.5
        ORDER BY zscore_visits DESC
    """)


def get_cart_distances():
    """Hakee kärrykohtaiset kuljetut matkat (SQL-laskenta pisteiden perusteella)."""
    return fetch_data("""
        WITH point_lags AS (
            SELECT
                visit_id,
                x, y,
                LAG(x) OVER (PARTITION BY visit_id ORDER BY timestamp) as px,
                LAG(y) OVER (PARTITION BY visit_id ORDER BY timestamp) as py
            FROM Zone
        ),
        visit_distances AS (
            SELECT
                visit_id,
                SUM(SQRT(POWER(x - px, 2) + POWER(y - py, 2))) / 100.0 as dist_m
            FROM point_lags
            WHERE px IS NOT NULL
            GROUP BY visit_id
        )
        SELECT
            v.node_id,
            COUNT(v.visit_id) as total_trips,
            SUM(vd.dist_m) / 1000.0 as total_distance_km
        FROM Visit v
        LEFT JOIN visit_distances vd ON v.visit_id = vd.visit_id
        GROUP BY v.node_id
        ORDER BY total_distance_km DESC
    """)
def get_department_flow(departments):
    """
    Laskee osastokohtaiset vierailijamäärät (konversio) ja keskimääräiset viipymät.
    Käyttää SQL-tasoista spatiaalista leikkausta tehokkuuden vuoksi.
    """
    # Rakennetaan CASE-lauseke osastojen tunnistamiseen koordinaattien perusteella
    case_parts = []
    for name, info in departments.items():
        x1, x2, y1, y2 = info['coords']
        case_parts.append(f"WHEN x >= {x1} AND x <= {x2} AND y >= {y1} AND y <= {y2} THEN '{name}'")

    case_sql = "CASE " + " ".join(case_parts) + " END"

    return fetch_data(f"""
        WITH point_zones AS (
            SELECT
                visit_id,
                timestamp,
                {case_sql} as department
            FROM Zone
            WHERE department IS NOT NULL
        ),
        visit_durations AS (
            SELECT
                visit_id,
                department,
                MIN(timestamp) as entry,
                MAX(timestamp) as exit,
                DATEDIFF('second', MIN(timestamp), MAX(timestamp)) as duration_sec
            FROM point_zones
            GROUP BY visit_id, department
            HAVING duration_sec > 5  -- Suodatetaan pois pelkät ohikulkijat
        )
        SELECT
            department as zone,
            COUNT(DISTINCT visit_id) as unique_visits,
            AVG(duration_sec) / 60.0 as avg_dwell_min
        FROM visit_durations
        GROUP BY department
        ORDER BY unique_visits DESC
    """)
