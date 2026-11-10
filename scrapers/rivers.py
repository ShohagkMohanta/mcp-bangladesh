import json
import os
import sys
from datetime import datetime, timezone
import requests
import urllib3

sys.stdout.reconfigure(line_buffering=True)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://ffwc.gov.bd",
    "Referer": "https://ffwc.gov.bd/"
}

BASELINE_STATIONS = [
    {"river": "Jamuna", "station": "Aricha", "basin": "Brahmaputra", "district": "Manikganj", "danger_level_m": 8.95, "water_level_m": 4.18},
    {"river": "Jamuneswari", "station": "Badarganj", "basin": "Brahmaputra", "district": "Rangpur", "danger_level_m": 31.70, "water_level_m": 27.35},
    {"river": "Karatoa-Atrai-GGH", "station": "Baghabari", "basin": "Brahmaputra", "district": "Sirajganj", "danger_level_m": 9.95, "water_level_m": 5.31},
    {"river": "Jamuna", "station": "Bahadurabad", "basin": "Brahmaputra", "district": "Jamalpur", "danger_level_m": 19.05, "water_level_m": 14.05},
    {"river": "Nil Jinjiram", "station": "Boalmari", "basin": "Brahmaputra", "district": "Kurigram", "danger_level_m": 23.90, "water_level_m": 21.58},
    {"river": "Karatoa", "station": "Bogra", "basin": "Brahmaputra", "district": "Bogura", "danger_level_m": 15.85, "water_level_m": 10.50},
    {"river": "Brahmaputra", "station": "Chilmari", "basin": "Brahmaputra", "district": "Kurigram", "danger_level_m": 23.25, "water_level_m": 18.69},
    {"river": "Teesta", "station": "Dalia", "basin": "Brahmaputra", "district": "Nilphamari", "danger_level_m": 52.15, "water_level_m": 50.77},
    {"river": "Balu", "station": "Demra", "basin": "Brahmaputra", "district": "Dhaka", "danger_level_m": 5.30, "water_level_m": 1.33},
    {"river": "Buriganga", "station": "Dhaka", "basin": "Brahmaputra", "district": "Dhaka", "danger_level_m": 5.55, "water_level_m": 1.40},
    {"river": "Dhaleswari", "station": "Elasinghat", "basin": "Brahmaputra", "district": "Tangail", "danger_level_m": 10.95, "water_level_m": 4.83},
    {"river": "Jamuna", "station": "Fulchari", "basin": "Brahmaputra", "district": "Gaibandha", "danger_level_m": 19.35, "water_level_m": 13.89},
    {"river": "Ghagot", "station": "Gaibandha", "basin": "Brahmaputra", "district": "Gaibandha", "danger_level_m": 21.25, "water_level_m": 16.14},
    {"river": "Teesta", "station": "Haripur", "basin": "Brahmaputra", "district": "Gaibandha", "danger_level_m": 22.30, "water_level_m": 18.85},
    {"river": "Jamuna", "station": "Jagannathganj", "basin": "Brahmaputra", "district": "Jamalpur", "danger_level_m": 13.55, "water_level_m": 8.54},
    {"river": "Old Brahmaputra", "station": "Jamalpur", "basin": "Brahmaputra", "district": "Jamalpur", "danger_level_m": 16.55, "water_level_m": 8.44},
    {"river": "Turag", "station": "Kaliakoir", "basin": "Brahmaputra", "district": "Gazipur", "danger_level_m": 7.95, "water_level_m": 3.67},
    {"river": "Brahmaputra", "station": "Kamarjani", "basin": "Brahmaputra", "district": "Gaibandha", "danger_level_m": 21.70, "water_level_m": 17.20},
    {"river": "Dharla", "station": "Kurigram", "basin": "Brahmaputra", "district": "Kurigram", "danger_level_m": 26.05, "water_level_m": 21.92},
    {"river": "Teesta", "station": "Kaunia", "basin": "Brahmaputra", "district": "Rangpur", "danger_level_m": 29.30, "water_level_m": 27.10},
    {"river": "Bangali", "station": "Shimulbari", "basin": "Brahmaputra", "district": "Bogura", "danger_level_m": 17.75, "water_level_m": 11.58},
    {"river": "Jamuna", "station": "Sariakandi", "basin": "Brahmaputra", "district": "Bogura", "danger_level_m": 16.25, "water_level_m": 10.41},
    {"river": "Jamuna", "station": "Serajganj", "basin": "Brahmaputra", "district": "Sirajganj", "danger_level_m": 12.90, "water_level_m": 7.41},
    {"river": "Jamuna", "station": "Porabari", "basin": "Brahmaputra", "district": "Tangail", "danger_level_m": 11.80, "water_level_m": 6.74},
    {"river": "Upper Karatoa", "station": "Panchagarh", "basin": "Brahmaputra", "district": "Panchagarh", "danger_level_m": 70.30, "water_level_m": 64.09},
    {"river": "Atrai", "station": "Mohadebpur", "basin": "Ganges", "district": "Naogaon", "danger_level_m": 18.15, "water_level_m": 12.43},
    {"river": "Atrai", "station": "Singra", "basin": "Brahmaputra", "district": "Natore", "danger_level_m": 12.20, "water_level_m": 8.39},
    {"river": "Old Brahmaputra", "station": "Mymensingh", "basin": "Brahmaputra", "district": "Mymensingh", "danger_level_m": 12.05, "water_level_m": 2.36},
    {"river": "Padma", "station": "Goalundo", "basin": "Ganges", "district": "Rajbari", "danger_level_m": 8.20, "water_level_m": 4.15},
    {"river": "Padma", "station": "Bhagyakul", "basin": "Ganges", "district": "Munshiganj", "danger_level_m": 5.85, "water_level_m": 2.80},
    {"river": "Padma", "station": "Mawa", "basin": "Ganges", "district": "Munshiganj", "danger_level_m": 5.65, "water_level_m": 2.65},
    {"river": "Ganges", "station": "Pankha", "basin": "Ganges", "district": "Chapainawabganj", "danger_level_m": 22.05, "water_level_m": 14.10},
    {"river": "Ganges", "station": "Rajshahi", "basin": "Ganges", "district": "Rajshahi", "danger_level_m": 18.05, "water_level_m": 10.95},
    {"river": "Ganges", "station": "Hardinge Bridge", "basin": "Ganges", "district": "Pabna", "danger_level_m": 13.80, "water_level_m": 8.40},
    {"river": "Surma", "station": "Kanaighat", "basin": "Meghna", "district": "Sylhet", "danger_level_m": 12.75, "water_level_m": 7.85},
    {"river": "Surma", "station": "Sylhet", "basin": "Meghna", "district": "Sylhet", "danger_level_m": 10.80, "water_level_m": 5.40},
    {"river": "Surma", "station": "Sunamganj", "basin": "Meghna", "district": "Sunamganj", "danger_level_m": 7.80, "water_level_m": 4.90},
    {"river": "Kushiyara", "station": "Amalshid", "basin": "Meghna", "district": "Sylhet", "danger_level_m": 15.40, "water_level_m": 9.60},
    {"river": "Kushiyara", "station": "Sheola", "basin": "Meghna", "district": "Beanibazar", "danger_level_m": 13.05, "water_level_m": 8.15},
    {"river": "Manu", "station": "Moulvibazar", "basin": "Meghna", "district": "Moulvibazar", "danger_level_m": 11.30, "water_level_m": 6.80},
    {"river": "Khowai", "station": "Habiganj", "basin": "Meghna", "district": "Habiganj", "danger_level_m": 9.05, "water_level_m": 5.90},
    {"river": "Gumti", "station": "Comilla", "basin": "Meghna", "district": "Cumilla", "danger_level_m": 11.30, "water_level_m": 7.10},
    {"river": "Muhuri", "station": "Parshuram", "basin": "South Eastern Hill", "district": "Feni", "danger_level_m": 12.55, "water_level_m": 9.20},
    {"river": "Halda", "station": "Narayanhat", "basin": "South Eastern Hill", "district": "Chattogram", "danger_level_m": 14.80, "water_level_m": 10.40}
]

def get_ffwc_data():
    api_endpoints = [
        "https://api.ffwc.gov.bd/data_load/modified-observed/",
        "https://api.ffwc.gov.bd/data_load/stations/"
    ]

    for url in api_endpoints:
        try:
            r = requests.get(url, headers=HEADERS, timeout=8, verify=False)
            if r.status_code == 200 and r.text.strip().startswith("["):
                raw = r.json()
                if len(raw) > 0:
                    print(f"fetched {len(raw)} live records from {url}")
                    return raw
        except Exception as e:
            print(f"ffwc endpoint {url} skipped -> {e}")

    return []

def build_baseline():
    stations = []
    for s in BASELINE_STATIONS:
        item = dict(s)
        dl = item["danger_level_m"]
        wl = item["water_level_m"]
        item["margin_m"] = round(dl - wl, 2)
        item["status"] = "ABOVE_DANGER" if wl >= dl else ("WARNING" if (dl - wl) <= 0.5 else "NORMAL")
        stations.append(item)
    return stations

def main():
    os.makedirs("data", exist_ok=True)
    out_path = "data/rivers_live.json"

    existing = {}
    if os.path.exists(out_path):
        try:
            with open(out_path, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            existing = {}

    data = get_ffwc_data() or existing.get("stations", []) or build_baseline()

    out = {
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "source": "FFWC / BWDB",
        "total_stations": len(data),
        "stations": data
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"saved {len(data)} river station records")

if __name__ == "__main__":
    main()
