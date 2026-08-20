import requests
import csv
import os

SUPABASE_URL = "https://tiykapksaboucamusmbk.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRpeWthcGtzYWJvdWNhbXVzbWJrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODcxNjUyMjEsImV4cCI6MjEwMjc0MTIyMX0.D2YkQaF5Gfn49bsRpuoi3W1upoFfhGxdFQ-pBRW6IAM"

headers = {
    "apikey": SUPABASE_ANON_KEY,
    "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
    "Content-Type": "application/json",
    "Prefer": "count=exact"
}

def export_data():
    all_data = []
    offset = 0
    limit = 1000
    
    while True:
        headers["Range"] = f"{offset}-{offset + limit - 1}"
        response = requests.get(f"{SUPABASE_URL}/rest/v1/earthquakes?select=*", headers=headers)
        
        if response.status_code != 200:
            print(f"Error fetching data: {response.text}")
            break
            
        data = response.json()
        if not data:
            break
            
        all_data.extend(data)
        if len(data) < limit:
            break
            
        offset += limit

    print(f"Total records fetched: {len(all_data)}")
    
    if all_data:
        csv_file = r"c:\deprem\gecmis_depremler.csv"
        # Extract headers from the first record
        keys = ["id", "date", "lat", "lon", "depth", "mag", "location"]
        
        with open(csv_file, mode="w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(all_data)
        
        print(f"Successfully saved to {csv_file}")

if __name__ == "__main__":
    export_data()
