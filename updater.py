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

    new_eqs_this_run = []
    
    for eq in earthquakes:
        eq_key = f"{eq['date']}_{eq['lat']}_{eq['lon']}"
        if eq_key not in existing_set:
            # Yeni deprem!
            res = supabase.table('earthquakes').insert(eq).execute()
            if len(res.data) > 0:
                new_eq_added = True
                new_eqs_this_run.append(res.data[0])
                print(f"YENİ DEPREM EKLENDİ: {eq['date']} Mag: {eq['mag']}")
                
    # Yeni depremleri kronolojik sıraya diz (eskiden yeniye)
    new_eqs_this_run.sort(key=lambda x: x['date'])
        
    # Tüm depremleri veritabanından çekip morfolojik analiz yapalım
    db_eqs_res = supabase.table('earthquakes').select('*').order('date').execute()
    db_eqs = db_eqs_res.data
    N = len(db_eqs)
    
    if N < 5:
        print("Tahmin için yeterli veri yok.")
        return
        
    # 3. Eğer yeni deprem(ler) olduysa, açıkta bekleyen tahminlerimizi sırayla kontrol et ve eşleştir
    if new_eqs_this_run:
        # Eşleşmemiş tüm tahminleri eskiden yeniye bul
        unmatched_preds_res = supabase.table('predictions').select('*').is_('matched_earthquake_id', 'null').order('created_at').execute()
        unmatched_preds = unmatched_preds_res.data
        
        for i, real_eq in enumerate(new_eqs_this_run):
            if i < len(unmatched_preds):
                pred = unmatched_preds[i]
                
                dist_error = haversine(pred['pred_lat'], pred['pred_lon'], real_eq['lat'], real_eq['lon'])
                mag_error = real_eq['mag'] - pred['pred_mag']
                error_lat = real_eq['lat'] - pred['pred_lat']
                error_lon = real_eq['lon'] - pred['pred_lon']
                error_depth = real_eq['depth'] - pred['pred_depth']
                
                # Zaman farkı hesabı
                try:
                    def to_naive(dt_str):
                        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
                        if dt.tzinfo is not None:
                            dt = dt.replace(tzinfo=None)
                        return dt
                        
                    real_time = to_naive(real_eq['date'])
                    if pred.get('pred_date'):
                        pred_time = to_naive(pred['pred_date'])
                        error_time_mins = (real_time - pred_time).total_seconds() / 60.0
                    else:
                        error_time_mins = 0
                except Exception as e:
                    print("Time error:", e)
                    error_time_mins = 0
                
                # Tahmini güncelle
                supabase.table('predictions').update({
                    'matched_earthquake_id': real_eq['id'],
                    'error_distance_km': dist_error,
                    'error_mag': mag_error,
                    'error_lat': error_lat,
                    'error_lon': error_lon,
                    'error_depth': error_depth,
                    'error_time_mins': error_time_mins
                }).eq('id', pred['id']).execute()
                
                print(f"Tahmin değerlendirildi! ({real_eq['date']} -> Tahmin {pred['target_order']}) Sapma: {dist_error:.2f} km")
            else:
                print(f"Uyarı: {real_eq['date']} tarihli deprem için hazırda bekleyen bir tahmin yoktu, boş geçiliyor.")

    # 4. Açıkta (eşleşmemiş) tahmin var mı kontrol et, yoksa yeni tahmin üret
    pending_preds_res = supabase.table('predictions').select('*').is_('matched_earthquake_id', 'null').execute()
    
    if len(pending_preds_res.data) == 0:
        print("Yeni tahmin üretiliyor (V3 Algoritması)...")
        
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
        
        # 3. Kümülatif Sismik Moment (Enerji Birikimi) V3 Algoritması
        avg_mag = sum(eq['mag'] for eq in recent_eqs) / n_pts
        last_mag = recent_eqs[-1]['mag']
        
        total_energy = sum(10 ** (1.5 * eq['mag']) for eq in recent_eqs)
        avg_energy = total_energy / n_pts
        recent_3_energy = sum(10 ** (1.5 * eq['mag']) for eq in recent_eqs[-3:]) / 3
        
        if recent_3_energy < avg_energy * 0.5:
            # Fay aşırı sessizleşti, büyük bir boşalma (strain release) bekleniyor
            pred_mag = avg_mag + 0.5
        elif last_mag < avg_mag:
            pred_mag = avg_mag + 0.2 # Hafif enerji birikiyor
        else:
            pred_mag = max(avg_mag - 0.3, 1.0) # Enerji boşaldı (artçı)
            
        pred_mag = round(pred_mag, 1)
        
        # 4. 3D Tahmin Noktalarını Yerleştir
        last_eq = recent_eqs[-1]
        
        remainder = N % 3
        points_to_predict = 3 if remainder == 0 else (3 - remainder)
        
        # V3 Merkezcil Çekim (Centroid Clustering) - Son 5 depremin ağırlık merkezi
        cluster_eqs = recent_eqs[-5:]
        centroid_lat = sum(e['lat'] for e in cluster_eqs) / len(cluster_eqs)
        centroid_lon = sum(e['lon'] for e in cluster_eqs) / len(cluster_eqs)
        
        # Regresyon Projeksiyonu
        proj_lat = last_eq['lat'] + (dir_lat * step_deg)
        proj_lon = last_eq['lon'] + (dir_lon * step_deg)
        
        # P1: İleri doğru ana kırılma noktası (%70 Regresyon + %30 Kovan Merkezi)
        p1_lat = (proj_lat * 0.7) + (centroid_lat * 0.3)
        p1_lon = (proj_lon * 0.7) + (centroid_lon * 0.3)
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
        
        # Zaman hesaplaması (Sismik Fizik Mantığı: Değerlere bakarak karar ver!)
        sample = recent_eqs[-10:]
        total_gap = timedelta(0)
        
        def parse_d(d_str):
            if not d_str: return datetime.now()
            return datetime.fromisoformat(d_str.replace('Z', '+00:00') if 'Z' in d_str else d_str)

        gaps = []
        for i in range(len(sample) - 1):
            gap = parse_d(sample[i+1]['date']) - parse_d(sample[i]['date'])
            gaps.append(gap)
            total_gap += gap
            
        avg_gap = total_gap / len(gaps) if gaps else timedelta(minutes=60)
        
        base_time = parse_d(last_eq['date'])
        import datetime as dt_module
        
        # Son depremin büyüklüğüne göre enerji katsayısı
        # Eğer büyük bir depremse (enerji boşaldı), bir sonraki çok geç olur.
        # Eğer küçükse (enerji birikiyor), bir sonraki çok çabuk olur (5-10 dk).
        mag_factor = (last_eq['mag'] / 1.5) ** 2 
        
        # Supabase'e ekle
        for p in range(points_to_predict):
            current_node = ((N + p) % 3) + 1
            
            # Değerlere (büyüklüğe) dayalı dinamik gecikme!
            # Her bir sonraki nokta için (p+1), mag_factor ile şekillenen bir zaman biç.
            multiplier = p + 1
            
            # Ana kural: Küçük depremden sonra hemen patlar, büyükten sonra yatar.
            dynamic_delay = avg_gap * mag_factor * multiplier
            
            # Çok kısa süreyi (artçıları) desteklemek için, eğer enerji çok küçükse 5 dakikaya kadar inebilir.
            if dynamic_delay < dt_module.timedelta(minutes=5 * multiplier):
                dynamic_delay = dt_module.timedelta(minutes=5 * multiplier)
                
            pred_time = base_time + dynamic_delay
            
            # Zaman karşılaştırması için iki tarafın da tzinfo'sunu eşitle (AWARE vs NAIVE hatasını önle)
            current_time = dt_module.datetime.now(dt_module.timezone.utc)
            if pred_time.tzinfo is None:
                # Veritabanındaki tarihler UTC+3'e göre naive kaydediliyor
                pred_time = pred_time.replace(tzinfo=dt_module.timezone(dt_module.timedelta(hours=3)))
            
            # current_time'ı UTC+3'e çevirip karşılaştır
            current_time_local = current_time.astimezone(dt_module.timezone(dt_module.timedelta(hours=3)))
            
            if pred_time < current_time_local:
                # Sadece değerlerin (magnitude'un) belirlediği saf gecikmeyi şu ana ekle. Eski "fay kilitlenmesi" saçmalığını iptal ettik.
                pred_time = current_time_local + (dynamic_delay / 2) # Geride kalındığı için daha hızlı olması beklenir

            # Tahmin zamanını Supabase'e gönderirken Türkiye Saati (UTC+3) olduğunu belirt
            timezone = dt_module.timezone(dt_module.timedelta(hours=3))
            if pred_time.tzinfo is None:
                pred_time = pred_time.replace(tzinfo=timezone)
            
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
