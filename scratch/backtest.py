import os
import math
from datetime import datetime
from supabase import create_client

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def to_naive(dt_str):
    dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
    if dt.tzinfo is not None:
        dt = dt.replace(tzinfo=None)
    return dt

url = 'https://tiykapksaboucamusmbk.supabase.co'
key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRpeWthcGtzYWJvdWNhbXVzbWJrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODcxNjUyMjEsImV4cCI6MjEwMjc0MTIyMX0.D2YkQaF5Gfn49bsRpuoi3W1upoFfhGxdFQ-pBRW6IAM'
supabase = create_client(url, key)

res = supabase.table('earthquakes').select('*').order('date', desc=False).execute()
eqs = res.data

print(f"Toplam {len(eqs)} deprem bulundu.")

results = []

for i in range(10, len(eqs)):
    recent_eqs = eqs[i-10:i]
    target_eq = eqs[i]
    
    n_pts = len(recent_eqs)
    
    # V3 Logic
    sum_x = 0; sum_y = 0; sum_xy = 0; sum_xx = 0
    for eq in recent_eqs:
        sum_x += eq['lon']
        sum_y += eq['lat']
        sum_xy += eq['lon'] * eq['lat']
        sum_xx += eq['lon'] ** 2
        
    mean_x = sum_x / n_pts
    mean_y = sum_y / n_pts
    
    denominator = (sum_xx - n_pts * mean_x**2)
    if denominator == 0:
        slope = 0
    else:
        slope = (sum_xy - n_pts * mean_x * mean_y) / denominator
        
    dir_lon = 1.0
    dir_lat = slope
    length = math.sqrt(dir_lon**2 + dir_lat**2)
    dir_lon /= length
    dir_lat /= length
    
    if recent_eqs[-1]['lon'] - recent_eqs[0]['lon'] < 0:
        dir_lon = -dir_lon
        dir_lat = -dir_lat
        
    total_dist = 0
    for j in range(1, n_pts):
        total_dist += haversine(recent_eqs[j-1]['lat'], recent_eqs[j-1]['lon'], recent_eqs[j]['lat'], recent_eqs[j]['lon'])
    avg_step_km = total_dist / (n_pts - 1) if n_pts > 1 else 1.0
    step_km = max(avg_step_km, 1.0) 
    step_deg = step_km / 111.0
    
    # Magnitude
    avg_mag = sum(eq['mag'] for eq in recent_eqs) / n_pts
    last_mag = recent_eqs[-1]['mag']
    total_energy = sum(10 ** (1.5 * eq['mag']) for eq in recent_eqs)
    avg_energy = total_energy / n_pts
    recent_3_energy = sum(10 ** (1.5 * eq['mag']) for eq in recent_eqs[-3:]) / 3
    
    if recent_3_energy < avg_energy * 0.5:
        pred_mag = avg_mag + 0.5
    elif last_mag < avg_mag:
        pred_mag = avg_mag + 0.2
    else:
        pred_mag = max(avg_mag - 0.3, 1.0)
    pred_mag = round(pred_mag, 1)
    
    # P1 (Loc)
    cluster_eqs = recent_eqs[-5:]
    centroid_lat = sum(e['lat'] for e in cluster_eqs) / len(cluster_eqs)
    centroid_lon = sum(e['lon'] for e in cluster_eqs) / len(cluster_eqs)
    
    proj_lat = recent_eqs[-1]['lat'] + (dir_lat * step_deg)
    proj_lon = recent_eqs[-1]['lon'] + (dir_lon * step_deg)
    
    p1_lat = (proj_lat * 0.7) + (centroid_lat * 0.3)
    p1_lon = (proj_lon * 0.7) + (centroid_lon * 0.3)
    
    # Errors
    dist_err = haversine(p1_lat, p1_lon, target_eq['lat'], target_eq['lon'])
    mag_err = target_eq['mag'] - pred_mag
    
    # Time diff
    time_diffs = []
    for j in range(1, n_pts):
        dt1 = to_naive(recent_eqs[j-1]['date'])
        dt2 = to_naive(recent_eqs[j]['date'])
        time_diffs.append((dt2 - dt1).total_seconds())
    avg_time_diff = sum(time_diffs) / len(time_diffs) if time_diffs else 3600
    pred_time = to_naive(recent_eqs[-1]['date']).timestamp() + avg_time_diff
    actual_time = to_naive(target_eq['date']).timestamp()
    time_err_mins = (actual_time - pred_time) / 60.0
    
    results.append({
        'target_date': target_eq['date'],
        'target_mag': target_eq['mag'],
        'pred_mag': pred_mag,
        'dist_err': dist_err,
        'mag_err': mag_err,
        'time_err': time_err_mins
    })

avg_dist = sum(r['dist_err'] for r in results) / len(results)
avg_mag = sum(abs(r['mag_err']) for r in results) / len(results)
avg_time = sum(abs(r['time_err']) for r in results) / len(results)

print(f"Test Edilen Tahmin Sayısı: {len(results)}")
print(f"Ortalama Mesafe Hatası: {avg_dist:.2f} km")
print(f"Ortalama Büyüklük Hatası (Mutlak): {avg_mag:.2f}")
print(f"Ortalama Zaman Hatası (Mutlak): {avg_time:.2f} dk")

# Generate HTML Table
html = f"""
<div style="background: rgba(0,0,0,0.5); padding: 20px; border-radius: 10px; margin-top: 20px;">
    <h3 style="color: #4facfe;">V3 Model Backtest Sonuçları (Son {len(results)} Deprem)</h3>
    <div style="display: flex; gap: 20px; margin-bottom: 20px;">
        <div style="background: rgba(255,255,255,0.1); padding: 10px; border-radius: 5px;">📍 Ort. Mesafe Sapması: <strong>{avg_dist:.2f} km</strong></div>
        <div style="background: rgba(255,255,255,0.1); padding: 10px; border-radius: 5px;">📈 Ort. Mag Sapması: <strong>{avg_mag:.2f}</strong></div>
        <div style="background: rgba(255,255,255,0.1); padding: 10px; border-radius: 5px;">⏱️ Ort. Zaman Sapması: <strong>{avg_time:.2f} dk</strong></div>
    </div>
    <table style="width: 100%; border-collapse: collapse; font-size: 13px; text-align: left;">
        <tr style="border-bottom: 1px solid #4facfe;">
            <th>Tarih</th>
            <th>Gerçek Mag</th>
            <th>Tahmin Mag</th>
            <th>Mesafe Sapması</th>
            <th>Mag Sapması</th>
            <th>Zaman Sapması</th>
        </tr>
"""
for r in results[-10:]: # Sadece son 10'u gösterelim çok uzun olmasın
    color = "#44ee44" if r['dist_err'] < 2.0 else ("#ffaa00" if r['dist_err'] < 5.0 else "#ff4444")
    html += f"""
        <tr style="border-bottom: 1px solid rgba(255,255,255,0.1);">
            <td style="padding: 5px 0;">{r['target_date']}</td>
            <td>{r['target_mag']}</td>
            <td>{r['pred_mag']}</td>
            <td style="color: {color};"><strong>{r['dist_err']:.2f} km</strong></td>
            <td>{r['mag_err']:.2f}</td>
            <td>{r['time_err']:.0f} dk</td>
        </tr>
    """
html += "</table><p style='font-size: 11px; color:#888; margin-top: 10px;'>* Tabloda son 10 test sonucu gösterilmektedir.</p></div>"

with open('c:\\deprem\\scratch\\backtest_report.html', 'w', encoding='utf-8') as f:
    f.write(html)
