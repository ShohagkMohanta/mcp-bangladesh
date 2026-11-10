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

def scrape_bb_fx():
    url = "https://www.bb.org.bd/en/index.php/econdata/rfrexrate"
    rates = []
    try:
        r = requests.get(url, headers=HEADERS, timeout=15, verify=False)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            for tr in soup.find_all("tr"):
                cols = [c.get_text(" ", strip=True) for c in tr.find_all("td")]
                if len(cols) >= 3 and re.search(r"202\d", cols[0]):
                    rates.append({
                        "date": cols[0],
                        "rate_11am_bdt": cols[1],
                        "rate_5pm_bdt": cols[2]
                    })
                    if len(rates) >= 5:
                        break
    except Exception as e:
        print(f"bb fx error -> {e}")
    return rates

def scrape_bb_inflation():
    url = "https://www.bb.org.bd/en/index.php/econdata/inflation"
    metrics = []
    try:
        r = requests.get(url, headers=HEADERS, timeout=15, verify=False)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            headers = []
            for tr in soup.find_all("tr"):
                ths = [c.get_text(" ", strip=True) for c in tr.find_all("th")]
                if len(ths) >= 3:
                    headers = ths
                tds = [c.get_text(" ", strip=True) for c in tr.find_all("td")]
                if len(tds) >= 3 and ("Point" in tds[0] or "Average" in tds[0]):
                    metrics.append({
                        "metric": tds[0],
                        "latest_month": headers[1] if len(headers) > 1 else "Latest",
                        "latest_value": tds[1],
                        "previous_month": headers[2] if len(headers) > 2 else "Previous",
                        "previous_value": tds[2]
                    })
    except Exception as e:
        print(f"bb inflation error -> {e}")
    return metrics

def scrape_tcb_bulletins():
    url = "https://tcb.gov.bd/pages/daily-rmps"
    reports = []
    try:
        r = requests.get(url, headers=HEADERS, timeout=10, verify=False)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            for tr in soup.find_all("tr"):
                cols = [c.get_text(" ", strip=True) for c in tr.find_all("td")]
                if len(cols) >= 2:
                    raw = " ".join(cols).translate(DIGIT_MAP)
                    m = re.search(r"\b(\d{1,2})[-/.](\d{1,2})[-/.](\d{2,4})\b", raw)
                    if not m:
                        continue
                    link = url
                    for a in tr.find_all("a", href=True):
                        if not a["href"].startswith("javascript"):
                            link = urljoin(url, a["href"].strip())
                            break
                    reports.append({
                        "date": m.group(0),
                        "title": "Dhaka Daily Retail Market Price Bulletin (TCB)",
                        "url": link
                    })
                    if len(reports) >= 5:
                        break
    except Exception as e:
        print(f"tcb skipped -> {e}")
    return reports

def main():
    os.makedirs("data", exist_ok=True)
    out_path = "data/economy_live.json"

    existing = {}
    if os.path.exists(out_path):
        try:
            with open(out_path, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            existing = {}

    fx = scrape_bb_fx() or existing.get("usd_bdt_reference_rates", [])
    inf = scrape_bb_inflation() or existing.get("cpi_inflation", [])
    tcb = scrape_tcb_bulletins() or existing.get("tcb_daily_price_reports", [])

    out = {
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "sources": ["Bangladesh Bank (bb.org.bd)", "Trading Corporation of Bangladesh (tcb.gov.bd)"],
        "usd_bdt_reference_rates": fx,
        "cpi_inflation": inf,
        "tcb_daily_price_reports": tcb
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"saved economy data: {len(fx)} fx rows, {len(inf)} inflation rows, {len(tcb)} tcb reports")

if __name__ == "__main__":
    main()
