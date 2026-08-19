import os
import json
import time
from datetime import datetime, timedelta
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
            error_lat = real_eq['lat'] - pred['pred_lat']
            error_lon = real_eq['lon'] - pred['pred_lon']
            error_depth = real_eq['depth'] - pred['pred_depth']
            
            # Zaman farkı hesabı
            try:
                real_time = datetime.fromisoformat(real_eq['date'].replace('Z', '+00:00') if 'Z' in real_eq['date'] else real_eq['date'])
                if pred.get('pred_date'):
                    pred_time = datetime.fromisoformat(pred['pred_date'].replace('Z', '+00:00') if 'Z' in pred['pred_date'] else pred['pred_date'])
                    error_time_mins = (real_time - pred_time).total_seconds() / 60.0
                else:
                    error_time_mins = 0
            except Exception as e:
                error_time_mins = 0
            
            # Tahmini güncelle
            supabase.table('predictions').update({
                'matched_earthquake_id': latest_eq_id,
                'error_distance_km': dist_error,
                'error_mag': mag_error,
                'error_lat': error_lat,
                'error_lon': error_lon,
                'error_depth': error_depth,
                'error_time_mins': error_time_mins
            }).eq('id', pred['id']).execute()
            
            print(f"Tahmin değerlendirildi! Sapma: {dist_error:.2f} km")

    # 4. Açıkta (eşleşmemiş) tahmin var mı kontrol et, yoksa yeni tahmin üret
    pending_preds_res = supabase.table('predictions').select('*').is_('matched_earthquake_id', 'null').execute()
    
    if len(pending_preds_res.data) == 0:
        print("Yeni tahmin üretiliyor (V2 Algoritması)...")
        
        look_back = min(10, N)
        recent_eqs = db_eqs[-look_back:]
        
        # 1. Regresyon ile Fay Doğrultusu (Strike) hesabı
        sum_x = 0; sum_y = 0; sum_xy = 0; sum_xx = 0
        for eq in recent_eqs:
            sum_x += eq['lon']
            sum_y += eq['lat']
            sum_xy += eq['lon'] * eq['lat']
            sum_xx += eq['lon'] ** 2
            
        n_pts = len(recent_eqs)
        mean_x = sum_x / n_pts
        mean_y = sum_y / n_pts
        
        denominator = (sum_xx - n_pts * mean_x**2)
        if denominator == 0:
            slope = 0
        else:
            slope = (sum_xy - n_pts * mean_x * mean_y) / denominator
            
        # Doğrultu Vektörü (Normalize edilmiş)
        dir_lon = 1.0
        dir_lat = slope
        length = math.sqrt(dir_lon**2 + dir_lat**2)
        dir_lon /= length
        dir_lat /= length
        
        # Gidiş yönünü belirle (Doğuya mı Batıya mı gidiyor?)
        if recent_eqs[-1]['lon'] - recent_eqs[0]['lon'] < 0:
            dir_lon = -dir_lon
            dir_lat = -dir_lat
            
        # Ortalama Derinlik Eğilimi (Dip)
        depth_diff = recent_eqs[-1]['depth'] - recent_eqs[0]['depth']
        dir_depth = depth_diff / n_pts
        
        # 2. Kopma Mesafesi (Minimum Boyut)
        total_dist = 0
        for i in range(1, n_pts):
            total_dist += haversine(recent_eqs[i-1]['lat'], recent_eqs[i-1]['lon'], recent_eqs[i]['lat'], recent_eqs[i]['lon'])
        avg_step_km = total_dist / (n_pts - 1) if n_pts > 1 else 1.0
        
        # Alt limit (Fay kırığı üst üste binemez, en az 1 km olmalı)
        step_km = max(avg_step_km, 1.0) 
        step_deg = step_km / 111.0
        
        # 3. Gerilim (Strain) ve Magnitude Tahmini
        avg_mag = sum(eq['mag'] for eq in recent_eqs) / n_pts
        last_mag = recent_eqs[-1]['mag']
        
        if last_mag < avg_mag:
            pred_mag = avg_mag + 0.3 # Enerji birikiyor
        else:
            pred_mag = max(avg_mag - 0.2, 1.0) # Enerji boşaldı (artçı)
            
        pred_mag = round(pred_mag, 1)
        
        # 4. 3D Tahmin Noktalarını Yerleştir
        last_eq = recent_eqs[-1]
        
        remainder = N % 3
        points_to_predict = 3 if remainder == 0 else (3 - remainder)
        
        # P1: İleri doğru ana kırılma noktası
        p1_lat = last_eq['lat'] + (dir_lat * step_deg)
        p1_lon = last_eq['lon'] + (dir_lon * step_deg)
        p1_depth = last_eq['depth'] + dir_depth
        
        # P2 ve P3: Fay düzlemini genişleten yanal kırıklar
        perp_lat = -dir_lon
        perp_lon = dir_lat
        width_deg = step_deg * 0.6
        
        p2_lat = p1_lat + (perp_lat * width_deg)
        p2_lon = p1_lon + (perp_lon * width_deg)
        p2_depth = p1_depth + 1.5 # Derine doğru eğim
        
        p3_lat = p1_lat - (perp_lat * width_deg)
        p3_lon = p1_lon - (perp_lon * width_deg)
        p3_depth = p1_depth - 1.5 # Yüzeye doğru eğim
        
        pred_coords = [
            {'lat': p1_lat, 'lon': p1_lon, 'depth': p1_depth},
            {'lat': p2_lat, 'lon': p2_lon, 'depth': p2_depth},
            {'lat': p3_lat, 'lon': p3_lon, 'depth': p3_depth}
        ]
        
        # Zaman hesaplaması (En yeni depremler üzerinden ortalama boşluk)
        sample = recent_eqs[-10:]
        total_gap = timedelta(0)
        
        def parse_d(d_str):
            if not d_str: return datetime.now()
            return datetime.fromisoformat(d_str.replace('Z', '+00:00') if 'Z' in d_str else d_str)

        for i in range(len(sample) - 1):
            total_gap += parse_d(sample[i+1]['date']) - parse_d(sample[i]['date'])
            
        avg_gap = total_gap / (len(sample) - 1) if len(sample) > 1 else timedelta(minutes=60)
        base_time = parse_d(last_eq['date'])
        
        # Supabase'e ekle
        for p in range(points_to_predict):
            current_node = (remainder if remainder != 0 else 0) + p + 1
            
            # Node sırasına göre zamanı ileri at
            multiplier = current_node
            pred_time = base_time + (avg_gap * multiplier)
            
            new_pred = {
                'target_order': current_node,
                'pred_lat': pred_coords[p]['lat'],
                'pred_lon': pred_coords[p]['lon'],
                'pred_depth': pred_coords[p]['depth'],
                'pred_mag': pred_mag, # Gerilim (Strain) analizi ile tahmin edilen büyüklük
                'pred_date': pred_time.isoformat()
            }
            supabase.table('predictions').insert(new_pred).execute()
        
        print(f"{points_to_predict} yeni tahmin veritabanına eklendi.")
    else:
        print("Sistemde açık tahminler var, yeni deprem bekleniyor.")

if __name__ == "__main__":
    update_system()
