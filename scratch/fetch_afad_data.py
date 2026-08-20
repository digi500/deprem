import requests
import json
import time

def fetch_data():
    url = "https://deprem.afad.gov.tr/apiv2/event/filter"
    params = {
        "start": "2010-01-01T00:00:00",
        "end": "2026-12-31T23:59:59",
        "minlat": "40.5",
        "maxlat": "41.0",
        "minlon": "28.5",
        "maxlon": "29.5"
    }
    
    print(f"Fetching AFAD data from {params['start']} to {params['end']}...")
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        data = response.json()
        print(f"Başarıyla {len(data)} deprem çekildi.")
        
        # Sort by date (ascending)
        data.sort(key=lambda x: x['date'])
        
        with open('c:\\deprem\\scratch\\afad_dataset.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("Veri 'scratch/afad_dataset.json' dosyasına kaydedildi.")
    else:
        print(f"Hata oluştu! Status Code: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    fetch_data()
