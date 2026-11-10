import json
import os
import re
import sys
from datetime import datetime, timezone
from urllib.parse import urljoin
import requests
import urllib3
from bs4 import BeautifulSoup

sys.stdout.reconfigure(line_buffering=True)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

DIGIT_MAP = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")

AGENCIES = [
    {"code": "DSHE", "name": "Directorate of Secondary & Higher Education", "url": "https://dshe.gov.bd/pages/notices"},
    {"code": "SHED", "name": "Ministry of Education (SHED)", "url": "https://shed.gov.bd/pages/notices"},
    {"code": "MOF", "name": "Ministry of Finance", "url": "https://mof.gov.bd/pages/notices"},
    {"code": "BPSC", "name": "Bangladesh Public Service Commission", "url": "https://bpsc.gov.bd/pages/notices"},
    {"code": "PLANDIV", "name": "Planning Division", "url": "https://plandiv.gov.bd/pages/notices"},
    {"code": "DPE", "name": "Directorate of Primary Education", "url": "https://dpe.gov.bd/pages/notices"}
]

def clean_date(text):
    if not text:
        return ""
    norm = text.translate(DIGIT_MAP)
    m = re.search(r"\b(?:\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4}|\d{4}[-/.]\d{1,2}[-/.]\d{1,2})\b", norm)
    return m.group(0) if m else ""

def fetch_agency_notices(agency):
    items = []
    try:
        r = requests.get(agency["url"], headers=HEADERS, timeout=15, verify=False)
        if r.status_code != 200:
            print(f"{agency['code']} returned status {r.status_code}")
            return items

        soup = BeautifulSoup(r.text, "html.parser")
        for tr in soup.find_all("tr"):
            cols = [c.get_text(" ", strip=True) for c in tr.find_all(["td", "th"])]
            if len(cols) < 2:
                continue

            row_text = " ".join(cols)
            pub_date = clean_date(row_text)
            if not pub_date:
                continue

            title_candidates = [
                c for c in cols
                if len(c) > 12 and c not in ["দেখুন", "ডাউনলোড", "কার্যকলাপ", "প্রকাশের তারিখ"]
            ]
            title = max(title_candidates, key=len) if title_candidates else cols[1]
            title = re.sub(r"\s+", " ", title).strip()

            link = agency["url"]
            for a in tr.find_all("a", href=True):
                href = a["href"].strip()
                if href and not href.startswith("javascript"):
                    link = urljoin(agency["url"], href)
                    break

            items.append({
                "agency_code": agency["code"],
                "agency_name": agency["name"],
                "title": title[:220],
                "published_date": pub_date,
                "url": link
            })
            if len(items) >= 8:
                break
    except Exception as e:
        print(f"error scraping {agency['code']} -> {e}")

    return items

def main():
    os.makedirs("data", exist_ok=True)
    out_path = "data/gov_notices.json"

    prev_by_agency = {}
    if os.path.exists(out_path):
        try:
            with open(out_path, "r", encoding="utf-8") as f:
                old_data = json.load(f)
                for n in old_data.get("notices", []):
                    code = n.get("agency_code")
                    if code:
                        prev_by_agency.setdefault(code, []).append(n)
        except Exception:
            prev_by_agency = {}

    all_notices = []
    for ag in AGENCIES:
        code = ag["code"]
        found = fetch_agency_notices(ag)
        if found:
            print(f"{code}: fetched {len(found)} notices")
            all_notices.extend(found)
        elif code in prev_by_agency:
            print(f"{code}: keeping {len(prev_by_agency[code])} previous notices")
            all_notices.extend(prev_by_agency[code])

    out = {
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "total_agencies": len(AGENCIES),
        "total_notices": len(all_notices),
        "notices": all_notices
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"saved {len(all_notices)} government notices total")

if __name__ == "__main__":
    main()
