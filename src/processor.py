import duckdb
import pandas as pd
import numpy as np


class StoreDataCleaner:
    """
    Vastaa UWB-paikannusdatan puhdistuksesta, sessioinnista ja validoinnista.
    """

    def __init__(self, config):
        """Alustaa puhdistajan kauppakohtaisella konfiguraatiolla."""
        self.config = config
        self.geom = config['geometry']
        self.logic = config['session_logic']
        self.motion = config['motion_filters']
        self.ops = config['operational_hours']
        self.gates = config['spatial_zones']['gates']

    def get_categories_df(self):
        """
        Muuntaa store_config.py:n osastot ja kassat kategorioiksi.
        Palauttaa DataFramen, joka voidaan tallentaa Categories-tauluun.
        """
        rows = []
        cat_id = 1
        
        # Osastot
        for name, info in self.config['spatial_zones']['departments'].items():
            x1, x2, y1, y2 = info['coords']
            rows.append({'category_id': cat_id, 'name': name, 'x1': x1, 'x2': x2, 'y1': y1, 'y2': y2})
            cat_id += 1
            
        # Kassat
        for name, info in self.config['spatial_zones']['checkouts'].items():
            x1, x2, y1, y2 = info['coords']
            rows.append({'category_id': cat_id, 'name': name, 'x1': x1, 'x2': x2, 'y1': y1, 'y2': y2})
            cat_id += 1
            
        return pd.DataFrame(rows)

    def clean_spatial(self, df):
        """Poistaa koordinaatit, jotka ovat myymälän ulkopuolella tai dead zoneilla."""
        initial_count = len(df)
        mask_bounds = (df['x'] >= 0) & (df['x'] <= self.geom['store_max_x_cm']) & \
                      (df['y'] >= 0) & (df['y'] <= self.geom['store_max_y_cm'])
        
        # Dead zones hylkäykset
        rejected_points = df[~mask_bounds].copy()
        rejected_points['is_valid'] = False
        rejected_points['reason'] = 'OUT_OF_BOUNDS'

        df_in = df[mask_bounds].copy()
        
        for name, coords in self.config['spatial_zones']['dead_zones'].items():
            x1, x2, y1, y2 = coords
            dz_mask = (df_in['x'] >= x1) & (df_in['x'] <= x2) & (df_in['y'] >= y1) & (df_in['y'] <= y2)
            
            dz_points = df_in[dz_mask].copy()
            dz_points['is_valid'] = False
            dz_points['reason'] = f'DEAD_ZONE_{name.upper()}'
            rejected_points = pd.concat([rejected_points, dz_points])
            
            df_in = df_in[~dz_mask]

        return df_in, rejected_points

    def sessionize(self, df):
        """Jakaa laitekohtaisen datapistejonon erillisiksi asiointioistunnoiksi (gap-perusteinen)."""
        if df.empty:
            return df
        df = df.sort_values(['node_id', 'timestamp'])
        df['dt'] = df.groupby('node_id')['timestamp'].diff().dt.total_seconds()
        df['new_session'] = (df['dt'] > self.logic['gap_threshold_s']) | df['dt'].isna()
        df['session_id'] = df.groupby('node_id')['new_session'].cumsum()
        df['final_sid'] = df['node_id'].astype(str) + "_" + df['session_id'].astype(str)
        return df

    def clean_motion(self, df):
        """Poistaa epärealistiset nopeushypyt ja sensorikohinan."""
        if df.empty:
            return df
        df = df.sort_values(['final_sid', 'timestamp'])
        
        # Lasketaan aika ja matka metreinä
        df['dt_step'] = df.groupby('final_sid')['timestamp'].diff().dt.total_seconds()
        df['dx_m'] = df.groupby('final_sid')['x'].diff() / 100.0
        df['dy_m'] = df.groupby('final_sid')['y'].diff() / 100.0
        
        # Nopeuslaskenta ja suodatus
        df['speed_ms'] = np.where(
            df['dt_step'].isna(),
            np.nan,
            np.where(
                df['dt_step'] > 0.1,
                np.sqrt(df['dx_m']**2 + df['dy_m']**2) / df['dt_step'],
                999.0
            )
        )
        
        max_speed = self.motion['max_jump_speed_ms']
        valid_points = df[(df['speed_ms'] <= max_speed) | df['speed_ms'].isna()].copy()
        
        return valid_points.drop(columns=['dt_step', 'dx_m', 'dy_m', 'speed_ms'])

    def is_operational(self, timestamp):
        """Tarkistaa onko annettu ajanhetki kaupan aukioloaikojen sisällä."""
        wd = timestamp.day_name()
        hr = timestamp.hour
        days_cfg = self.ops['sun'] if wd == 'Sunday' else self.ops['mon-sat']
        return days_cfg[0] <= hr < days_cfg[1]

    def validate_sessions(self, df):
        """Validoi istunnot keston, matkan ja porttitunnistuksen perusteella."""
        valid_data = []
        stats = []
        quality_records = []

        if df.empty:
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

        for sid, group in df.groupby('final_sid'):
            node_id = group['node_id'].iloc[0]
            
            # TARKISTUS 1: Pistemäärä
            if len(group) < self.logic['min_points']:
                quality_records.append({'node_id': node_id, 'is_valid': False, 'reason': 'TOO_FEW_POINTS', 'more_info': f'pts: {len(group)}'})
                continue

            # TARKISTUS 2: Aukioloajat
            start_time = group['timestamp'].min()
            if not self.is_operational(start_time):
                quality_records.append({'node_id': node_id, 'is_valid': False, 'reason': 'OUTSIDE_OPERATIONAL_HOURS', 'more_info': f'start: {start_time}'})
                continue

            # TARKISTUS 3: Istunnon kesto
            end_time = group['timestamp'].max()
            duration_s = (end_time - start_time).total_seconds()
            if duration_s > self.logic['max_time_s']:
                quality_records.append({'node_id': node_id, 'is_valid': False, 'reason': 'SESSION_TOO_LONG', 'more_info': f'min: {duration_s/60:.1f}'})
                continue
            
            if duration_s < self.logic['min_time_s']:
                quality_records.append({'node_id': node_id, 'is_valid': False, 'reason': 'SESSION_TOO_SHORT', 'more_info': f'sec: {duration_s:.1f}'})
                continue
            
            # TARKISTUS 4: Läpäisy (kävikö myymälässä syvällä)
            penetration = group['x'].max()
            if penetration < self.logic['min_store_penetration_x']:
                quality_records.append({'node_id': node_id, 'is_valid': False, 'reason': 'LOW_PENETRATION', 'more_info': f'max_x: {penetration:.0f}cm'})
                continue

            # TARKISTUS 5: Matka
            dist_m = np.sqrt(np.diff(group['x']/100.0)**2 + np.diff(group['y']/100.0)**2).sum()
            if dist_m < self.logic['min_dist_m']:
                quality_records.append({'node_id': node_id, 'is_valid': False, 'reason': 'TOO_SHORT_DISTANCE', 'more_info': f'dist: {dist_m:.1f}m'})
                continue

            # TARKISTUS 6: Portit (OR-logiikka)
            has_inbound = any((group['x'] >= self.gates['sisäänkäynti']['coords'][0]) & (group['x'] <= self.gates['sisäänkäynti']['coords'][1]) &
                              (group['y'] >= self.gates['sisäänkäynti']['coords'][2]) & (group['y'] <= self.gates['sisäänkäynti']['coords'][3]))
            has_outbound = any((group['x'] >= self.gates['kassa']['coords'][0]) & (group['x'] <= self.gates['kassa']['coords'][1]) &
                               (group['y'] >= self.gates['kassa']['coords'][2]) & (group['y'] <= self.gates['kassa']['coords'][3]))

            if not (has_inbound or has_outbound):
                quality_records.append({'node_id': node_id, 'is_valid': False, 'reason': 'INVALID_GATES', 'more_info': f'in:{has_inbound} out:{has_outbound}'})
                continue

            # Jos läpäisi kaikki, lisätään validiin dataan
            valid_data.append(group)
            stats.append({
                'visit_id': sid,
                'node_id': node_id,
                'start_time': start_time,
                'end_time': end_time,
                'duration_seconds': duration_s,
                'total_distance_m': dist_m
            })

        if not valid_data:
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(quality_records)
            
        return pd.concat(valid_data), pd.DataFrame(stats), pd.DataFrame(quality_records)

    def calculate_zone_visits(self, df, df_categories):
        """
        Laskee osastovierailut (ZoneVisit) hyödyntämällä DuckDB:n SQL-natiivia spatial joinia.
        Huomattavasti nopeampi kuin Python-silmukat.
        """
        if df.empty or df_categories.empty:
            return pd.DataFrame(columns=['visit_id', 'category_id', 'start_time', 'end_time'])
            
        con = duckdb.connect()
        con.register('df_work_local', df[['final_sid', 'x', 'y', 'timestamp']])
        con.register('df_categories_local', df_categories)
        
        query = """
            SELECT 
                final_sid, 
                timestamp, 
                FIRST(category_id) as category_id
            FROM df_work_local
            JOIN df_categories_local ON 
                df_work_local.x >= df_categories_local.x1 AND 
                df_work_local.x <= df_categories_local.x2 AND
                df_work_local.y >= df_categories_local.y1 AND 
                df_work_local.y <= df_categories_local.y2
            GROUP BY final_sid, timestamp
            ORDER BY final_sid, timestamp
        """
        
        df_cats_raw = con.execute(query).df()
        con.close()
        
        if df_cats_raw.empty:
            return pd.DataFrame(columns=['visit_id', 'category_id', 'start_time', 'end_time'])
        
        df_cats = df_cats_raw
        
        # Etsitään milloin kategoria vaihtuu (tai sessio vaihtuu)
        df_cats['cat_changed'] = (df_cats['category_id'] != df_cats['category_id'].shift()) | \
                                 (df_cats['final_sid'] != df_cats['final_sid'].shift())
        
        df_cats['visit_group'] = df_cats['cat_changed'].cumsum()
        
        # Aggregoidaan vierailut
        zone_visits = df_cats.groupby(['final_sid', 'visit_group', 'category_id']).agg(
            start_time=('timestamp', 'min'),
            end_time=('timestamp', 'max')
        ).reset_index()
        
        zone_visits = zone_visits.rename(columns={'final_sid': 'visit_id'})
        
        return zone_visits[['visit_id', 'category_id', 'start_time', 'end_time']]