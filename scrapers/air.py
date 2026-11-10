import json
import os
import sys
from datetime import datetime, timezone
import requests

sys.stdout.reconfigure(line_buffering=True)

CITIES = [
    {"city": "Dhaka", "division": "Dhaka", "lat": 23.8103, "lon": 90.4125},
    {"city": "Narayanganj", "division": "Dhaka", "lat": 23.6238, "lon": 90.5000},
    {"city": "Gazipur", "division": "Dhaka", "lat": 23.9999, "lon": 90.4203},
    {"city": "Chattogram", "division": "Chattogram", "lat": 22.3569, "lon": 91.7832},
    {"city": "Rajshahi", "division": "Rajshahi", "lat": 24.3745, "lon": 88.6042},
    {"city": "Bogura", "division": "Rajshahi", "lat": 24.8481, "lon": 89.3730},
    {"city": "Naogaon", "division": "Rajshahi", "lat": 24.7936, "lon": 88.9318},
    {"city": "Sylhet", "division": "Sylhet", "lat": 24.8949, "lon": 91.8687},
    {"city": "Khulna", "division": "Khulna", "lat": 22.8456, "lon": 89.5403},
    {"city": "Barishal", "division": "Barishal", "lat": 22.7010, "lon": 90.3535},
    {"city": "Rangpur", "division": "Rangpur", "lat": 25.7439, "lon": 89.2752},
    {"city": "Mymensingh", "division": "Mymensingh", "lat": 24.7471, "lon": 90.4203},
    {"city": "Cumilla", "division": "Chattogram", "lat": 23.4607, "lon": 91.1809}
]

def aqi_category(val):
    if val is None:
        return "Unknown"
    if val <= 50:
        return "Good"
    if val <= 100:
        return "Moderate"
    if val <= 150:
        return "Unhealthy for Sensitive Groups"
    if val <= 200:
        return "Unhealthy"
    if val <= 300:
        return "Very Unhealthy"
    return "Hazardous"

def fetch_aqi():
    rows = []
    lats = ",".join(str(c["lat"]) for c in CITIES)
    lons = ",".join(str(c["lon"]) for c in CITIES)
    url = (
        f"https://air-quality-api.open-meteo.com/v1/air-quality?"
        f"latitude={lats}&longitude={lons}"
        f"&current=us_aqi,pm2_5,pm10,carbon_monoxide,nitrogen_dioxide,ozone"
        f"&timezone=Asia%2FDhaka"
    )

    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        data = r.json()

        for idx, c in enumerate(CITIES):
            item = data[idx] if isinstance(data, list) else data
            curr = item.get("current", {})
            aqi = curr.get("us_aqi")
            rows.append({
                "city": c["city"],
                "division": c["division"],
                "us_aqi": aqi,
                "category": aqi_category(aqi),
                "pm2_5_ugm3": curr.get("pm2_5"),
                "pm10_ugm3": curr.get("pm10"),
                "no2_ugm3": curr.get("nitrogen_dioxide"),
                "o3_ugm3": curr.get("ozone")
            })
    except Exception as e:
        print(f"air quality fetch error -> {e}")

    return rows

def main():
    os.makedirs("data", exist_ok=True)
    out_path = "data/air_quality.json"

    existing = {}
    if os.path.exists(out_path):
        try:
            with open(out_path, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            existing = {}

    rows = fetch_aqi() or existing.get("cities", [])

    out = {
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "total_cities": len(rows),
        "cities": rows
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"saved air quality for {len(rows)} cities")

if __name__ == "__main__":
    main()
