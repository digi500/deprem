import urllib.request
import re
import json
from datetime import datetime, timedelta

def fetch_kandilli_data():
    url = "http://www.koeri.boun.edu.tr/scripts/lst4.asp"
    try:
        response = urllib.request.urlopen(url)
        # Handle Turkish characters properly
        html = response.read().decode('windows-1254')
        return html
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

def parse_data(html_content):
    # Find the pre tag content where the data is
    match = re.search(r'<pre>(.*?)</pre>', html_content, re.DOTALL | re.IGNORECASE)
    if not match:
        return []
    
    data_text = match.group(1)
    lines = data_text.strip().split('\n')
    
    earthquakes = []
    # Skip header lines (usually around 6-7 lines)
    start_parsing = False
    for line in lines:
        if "----------" in line:
            start_parsing = True
            continue
        if not start_parsing:
            continue
            
        parts = line.split()
        if len(parts) >= 8:
            date_str = parts[0]
            time_str = parts[1]
            try:
                lat = float(parts[2])
                lon = float(parts[3])
                depth = float(parts[4])
                mag = float(parts[6]) # ML magnitude
                
                # Reconstruct location string
                loc_start = 8 if parts[7] == '-.-' else 8
                location = " ".join(parts[loc_start:-1]).replace("İlksel", "").strip()
                
                # Parse date
                eq_date = datetime.strptime(f"{date_str} {time_str}", "%Y.%m.%d %H:%M:%S")
                
                earthquakes.append({
                    "date": eq_date.isoformat(),
                    "lat": lat,
                    "lon": lon,
                    "depth": depth,
                    "mag": mag,
                    "location": location
                })
            except ValueError:
                continue
                
    return earthquakes

def main():
    html = fetch_kandilli_data()
    if not html:
        return
        
    earthquakes = parse_data(html)
    
    # Filter for last 3 days
    now = datetime.now()
    three_days_ago = now - timedelta(days=3)
    
    recent_eqs = [eq for eq in earthquakes if datetime.fromisoformat(eq["date"]) >= three_days_ago]
    
    # Filter for Marmara / Adalar region (approximate bounding box)
    # Marmara Sea general: Lat 40.2 to 41.1, Lon 27.0 to 30.0
    # Adalar specific: Lat 40.8 to 40.95, Lon 28.9 to 29.2
    
    marmara_eqs = []
    for eq in recent_eqs:
        # Broad Marmara filter for now to ensure we have data, we can narrow down if needed
        if 40.2 <= eq["lat"] <= 41.1 and 27.0 <= eq["lon"] <= 30.0:
            marmara_eqs.append(eq)
            
    print(f"Total parsed: {len(earthquakes)}")
    print(f"Recent (3 days): {len(recent_eqs)}")
    print(f"Marmara (3 days): {len(marmara_eqs)}")
    
    with open("earthquakes.json", "w", encoding="utf-8") as f:
        json.dump(marmara_eqs, f, indent=2, ensure_ascii=False)
        
if __name__ == "__main__":
    main()
