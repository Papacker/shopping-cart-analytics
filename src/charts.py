import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np


def create_pie_chart(df_health):
    """Luo piirakkakaavion datan laadusta."""
    fig, ax = plt.subplots(figsize=(8, 4))
    fig.patch.set_facecolor('#0e1117')
    ax.set_facecolor('#1a1d23')
    
    colors = ['#4cc9f0', '#f72585']
    ax.pie(df_health['count'], labels=df_health['reason'], autopct='%1.1f%%',
           colors=colors, textprops={'color':"w"}, startangle=140)
    
    plt.title("Datan laatu: Hyväksytyt vs Hylätyt", color='white')
    return fig


def create_hourly_bar_chart(df_hourly, peak_val=None):
    """Luo pinkin tuntikohtaisen pylväskaavion, jossa korkein huippu on korostettu keltaisella."""
    fig, ax = plt.subplots(figsize=(12, 5))
    fig.patch.set_facecolor('#0e1117')
    ax.set_facecolor('#1a1d23')
    
    # Suodatetaan aukioloajat (8-21)
    df = df_hourly[(df_hourly['tunti'] >= 8) & (df_hourly['tunti'] <= 20)].copy()
    labels = [f"{int(h)}-{int(h)+1}" for h in df['tunti']]
    
    # Väritetään: Pinkki (#f72585), mutta korkein huippu keltaisella (#ffd60a)
    max_c = df['count'].max()
    colors = ['#ffd60a' if c == max_c else '#f72585' for c in df['count']]
    alphas = [1.0 if c == max_c else 0.7 for c in df['count']]
    
    bars = ax.bar(labels, df['count'], color=colors, edgecolor='white', linewidth=0.5)
    
    # Asetetaan alfat manuaalisesti
    for bar, alpha in zip(bars, alphas):
        bar.set_alpha(alpha)
        
    if peak_val:
        ax.set_ylim(0, peak_val * 1.1)
    
    ax.set_xlabel("Kellonaika (Aikaväli)", color='white')
    ax.set_ylabel("Sessiot", color='white')
    ax.tick_params(colors='white')
    
    for spine in ax.spines.values():
        spine.set_edgecolor('#333')
        
    plt.title("Asiakasvirrat aukioloaikoina", color='white', pad=20)
    plt.tight_layout()
    return fig


def create_duration_histogram(df_visits, mean_val=None, median_val=None):
    """Luo histogrammin asiointiajoista keskiarvo- ja mediaaniviivoilla."""
    fig, ax = plt.subplots(figsize=(10, 4))
    fig.patch.set_facecolor('#0e1117')
    ax.set_facecolor('#1a1d23')
    
    if 'duration_seconds' in df_visits.columns:
        durations = df_visits[df_visits['duration_seconds'] <= 5400]['duration_seconds'] / 60.0
    else:
        durations = df_visits['kesto_min']
    
    ax.hist(durations, bins=30, color='#f72585', alpha=0.7, edgecolor='white')
    
    # Mediaani (Keltainen katkoviiva)
    m_val = median_val if median_val is not None else durations.median()
    ax.axvline(m_val, color='#ffd60a', linestyle='dashed', linewidth=2, label=f'Mediaani: {m_val:.1f} min')
    
    # Keskiarvo (Vaaleansininen pisteviiva)
    avg_val = mean_val if mean_val is not None else durations.mean()
    ax.axvline(avg_val, color='#4cc9f0', linestyle='dotted', linewidth=2.5, label=f'Keskiarvo: {avg_val:.1f} min')
    
    ax.set_xlabel("Kesto (min)", color='white')
    ax.set_ylabel("Lukumäärä", color='white')
    ax.tick_params(colors='white')
    ax.legend(facecolor='#1a1d23', labelcolor='white')
    
    for spine in ax.spines.values():
        spine.set_edgecolor('#333')
        
    plt.title("Asiointiajan jakauma", color='white')
    plt.tight_layout()
    return fig


def create_weekday_bar_chart(df_weekday):
    """Luo vaaleansinisen viikonpäiväkaavion, jossa suosituin päivä on pinkki."""
    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor('#0e1117')
    ax.set_facecolor('#1a1d23')
    
    # Väritetään: Vaaleansininen (#4cc9f0), mutta suosituin päivä pinkki (#f72585)
    max_c = df_weekday['count'].max()
    colors = ['#f72585' if c == max_c else '#4cc9f0' for c in df_weekday['count']]
    
    # Lisätään pieni gradientti alfan avulla (pitempi palkki = kirkkaampi)
    base_alpha = 0.5
    alphas = [1.0 if c == max_c else (base_alpha + (c/max_c)*(1-base_alpha)) for c in df_weekday['count']]
    
    bars = ax.bar(df_weekday['nimi'], df_weekday['count'], color=colors, edgecolor='white', linewidth=0.5)
    
    for bar, alpha in zip(bars, alphas):
        bar.set_alpha(alpha)
    
    # Lisätään lukumäärät palkkien päälle
    for i, v in enumerate(df_weekday['count']):
        ax.text(i, v + (max_c * 0.02), f"{int(v)}", 
                color='white', ha='center', fontweight='bold')

    ax.set_ylabel("Sessiot", color='white')
    ax.tick_params(colors='white')
    
    for spine in ax.spines.values():
        spine.set_edgecolor('#333')
        
    plt.title("Vierailut viikonpäivittäin", color='white', pad=20)
    plt.tight_layout()
    return fig


def create_departments_bar_chart(df_dep):
    """Luo vaakapalkkikaavion suosituimmista osastoista."""
    if df_dep.empty:
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "Ei osastodataa", ha='center')
        return fig

    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor('#0e1117')
    ax.set_facecolor('#1a1d23')
    
    # Käännetään järjestys niin että suosituin on ylhäällä
    df = df_dep.sort_values('käynnit', ascending=True)
    
    colors = plt.cm.viridis(np.linspace(0, 0.8, len(df)))
    bars = ax.barh(df['zone'], df['käynnit'], color=colors, edgecolor='none')
    
    for bar in bars:
        width = bar.get_width()

    ax.set_xlabel("Vierailut (kpl)", color='white')
    ax.tick_params(colors='white')
    for spine in ax.spines.values():
        spine.set_edgecolor('#333')
    
    ax.set_title("Suosituimmat osastot", color='white')
    plt.tight_layout()
    return fig


def create_checkout_bar_chart(df_kassa):
    """Luo pystypalkkikaavion kassapisteiden kuormituksesta."""
    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor('#0e1117')
    ax.set_facecolor('#1a1d23')
    
    ax.bar(df_kassa['zone'], df_kassa['käynnit'], color='#4cc9f0', alpha=0.8)
    
    ax.set_ylabel("Vierailut", color='white')
    ax.tick_params(colors='white')
    for spine in ax.spines.values():
        spine.set_edgecolor('#333')
    
    ax.set_title("Kassapisteiden kuormitus", color='white')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    return fig


def create_usage_heatmap(df_hourly):
    """Luo heatmapin kärryjen käyttöasteesta (tunti vs viikonpäivä) suomeksi."""
    df = df_hourly.copy()
    df['hour'] = df['bucket_start'].dt.hour
    
    # Suodatetaan aukioloajat (8-21)
    df = df[(df['hour'] >= 8) & (df['hour'] <= 20)]
    
    # Suomenkieliset viikonpäivät
    paiva_nimet = {
        'Monday': 'Maanantai', 'Tuesday': 'Tiistai', 'Wednesday': 'Keskiviikko',
        'Thursday': 'Torstai', 'Friday': 'Perjantai', 'Saturday': 'Lauantai', 'Sunday': 'Sunnuntai'
    }
    df['weekday_fi'] = df['bucket_start'].dt.day_name().map(paiva_nimet)
    
    # Järjestetään viikonpäivät
    days_fi = ['Maanantai', 'Tiistai', 'Keskiviikko', 'Torstai', 'Perjantai', 'Lauantai', 'Sunnuntai']
    
    # Luodaan aikaväli-labelit (8 -> "8-9")
    df['hour_range'] = df['hour'].apply(lambda h: f"{int(h)}-{int(h)+1}")
    ranges = [f"{h}-{h+1}" for h in range(8, 21)]
    
    pivot = df.pivot_table(index='hour_range', columns='weekday_fi', values='active_carts', aggfunc='mean')
    pivot = pivot.reindex(index=ranges, columns=days_fi).fillna(0)
    
    fig, ax = plt.subplots(figsize=(12, 6))
    fig.patch.set_facecolor('#0e1117')
    
    sns.heatmap(pivot, cmap='magma', ax=ax, cbar_kws={'label': 'Aktiiviset kärryt'}, annot=False)
    
    ax.set_title("Kärryjen käyttöaste (Tunti vs Viikonpäivä)", color='white', pad=20, fontsize=12)
    ax.set_xlabel("Viikonpäivä", color='white')
    ax.set_ylabel("Kellonaika (Aikaväli)", color='white')
    ax.tick_params(colors='white')
    
    plt.tight_layout()
    return fig


def create_idle_bar_chart(df_idle):
    """Luo selkeän pylväskaavion kärryjen keskimääräisistä lepoajoista."""
    fig, ax = plt.subplots(figsize=(12, 5))
    fig.patch.set_facecolor('#0e1117')
    ax.set_facecolor('#1a1d23')
    
    # Lajitellaan niin että pisimpään lepäävät ovat ensin
    df = df_idle.sort_values('median_idle_min', ascending=False)
    # Muutetaan minuuteista tunneiksi luettavuuden vuoksi
    idle_hours = df['median_idle_min'] / 60.0
    
    colors = plt.cm.plasma(np.linspace(0.2, 0.8, len(df)))
    bars = ax.bar(df['node_id'], idle_hours, color=colors, alpha=0.8, edgecolor='white', linewidth=0.5)
    
    ax.set_title("Kärryjen keskimääräinen lepoaika (Tuntia)", color='white', pad=20)
    ax.set_ylabel("Tunnit", color='white')
    ax.tick_params(colors='white', axis='x', rotation=45)
    
    for spine in ax.spines.values():
        spine.set_edgecolor('#333')
        
    plt.tight_layout()
    return fig


def create_maintenance_status_chart(df_sorted, limit_km):
    """Luo huoltotilannekaavion värikoodeilla."""
    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor('#0e1117')
    ax.set_facecolor('#1a1d23')
    
    # Väritetään matkan mukaan: <30 vihreä, 30-50 keltainen, >50 punainen
    colors = []
    for d in df_sorted['total_distance_km']:
        if d >= limit_km: colors.append('#f72585')      # Punainen
        elif d >= limit_km * 0.6: colors.append('#ffd60a') # Keltainen
        else: colors.append('#4cc9f0')                 # Sininen/Vihreä
        
    ax.bar(df_sorted['node_id'], df_sorted['total_distance_km'], color=colors, alpha=0.9)
    ax.axhline(limit_km, color='#f72585', ls='--', label=f'Huoltoraja ({limit_km} km)')
    
    ax.set_title("Kärryjen kuluneisuus ja huoltotarve", color='white')
    ax.set_ylabel("Kuljettu matka (km)", color='white')
    ax.tick_params(colors='white', axis='x', rotation=45)
    ax.legend(facecolor='#1a1d23', labelcolor='white')
    
    for spine in ax.spines.values():
        spine.set_edgecolor('#333')
        
    plt.tight_layout()
    return fig


def create_heatmap_chart(img, px_x, px_y, bins_val, colormap, alpha_val, real_w, real_h, sample_pct, v_max=None):
    """
    Luo korkealaatuisen lämpökartan. 
    Käyttää YlOrRd-värikarttaa ja parempaa tiheyden hallintaa.
    """
    if len(px_x) == 0:
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "Ei dataa valituilla suodattimilla", ha='center')
        return fig

    fig, ax = plt.subplots(figsize=(16, 8))
    fig.patch.set_facecolor('#0e1117')
    ax.set_facecolor('#0e1117')

    # Pohjakuva
    ax.imshow(img, extent=[0, real_w, real_h, 0], aspect='equal', zorder=0)

    # Heatmap overlay
    h = ax.hist2d(
        px_x, px_y, bins=bins_val, 
        range=[[0, real_w], [0, real_h]],
        cmap=colormap, alpha=alpha_val, cmin=1, zorder=1,
        vmax=v_max if v_max and v_max > 0 else None
    )

    # Väripalkki
    cb = fig.colorbar(h[3], ax=ax, shrink=0.6, pad=0.02)
    cb.set_label('Käyntitiheys', color='white')
    cb.ax.yaxis.set_tick_params(color='white', labelcolor='white')

    ax.set_xlim(0, real_w)
    ax.set_ylim(real_h, 0)
    
    ax.set_title(
        f"Myymälän liikennevirrat ({len(px_x):,} pistettä)",
        color='white', fontsize=14, pad=15
    )
    
    ax.axis('off')
    plt.tight_layout()
    return fig


def create_horizontal_bar_chart(df, color_code, x_label='Vierailut'):
    """Luo vaakapalkkikaavion Advanced Insights -välilehdelle."""
    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor('#0e1117')
    ax.set_facecolor('#1a1d23')
    
    bars = ax.barh(df['Osasto'], df['Osumat'], color=color_code, edgecolor='none', alpha=0.8)
    
    for bar in bars:
        width = bar.get_width()

    ax.tick_params(colors='white', labelsize=11)
    ax.set_xlabel(x_label, color='white', fontsize=12)
    
    for spine in ax.spines.values():
        spine.set_edgecolor('#333')
    
    plt.tight_layout()
    return fig


def create_weather_correlation_chart(df_merged):
    """Luo sääkorrelaatiokaavion, jossa on selkeä visuaalinen hierarkia."""
    fig, ax1 = plt.subplots(figsize=(14, 6))
    fig.patch.set_facecolor('#0e1117')
    ax1.set_facecolor('#1a1d23')
    
    # 1. Sademäärä (2. Prioriteetti - Taustalla, vahvempi sininen alue)
    if 'precipitation' in df_merged.columns:
        ax3 = ax1.twinx()
        ax3.spines['right'].set_position(('outward', 60))
        ax3.fill_between(df_merged['date'], df_merged['precipitation'], color='#4cc9f0', alpha=0.3, label='Sademäärä (mm)')
        ax3.set_ylabel('Sademäärä (mm)', color='#4cc9f0', fontsize=10)
        ax3.tick_params(axis='y', labelcolor='#4cc9f0')
        ax3.set_ylim(0, max(df_merged['precipitation'].max() * 3, 10))
    
    # 2. Kävijämäärät (1. Prioriteetti - Päärooli, vahva pinkki)
    color_visits = '#f72585'
    ax1.bar(df_merged['date'], df_merged['visits'], color=color_visits, alpha=0.9, label='Kävijät', zorder=10)
    ax1.set_ylabel('Kävijämäärä (Vierailut)', color=color_visits, fontsize=13, fontweight='bold')
    ax1.tick_params(axis='y', labelcolor=color_visits)
    ax1.tick_params(axis='x', colors='white', labelsize=10)
    
    # 3. Lämpötila (3. Prioriteetti - Hienovaraisena taustalla)
    ax2 = ax1.twinx()
    color_temp = '#ffd60a'
    ax2.plot(df_merged['date'], df_merged['temperature'], color=color_temp, linewidth=1.5, 
             marker='o', markersize=6, markerfacecolor='#0e1117', markeredgewidth=1.5, 
             label='Max Lämpötila', zorder=5, alpha=0.4) # Paljon läpinäkyvämpi
    
    ax2.set_ylabel('Lämpötila (°C)', color=color_temp, fontsize=10)
    ax2.tick_params(axis='y', labelcolor=color_temp)
    
    # Muotoilu
    ax1.grid(True, axis='y', color='white', alpha=0.05)
    for spine in ax1.spines.values():
        spine.set_edgecolor('#333')
    
    plt.title("SÄÄTILA VS. ASIAKASVIRRAT", color='white', pad=25, fontsize=16, fontweight='bold')
    fig.autofmt_xdate()
    
    # Legenda yhdistettynä
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    try:
        h3, l3 = ax3.get_legend_handles_labels()
        ax1.legend(h1 + h2 + h3, l1 + l2 + l3, loc='upper left', facecolor='#0e1117', labelcolor='white')
    except:
        ax1.legend(h1 + h2, l1 + l2, loc='upper left', facecolor='#0e1117', labelcolor='white')
    
    plt.tight_layout()
    return fig


def create_etl_funnel(df_funnel):
    """Luo tyylikkään ja selkeän suppilokaavion ETL-prosessille."""
    fig, ax = plt.subplots(figsize=(12, 7))
    fig.patch.set_facecolor('#0e1117')
    ax.set_facecolor('#1a1d23')
    
    # Käännetään data, jotta suppilo alkaa ylhäältä
    df = df_funnel.iloc[::-1].reset_index(drop=True)
    y_pos = np.arange(len(df))
    counts = df['count'].values
    stages = df['stage'].values
    
    max_val = counts.max()
    left_pos = (max_val - counts) / 2
    
    # Väripaletti (gradientti sinisestä violettiin/punaiseen)
    colors = plt.cm.cool(np.linspace(0.8, 0.2, len(df)))
    
    # Piirretään suppilon osat
    bars = ax.barh(y_pos, counts, left=left_pos, color=colors, alpha=0.85, edgecolor='white', linewidth=1)
    
    # Lisätään tekstit ja konversioprosentit
    for i in range(len(df)):
        # Määrä keskellä
        ax.text(max_val/2, i, f"{int(counts[i]):,}", 
                color='white', ha='center', va='center', fontweight='bold', fontsize=11)
        
        # Vaiheen nimi vasemmalla
        ax.text(-max_val*0.05, i, stages[i], 
                color='white', ha='right', va='center', fontsize=10)
        
        # Konversio suhteessa alkuperäiseen (%) oikealla
        pct_of_total = (counts[i] / max_val) * 100
        ax.text(max_val + max_val*0.05, i, f"{pct_of_total:.1f}%", 
                color='#4cc9f0', ha='left', va='center', fontweight='bold')
        
        # Vaiheiden välinen pudotus (drop-off)
        if i < len(df) - 1:
            diff = counts[i+1] - counts[i]
            if diff > 0:
                ax.text(max_val/2, i + 0.5, f"↓ -{int(diff):,}", 
                        color='#f72585', ha='center', va='center', fontsize=9, alpha=0.8)

    ax.set_xlim(-max_val*0.4, max_val*1.4)
    ax.axis('off')
    plt.title("Sessioiden jalostusprosessi", color='white', pad=30, fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    return fig
