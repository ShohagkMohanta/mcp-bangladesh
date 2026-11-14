import json
import os
import re
import sys
from datetime import datetime, timezone
import requests
import urllib3
from bs4 import BeautifulSoup

sys.stdout.reconfigure(line_buffering=True)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

def scrape_bpdb_generation():
    url = "https://misc.bpdb.gov.bd/daily-generation"
    plants = []
    try:
        r = requests.get(url, headers=HEADERS, timeout=15, verify=False)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            for tr in soup.find_all("tr"):
                cols = [c.get_text(" ", strip=True) for c in tr.find_all("td")]
                if len(cols) >= 5 and re.match(r"^\d+\.?$", cols[0]):
                    name = cols[1]
                    nums = []
                    for c in cols[2:]:
                        m = re.search(r"^\d+(\.\d+)?$", c.strip())
                        if m:
                            nums.append(float(m.group(0)))
                    if name and len(nums) >= 2:
                        plants.append({
                            "serial": int(cols[0].replace(".", "")),
                            "plant_name": name,
                            "installed_or_derated_mw": nums[0],
                            "day_peak_mw": nums[1] if len(nums) > 1 else 0,
                            "evening_peak_mw": nums[2] if len(nums) > 2 else nums[-1]
                        })
    except Exception as e:
        print(f"bpdb scrape error -> {e}")

    return plants

def main():
    os.makedirs("data", exist_ok=True)
    out_path = "data/power_grid.json"

    existing = {}
    if os.path.exists(out_path):
        try:
            with open(out_path, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            existing = {}

    plants = scrape_bpdb_generation() or existing.get("plants", [])

    total_day = round(sum(p.get("day_peak_mw", 0) for p in plants), 1)
    total_eve = round(sum(p.get("evening_peak_mw", 0) for p in plants), 1)

    out = {
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "source": "Bangladesh Power Development Board (BPDB)",
        "sampled_plants_count": len(plants),
        "sampled_day_peak_mw": total_day,
        "sampled_evening_peak_mw": total_eve,
        "plants": plants
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"saved bpdb power data for {len(plants)} power plants")

if __name__ == "__main__":
    main()
