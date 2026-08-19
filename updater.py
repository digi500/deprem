import os
import json
import time
from datetime import datetime
import math
from supabase import create_client, Client
from fetch_data import fetch_kandilli_data # Assuming this returns the raw JSON list or we can just run it.

# Proje yapılandırması
SUPABASE_URL = "https://tiykapksaboucamusmbk.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRpeWthcGtzYWJvdWNhbXVzbWJrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4NzE2NTIyMSwiZXhwIjoyMTAyNzQxMjIxfQ.D_dVAm0ueAw4-bODs1zt4UMR3LZZxvrBVYgfqG6V4tI"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def haversine(lat1, lon1, lat2, lon2):
    # Dünya yarıçapı km
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    return distance

def update_system():
    print("Sistem güncelleniyor...")
    
    # 1. Kandilli'den verileri çek (fetch_data.py içindeki API'den)
    import requests
    from bs4 import BeautifulSoup

    url = 'http://www.koeri.boun.edu.tr/scripts/lst4.asp'
    response = requests.get(url)
    response.encoding = 'windows-1254'
    soup = BeautifulSoup(response.text, 'html.parser')
    pre_tag = soup.find('pre')
    if not pre_tag:
        print("Kandilli verisi alınamadı.")
        return

    lines = pre_tag.text.split('\n')
    earthquakes = []
    
    for line in lines[6:]:
        if len(line.strip()) == 0:
            continue
        try:
            parts = line.split()
            date_str = parts[0] + ' ' + parts[1]
            date_obj = datetime.strptime(date_str, '%Y.%m.%d %H:%M:%S')
            iso_date = date_obj.isoformat()
            
            lat = float(parts[2])
            lon = float(parts[3])
            depth = float(parts[4])
            
            # Sadece Adalar civarını al
            if not (40.75 <= lat <= 40.85 and 29.00 <= lon <= 29.20):
                continue

            mag = float(parts[6]) if parts[6] != '-.-' else 0.0
            
            loc_parts = []
            for p in parts[8:]:
                if p == 'İlksel' or p.startswith('REVIZE'):
                    break
                loc_parts.append(p)
            location = ' '.join(loc_parts)
            
            earthquakes.append({
                'date': iso_date,
                'lat': lat,
                'lon': lon,
                'depth': depth,
                'mag': mag,
                'location': location
            })
        except Exception as e:
            continue
            
    # Zamana göre sırala (eskiden yeniye)
    earthquakes.sort(key=lambda x: x['date'])
    
    if not earthquakes:
        print("Adalar civarında yeni deprem bulunamadı.")
        return

    # 2. Supabase'e ekle (zaten varsa UNIQUE constraint hata verir veya ignore ederiz)
    new_eq_added = False
    latest_eq_id = None
    
    # Supabase'deki mevcut depremleri al
    existing_eqs_res = supabase.table('earthquakes').select('date, lat, lon').execute()
    existing_set = set(f"{e['date']}_{e['lat']}_{e['lon']}" for e in existing_eqs_res.data)

    all_db_eqs = []
    
    for eq in earthquakes:
        eq_key = f"{eq['date']}_{eq['lat']}_{eq['lon']}"
        if eq_key not in existing_set:
            # Yeni deprem!
            res = supabase.table('earthquakes').insert(eq).execute()
            if len(res.data) > 0:
                new_eq_added = True
                latest_eq_id = res.data[0]['id']
                print(f"YENİ DEPREM EKLENDİ: {eq['date']} Mag: {eq['mag']}")
        
    # Tüm depremleri veritabanından çekip morfolojik analiz yapalım
    db_eqs_res = supabase.table('earthquakes').select('*').order('date').execute()
    db_eqs = db_eqs_res.data
    N = len(db_eqs)
    
    if N < 5:
        print("Tahmin için yeterli veri yok.")
        return
        
    # 3. Eğer yeni deprem olduysa, açıkta bekleyen tahminlerimizi kontrol et ve hatayı hesapla
    if new_eq_added and latest_eq_id:
        # Eşleşmemiş en eski tahmini bul
        unmatched_pred_res = supabase.table('predictions').select('*').is_('matched_earthquake_id', 'null').order('created_at').limit(1).execute()
        if len(unmatched_pred_res.data) > 0:
            pred = unmatched_pred_res.data[0]
            real_eq = db_eqs[-1] # En son deprem
            
            dist_error = haversine(pred['pred_lat'], pred['pred_lon'], real_eq['lat'], real_eq['lon'])
            mag_error = real_eq['mag'] - pred['pred_mag']
            
            # Tahmini güncelle
            supabase.table('predictions').update({
                'matched_earthquake_id': latest_eq_id,
                'error_distance_km': dist_error,
                'error_mag': mag_error
            }).eq('id', pred['id']).execute()
            
            print(f"Tahmin değerlendirildi! Sapma: {dist_error:.2f} km")

    # 4. Açıkta (eşleşmemiş) tahmin var mı kontrol et, yoksa yeni tahmin üret
    pending_preds_res = supabase.table('predictions').select('*').is_('matched_earthquake_id', 'null').execute()
    
    if len(pending_preds_res.data) == 0:
        print("Yeni tahmin üretiliyor...")
        # Algoritma:
        # Geçmişteki ortalama hata payını bul (Self-correcting bias)
        matched_preds_res = supabase.table('predictions').select('*').not_.is_('error_distance_km', 'null').execute()
        
        avg_err_lat = 0
        avg_err_lon = 0
        
        if len(matched_preds_res.data) > 0:
            # Sadece son 5 tahmini al
            recent_matched = matched_preds_res.data[-5:]
            for mp in recent_matched:
                # Eşleşen depremi bul (veritabanından veya basitçe sapmadan)
                pass # Gelişmiş hata düzeltmesi eklenebilir. Şimdilik basit tutuyoruz.
                
        # Ortalama adım (üçgen boyutu)
        total_dist = 0
        for i in range(1, N):
            total_dist += haversine(db_eqs[i-1]['lat'], db_eqs[i-1]['lon'], db_eqs[i]['lat'], db_eqs[i]['lon'])
        avg_step_km = total_dist / (N - 1) if N > 1 else 1.0
        
        # Son yön (Son 4 nokta arası)
        look_back = min(4, N-1)
        dir_lat = db_eqs[-1]['lat'] - db_eqs[-1 - look_back]['lat']
        dir_lon = db_eqs[-1]['lon'] - db_eqs[-1 - look_back]['lon']
        dir_depth = db_eqs[-1]['depth'] - db_eqs[-1 - look_back]['depth']
        
        # Normalize
        dir_len = math.sqrt(dir_lat**2 + dir_lon**2 + dir_depth**2)
        if dir_len == 0:
            dir_lat, dir_lon, dir_depth, dir_len = 0.01, 0, 0, 0.01
        dir_lat /= dir_len
        dir_lon /= dir_len
        dir_depth /= dir_len
        
        # Derece cinsinden ortalama adım hesabı (1 derece ~ 111 km)
        avg_step_deg = avg_step_km / 111.0
        
        last_eq = db_eqs[-1]
        
        remainder = N % 3
        points_to_predict = 3 if remainder == 0 else (3 - remainder)
        
        # Nokta 1: İleri
        p1_lat = last_eq['lat'] + (dir_lat * avg_step_deg)
        p1_lon = last_eq['lon'] + (dir_lon * avg_step_deg)
        p1_depth = last_eq['depth'] + (dir_depth * avg_step_deg) * 111.0 # Derinlik km
        
        # Nokta 2: İleri Sağ
        p2_lat = p1_lat + (dir_lon * avg_step_deg * 0.8)
        p2_lon = p1_lon + (-dir_lat * avg_step_deg * 0.8)
        p2_depth = p1_depth + 1.0
        
        # Nokta 3: İleri Sol
        p3_lat = p1_lat + (-dir_lon * avg_step_deg * 0.8)
        p3_lon = p1_lon + (dir_lat * avg_step_deg * 0.8)
        p3_depth = p1_depth - 1.0
        
        pred_coords = [
            {'lat': p1_lat, 'lon': p1_lon, 'depth': p1_depth},
            {'lat': p2_lat, 'lon': p2_lon, 'depth': p2_depth},
            {'lat': p3_lat, 'lon': p3_lon, 'depth': p3_depth}
        ]
        
        # Supabase'e ekle
        for p in range(points_to_predict):
            current_node = (remainder if remainder != 0 else 0) + p + 1
            new_pred = {
                'target_order': current_node,
                'pred_lat': pred_coords[p]['lat'],
                'pred_lon': pred_coords[p]['lon'],
                'pred_depth': pred_coords[p]['depth'],
                'pred_mag': last_eq['mag'] # Tahmini büyüklük
            }
            supabase.table('predictions').insert(new_pred).execute()
        
        print(f"{points_to_predict} yeni tahmin veritabanına eklendi.")
    else:
        print("Sistemde açık tahminler var, yeni deprem bekleniyor.")

if __name__ == "__main__":
    update_system()
