import pandas as pd
import numpy as np

class StoreDataCleaner:
    def __init__(self, config):
        self.config = config
        self.geom = config['geometry']
        self.logic = config['session_logic']
        self.motion = config['motion_filters']
        self.ops = config['operational_hours']
        self.gates = config['spatial_zones']['gates']

    def clean_spatial(self, df):
        # Kerätään hylkäykset jo tässä vaiheessa
        initial_count = len(df)
        mask_bounds = (df['x'] >= 0) & (df['x'] <= self.geom['store_max_x_cm']) & \
                      (df['y'] >= 0) & (df['y'] <= self.geom['store_max_y_cm'])
        
        # Dead zones
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
        if df.empty: return df
        df = df.sort_values(['node_id', 'timestamp'])
        df['dt'] = df.groupby('node_id')['timestamp'].diff().dt.total_seconds()
        df['new_session'] = (df['dt'] > self.logic['gap_threshold_s']) | df['dt'].isna()
        df['session_id'] = df.groupby('node_id')['new_session'].cumsum()
        df['final_sid'] = df['node_id'].astype(str) + "_" + df['session_id'].astype(str)
        return df

    def clean_motion(self, df):
        if df.empty: return df
        df = df.sort_values(['final_sid', 'timestamp'])
        
        # Lasketaan aika ja matka metreinä
        df['dt_step'] = df.groupby('final_sid')['timestamp'].diff().dt.total_seconds()
        df['dx_m'] = df.groupby('final_sid')['x'].diff() / 100.0
        df['dy_m'] = df.groupby('final_sid')['y'].diff() / 100.0
        
        # KORJAUS: Jos aikaero on 0 (tai alle 0.1s), pakotetaan nopeus massiiviseksi (999.0 m/s)
        # Jolloin suodatin varmasti nappaa ja poistaa kohinan
        df['speed_ms'] = np.where(
            df['dt_step'] > 0.1, 
            np.sqrt(df['dx_m']**2 + df['dy_m']**2) / df['dt_step'], 
            999.0  
        )
        
        # Suodatetaan
        max_speed = self.motion['max_jump_speed_ms']
        valid_points = df[(df['speed_ms'] <= max_speed) | df['speed_ms'].isna()].copy()
        
        return valid_points.drop(columns=['dt_step', 'dx_m', 'dy_m', 'speed_ms'])

    def is_operational(self, timestamp):
        wd = timestamp.day_name()
        hr = timestamp.hour
        # Sunnuntai vs arkityöajat
        days_cfg = self.ops['sun'] if wd == 'Sunday' else self.ops['mon-sat']
        return days_cfg[0] <= hr < days_cfg[1]

    def validate_sessions(self, df):
        valid_data = []
        stats = []
        quality_records = [] # Tänne kerätään sessiotason laatuarviot

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
                quality_records.append({'node_id': node_id, 'is_valid': False, 'reason': 'OUTSIDE_OPERATIONAL_HOURS'})
                continue

            # TARKISTUS 3: Portit (In/Out)
            start_pt = group.iloc[0]
            end_pt = group.iloc[-1]
            s_x1, s_x2, s_y1, s_y2 = self.gates['sisäänkäynti']['coords']
            is_start_valid = (s_x1 <= start_pt['x'] <= s_x2) and (s_y1 <= start_pt['y'] <= s_y2)

            k_x1, k_x2, k_y1, k_y2 = self.gates['kassa']['coords']
            is_end_valid = (k_x1 <= end_pt['x'] <= k_x2) and (k_y1 <= end_pt['y'] <= k_y2)

            if not (is_start_valid and is_end_valid):
                quality_records.append({'node_id': node_id, 'is_valid': False, 'reason': 'INVALID_GATES', 'more_info': f'start:{is_start_valid}, end:{is_end_valid}'})
                continue

            # TARKISTUS 4: Syvyys ja matka
            max_x = group['x'].max()
            duration = (group['timestamp'].max() - start_time).total_seconds()
            dx, dy = group['x'].diff().fillna(0)/100, group['y'].diff().fillna(0)/100
            dist = np.sqrt(dx**2 + dy**2).sum()

            if max_x < self.logic['min_store_penetration_x']:
                quality_records.append({'node_id': node_id, 'is_valid': False, 'reason': 'LOW_PENETRATION', 'more_info': f'max_x: {max_x}'})
                continue

            if dist < self.logic['min_dist_m']:
                quality_records.append({'node_id': node_id, 'is_valid': False, 'reason': 'TOO_SHORT_DISTANCE', 'more_info': f'dist: {dist:.1f}m'})
                continue

            # Jos kaikki ok
            group['node_id'] = node_id

            valid_data.append(group)
            stats.append({
                'visit_id': sid, 'node_id': node_id, 'start_time': start_time, 
                'end_time': group['timestamp'].max(), 'kesto_min': duration / 60
            })
            quality_records.append({'node_id': node_id, 'is_valid': True, 'reason': 'OK'})

        df_final = pd.concat(valid_data) if valid_data else pd.DataFrame()
        return df_final, pd.DataFrame(stats), pd.DataFrame(quality_records)