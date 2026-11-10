import json
import os
import sys
from datetime import datetime, timezone
import requests

sys.stdout.reconfigure(line_buffering=True)

LOCATIONS = [
    {"district": "Dhaka", "division": "Dhaka", "lat": 23.8103, "lon": 90.4125},
    {"district": "Chattogram", "division": "Chattogram", "lat": 22.3569, "lon": 91.7832},
    {"district": "Rajshahi", "division": "Rajshahi", "lat": 24.3745, "lon": 88.6042},
    {"district": "Bogura", "division": "Rajshahi", "lat": 24.8481, "lon": 89.3730},
    {"district": "Naogaon", "division": "Rajshahi", "lat": 24.7936, "lon": 88.9318},
    {"district": "Sylhet", "division": "Sylhet", "lat": 24.8949, "lon": 91.8687},
    {"district": "Sunamganj", "division": "Sylhet", "lat": 25.0658, "lon": 91.3950},
    {"district": "Khulna", "division": "Khulna", "lat": 22.8456, "lon": 89.5403},
    {"district": "Barishal", "division": "Barishal", "lat": 22.7010, "lon": 90.3535},
    {"district": "Rangpur", "division": "Rangpur", "lat": 25.7439, "lon": 89.2752},
    {"district": "Kurigram", "division": "Rangpur", "lat": 25.8054, "lon": 89.6362},
    {"district": "Mymensingh", "division": "Mymensingh", "lat": 24.7471, "lon": 90.4203},
    {"district": "Cumilla", "division": "Chattogram", "lat": 23.4607, "lon": 91.1809},
    {"district": "Feni", "division": "Chattogram", "lat": 23.0159, "lon": 91.3976},
    {"district": "Cox's Bazar", "division": "Chattogram", "lat": 21.4272, "lon": 92.0058}
]

def fetch_weather():
    results = []
    lats = ",".join(str(loc["lat"]) for loc in LOCATIONS)
    lons = ",".join(str(loc["lon"]) for loc in LOCATIONS)

    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lats}&longitude={lons}"
        f"&current=temperature_2m,relative_humidity_2m,precipitation,rain,wind_speed_10m"
        f"&daily=precipitation_sum,temperature_2m_max,temperature_2m_min"
        f"&timezone=Asia%2FDhaka&forecast_days=1"
    )

    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        payload = r.json()

        for idx, loc in enumerate(LOCATIONS):
            item = payload[idx] if isinstance(payload, list) else payload
            curr = item.get("current", {})
            daily = item.get("daily", {})

            results.append({
                "district": loc["district"],
                "division": loc["division"],
                "temp_c": curr.get("temperature_2m"),
                "humidity_pct": curr.get("relative_humidity_2m"),
                "current_rain_mm": curr.get("rain"),
                "wind_kmh": curr.get("wind_speed_10m"),
                "today_max_c": (daily.get("temperature_2m_max") or [None])[0],
                "today_min_c": (daily.get("temperature_2m_min") or [None])[0],
                "today_rain_sum_mm": (daily.get("precipitation_sum") or [None])[0]
            })
    except Exception as e:
        print(f"weather fetch error -> {e}")

    return results

def main():
    os.makedirs("data", exist_ok=True)
    out_path = "data/weather_live.json"

    existing = {}
    if os.path.exists(out_path):
        try:
            with open(out_path, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            existing = {}

    records = fetch_weather() or existing.get("districts", [])

    out = {
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "total_districts": len(records),
        "districts": records
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"saved weather for {len(records)} districts")

if __name__ == "__main__":
    main()
