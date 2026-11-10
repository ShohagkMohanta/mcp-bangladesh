import json
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse
import pdfplumber
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import urllib3
from bs4 import BeautifulSoup

sys.stdout.reconfigure(line_buffering=True)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

ROOT_URL = "https://dghs.gov.bd"

DENGUE_INDEX_URLS = [
    "https://dghs.gov.bd/pages/miscellaneous-infos?filters=%7B%22miscellaneous_info_type%22%3A%226a9cf0471fa8cd87d1f50227%22%7D",
    "https://dghs.gov.bd/views/latest-news?page=1&page_size=10",
]

MEASLES_INDEX_URLS = [
    "https://dghs.gov.bd/pages/press-releases",
    "https://dghs.gov.bd/views/latest-news?page=1&page_size=10",
]

DENGUE_DIV_ORDER = [
    "Dhaka", "Mymensingh", "Chattogram", "Khulna",
    "Rajshahi", "Rangpur", "Barishal", "Sylhet"
]

MEASLES_DIV_ORDER = [
    "Dhaka", "Sylhet", "Chattogram", "Rajshahi",
    "Mymensingh", "Barishal", "Khulna", "Rangpur"
]

DIGIT_TRANS = str.maketrans(
    "০১২৩৪৫৬৭৮৯०१२३४५६७८९٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹",
    "0123456789012345678901234567890123456789",
)

IGNORE_URLS = [
    "new_acr", "csc.dghs", "286d104ce01942429e716d6f9c425cdf",
    "/2024/12/", "old.dghs.gov.bd", "2016_11_2015", "guide%20book"
]

YEAR_NUMS = {datetime.now(timezone.utc).year, datetime.now(timezone.utc).year - 1}

DISTRICT_SERIALS = {
    1: ("Dhaka", "Dhaka"), 2: ("Faridpur", "Dhaka"), 3: ("Faridpur", "Dhaka"),
    4: ("Gazipur", "Dhaka"), 5: ("Gazipur", "Dhaka"), 6: ("Gopalganj", "Dhaka"),
    7: ("Kishoreganj", "Dhaka"), 8: ("Kishoreganj", "Dhaka"), 9: ("Madaripur", "Dhaka"),
    10: ("Manikganj", "Dhaka"), 11: ("Manikganj", "Dhaka"), 12: ("Munshiganj", "Dhaka"),
    13: ("Narayanganj", "Dhaka"), 14: ("Narsingdi", "Dhaka"), 15: ("Rajbari", "Dhaka"),
    16: ("Shariatpur", "Dhaka"), 17: ("Tangail", "Dhaka"), 18: ("Tangail", "Dhaka"),
    19: ("Mymensingh", "Mymensingh"), 20: ("Jamalpur", "Mymensingh"),
    21: ("Sherpur", "Mymensingh"), 22: ("Netrokona", "Mymensingh"),
    24: ("Chattogram", "Chattogram"), 35: ("Chattogram", "Chattogram"),
    25: ("Cox's Bazar", "Chattogram"), 26: ("Rangamati", "Chattogram"),
    27: ("Khagrachhari", "Chattogram"), 28: ("Bandarban", "Chattogram"),
    29: ("Feni", "Chattogram"), 33: ("Noakhali", "Chattogram"),
    30: ("Cumilla", "Chattogram"), 36: ("Cumilla", "Chattogram"),
    31: ("Chandpur", "Chattogram"), 32: ("Lakshmipur", "Chattogram"),
    34: ("Brahmanbaria", "Chattogram"), 37: ("Khulna", "Khulna"),
    38: ("Bagerhat", "Khulna"), 39: ("Satkhira", "Khulna"), 40: ("Jashore", "Khulna"),
    41: ("Jhenaidah", "Khulna"), 42: ("Magura", "Khulna"), 43: ("Narail", "Khulna"),
    44: ("Kushtia", "Khulna"), 45: ("Chuadanga", "Khulna"), 46: ("Meherpur", "Khulna"),
    48: ("Rajshahi", "Rajshahi"), 49: ("Chapainawabganj", "Rajshahi"),
    50: ("Naogaon", "Rajshahi"), 51: ("Natore", "Rajshahi"), 52: ("Joypurhat", "Rajshahi"),
    53: ("Bogura", "Rajshahi"), 54: ("Sirajganj", "Rajshahi"), 55: ("Pabna", "Rajshahi"),
    59: ("Rangpur", "Rangpur"), 60: ("Lalmonirhat", "Rangpur"), 61: ("Kurigram", "Rangpur"),
    62: ("Nilphamari", "Rangpur"), 63: ("Dinajpur", "Rangpur"), 64: ("Gaibandha", "Rangpur"),
    65: ("Thakurgaon", "Rangpur"), 66: ("Panchagarh", "Rangpur"),
    69: ("Barishal", "Barishal"), 70: ("Patuakhali", "Barishal"), 71: ("Patuakhali", "Barishal"),
    72: ("Bhola", "Barishal"), 73: ("Pirojpur", "Barishal"), 74: ("Barguna", "Barishal"),
    75: ("Jhalokati", "Barishal"), 77: ("Sylhet", "Sylhet"), 78: ("Sunamganj", "Sylhet"),
    79: ("Habiganj", "Sylhet"), 80: ("Moulvibazar", "Sylhet")
}

def get_http_client():
    s = requests.Session()
    s.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    })
    retry = Retry(
        total=2, connect=2, read=2, backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"]
    )
    adapter = HTTPAdapter(max_retries=retry)
    s.mount("https://", adapter)
    s.mount("http://", adapter)
    return s

CLIENT = get_http_client()

def clean_bn(text):
    if not text:
        return ""
    s = str(text)
    s = s.replace("\u09ac\u09bc", "র").replace("\u09af\u09bc", "য়")
    s = s.replace("\u09a1\u09bc", "ড়").replace("\u09a2\u09bc", "ঢ়")
    s = s.replace("\u200c", "").replace("\u200d", "").replace("\ufeff", "")
    return re.sub(r"\s+", " ", s).strip()

def bn_consonants(text):
    if not text:
        return ""
    s = clean_bn(text)
    s = s.replace("ড়", "ড").replace("ঢ়", "ঢ").replace("য়", "য")
    s = s.replace("ণ", "ন").replace("ষ", "স").replace("শ", "স")
    s = s.replace("ৎ", "ত").replace("ং", "ঙ").replace("ঈ", "ই").replace("ঊ", "উ")
    stripped = re.sub(r"[^অ-ঔক-হ]", "", s)
    return re.sub(r"(.)\1+", r"\1", stripped)

def parse_date_str(text):
    if not text:
        return ""
    norm = clean_bn(text).translate(DIGIT_TRANS)
    for d_s, m_s, y_s in re.findall(r"\b(\d{1,2})[-/.](\d{1,2})[-/.](\d{2,4})\b", norm):
        d, m, y = int(d_s), int(m_s), int(y_s)
        if d == 1 and m == 1:
            continue
        if 1 <= d <= 31 and 1 <= m <= 12:
            return f"{d:02d}/{m:02d}/{y % 100:02d}"
    return ""

def parse_int_list(text):
    if not text:
        return []
    norm = clean_bn(text).translate(DIGIT_TRANS)
    norm = norm.replace("O", "0").replace("o", "0").replace("।", "")
    norm = re.sub(r"(\d)\s*[,]\s*(\d)", r"\1\2", norm)
    norm = re.sub(r"(\d)\s*-\s*(\d)", r"\1\2", norm)
    return [int(n) for n in re.findall(r"\d+", norm)]

def is_summary_row(text):
    if not text:
        return False
    norm = clean_bn(text[:45])
    cons = bn_consonants(norm)
    if any(k in cons for k in ["সরবমট", "সবরমট", "বভগরমট", "বভগরসরবমট", "জলরমট"]):
        return True
    first = norm.split()[0] if norm.split() else ""
    return bn_consonants(first) in ("মট", "সরবমট", "সবরমট") or "মোট" in first or "েমাট" in first

def match_division(text):
    if not text or is_summary_row(text):
        return None
    cons = bn_consonants(text[:60])
    if any(k in cons for k in ["লকসমতর", "সটকরপরসন"]):
        return None
    if "ঢক" in cons:
        return "Dhaka"
    if "সলট" in cons or "লট" in cons:
        return "Sylhet"
    if "চটগরম" in cons or "চটগ" in cons:
        return "Chattogram"
    if "রজসহ" in cons or "জসহ" in cons or "রজস" in cons:
        return "Rajshahi"
    if "মযমনসঙহ" in cons or "মযমন" in cons or "সঙহ" in cons:
        return "Mymensingh"
    if "বরসল" in cons or "রসল" in cons or "বসল" in cons or "বরল" in cons:
        return "Barishal"
    if "খলন" in cons:
        return "Khulna"
    if "রঙপর" in cons or "ঙপর" in cons or "ঙপ" in cons or "রঙপ" in cons:
        return "Rangpur"
    return None

def valid_link(href):
    if not href or "javascript" in href.lower() or href.strip() == "#":
        return False
    if any(b in href.lower() for b in IGNORE_URLS):
        return False
    path = urlparse(href).path.rstrip("/")
    if any(p in path for p in ["/pages/press-releases/", "/pages/news/", "/pages/miscellaneous-infos/"]):
        return True
    return path.lower().endswith(".pdf")

def download_pdf_bytes(url):
    if not url or any(b in url.lower() for b in IGNORE_URLS):
        return None
    try:
        r = requests.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Connection": "close"
            },
            timeout=(10, 25),
            verify=False
        )
        if r.status_code == 200 and r.content.startswith(b"%PDF"):
            return r.content
    except Exception as e:
        print(f"pdf fetch skipped on {url} -> {e}")
    return None

def extract_pdf_links(html, base):
    links = []
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.find_all(["iframe", "embed", "object", "a"]):
        ref = tag.get("src") or tag.get("href") or tag.get("data")
        if ref and ".pdf" in ref.lower():
            full = urljoin(base, ref.strip())
            if full not in links:
                links.append(full)
    for m in re.findall(r'https?://[^\s"\'<>\\]+\.pdf', html, flags=re.IGNORECASE):
        if m not in links:
            links.append(m)
    return links

def resolve_detail_pdf(url, skip_pdfs, default_date):
    try:
        if url.lower().endswith(".pdf"):
            raw = download_pdf_bytes(url)
            return (url, default_date, raw) if raw else (None, "", None)
        r = CLIENT.get(url, timeout=15, verify=False)
        if r.status_code != 200:
            return (None, "", None)
        r_date = default_date or parse_date_str(r.text)
        found = [
            u for u in extract_pdf_links(r.text, ROOT_URL)
            if u.lower() not in skip_pdfs and not any(b in u.lower() for b in IGNORE_URLS)
        ]
        recent = [u for u in found if any(f"/{yr}/" in u for yr in YEAR_NUMS)]
        for candidate in recent + [u for u in found if u not in recent]:
            raw = download_pdf_bytes(candidate)
            if raw:
                return (candidate, r_date, raw)
    except Exception as e:
        print(f"detail lookup error -> {e}")
    return (None, "", None)

def find_latest_bulletin(index_urls, terms):
    for idx_url in index_urls:
        try:
            r = CLIENT.get(idx_url, timeout=15, verify=False)
            if r.status_code != 200:
                continue
            soup = BeautifulSoup(r.text, "html.parser")
            nav_pdfs = set()
            for nav in soup.find_all(["header", "nav", "footer"]):
                for a in nav.find_all("a", href=True):
                    if ".pdf" in a["href"].lower():
                        nav_pdfs.add(urljoin(ROOT_URL, a["href"].strip()).lower())

            seen = set()
            for tr in soup.find_all("tr"):
                txt = tr.get_text(" ", strip=True)
                if not any(t in txt.lower() for t in terms):
                    continue
                r_date = parse_date_str(txt)
                pdfs, details = [], []
                for a in tr.find_all("a", href=True):
                    href = a["href"].strip()
                    if ".pdf" in href.lower() and not any(b in href.lower() for b in IGNORE_URLS):
                        full = urljoin(ROOT_URL, href)
                        if full not in pdfs:
                            pdfs.append(full)
                    elif valid_link(href):
                        full = urljoin(ROOT_URL, href)
                        if full not in details:
                            details.append(full)
                for p in pdfs:
                    raw = download_pdf_bytes(p)
                    if raw:
                        return (p, r_date, raw)
                for d in details:
                    seen.add(d)
                    p_url, p_date, raw = resolve_detail_pdf(d, nav_pdfs, r_date)
                    if p_url and raw:
                        return (p_url, p_date, raw)

            for a in soup.find_all("a", href=True):
                txt = a.get_text(" ", strip=True)
                href = a["href"].strip()
                if not any(t in txt.lower() or t in href.lower() for t in terms):
                    continue
                if not valid_link(href):
                    continue
                full = urljoin(ROOT_URL, href)
                if full in seen:
                    continue
                seen.add(full)
                r_date = parse_date_str(txt) or parse_date_str(href)
                p_url, p_date, raw = resolve_detail_pdf(full, nav_pdfs, r_date)
                if p_url and raw:
                    return (p_url, p_date, raw)
        except Exception as e:
            print(f"index scan error on {idx_url} -> {e}")
    return (None, "", None)

def group_words_by_line(page, tol=4.2):
    words = page.extract_words()
    if not words:
        return []
    ordered = sorted(words, key=lambda w: (w["top"] + w["bottom"]) / 2.0)
    lines = []
    for w in ordered:
        ymid = (w["top"] + w["bottom"]) / 2.0
        matched = False
        for line in lines:
            if abs(ymid - line["y"]) <= tol:
                line["words"].append(w)
                line["y"] = sum((i["top"] + i["bottom"]) / 2.0 for i in line["words"]) / len(line["words"])
                matched = True
                break
        if not matched:
            lines.append({"y": ymid, "words": [w]})
    lines.sort(key=lambda l: l["y"])
    return [sorted(l["words"], key=lambda i: i["x0"]) for l in lines]

def split_line_tokens(words, width):
    left = [w for w in words if w["x0"] < width * 0.19]
    s_nums = parse_int_list(" ".join(w["text"] for w in left))
    serial = s_nums[0] if (s_nums and 1 <= s_nums[0] <= 85) else None

    bn_words = [
        w for w in words
        if w["x0"] < width * 0.62 and re.search(r"[অ-হড়ঢ়য়]", clean_bn(w["text"]))
    ]
    label = clean_bn(" ".join(w["text"] for w in bn_words)) if bn_words else ""

    max_x1 = max((w["x1"] for w in bn_words), default=width * 0.35)
    split_x = max(max_x1 - 2.0, width * 0.36)
    nums = parse_int_list(" ".join(w["text"] for w in words if w["x0"] >= split_x))
    return (serial, label, nums)

def unpack_dengue_nums(nums):
    if not nums or len(nums) < 2:
        return None
    total_adm = max(nums)
    if total_adm == 0 or total_adm > 500000:
        return None
    idx = nums.index(total_adm)
    before = nums[:idx]
    after = nums[idx + 1:]
    new_24h = max(before) if before else 0

    if not after:
        deaths, active = 0, 0
    elif len(after) >= 3:
        deaths, active = after[0], after[-1]
    elif len(after) == 2:
        a, b = after[0], after[1]
        if a < b and b >= total_adm * 0.5:
            deaths = a
            active = max(0, total_adm - a - b)
        else:
            deaths = max(0, total_adm - a - b) if abs((a + b) - total_adm) <= 25 else 0
            active = b
    else:
        a = after[0]
        deaths = 0
        active = max(0, total_adm - a) if a >= total_adm * 0.5 else a

    return {
        "new_cases_24h": new_24h,
        "currently_admitted": active,
        "total_admitted": total_adm,
        "total_deaths": deaths
    }

def scrape_dengue():
    pdf_url, rep_date, pdf_bytes = find_latest_bulletin(DENGUE_INDEX_URLS, ["ডেঙ্গু", "ডেংগু", "dengue"])
    if not pdf_url or not pdf_bytes:
        print("no live dengue pdf found")
        return None

    print(f"parsing dengue pdf -> {pdf_url}")
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as f:
            f.write(pdf_bytes)
            tmp = f.name

        divisions = {}
        districts = {}

        with pdfplumber.open(tmp) as pdf:
            if not pdf.pages:
                return None
            if not rep_date:
                for p in pdf.pages[:2]:
                    d = parse_date_str(p.extract_text() or "")
                    if d:
                        rep_date = d
                        break

            p1 = pdf.pages[0]
            candidates = []
            for words in group_words_by_line(p1, tol=4.5):
                _, label, nums = split_line_tokens(words, p1.width)
                if not label or len(nums) < 5:
                    continue
                if any(k in bn_consonants(label) for k in ["সরবমট", "সবরমট", "অদযবধ", "ভরতরগ"]):
                    continue
                tot_adm, tot_d, tot_rel, act_h = nums[-4], nums[-3], nums[-2], nums[-1]
                if 50 <= tot_adm <= 100000 and abs((tot_adm - tot_d - tot_rel) - act_h) <= 10:
                    pre = nums[:-4]
                    c_24 = pre[0] if pre else 0
                    d_24 = pre[1] if len(pre) >= 2 else 0
                    candidates.append((match_division(label), {
                        "new_cases_24h": c_24,
                        "new_deaths_24h": d_24,
                        "currently_admitted": act_h,
                        "total_admitted": tot_adm,
                        "total_deaths": tot_d
                    }))

            if len(candidates) == 8:
                for i, (div_name, stats) in enumerate(candidates):
                    key = div_name or DENGUE_DIV_ORDER[i]
                    divisions[key] = stats
            else:
                for div_name, stats in candidates:
                    if div_name:
                        divisions[div_name] = stats

            for p_idx in range(3, len(pdf.pages)):
                page = pdf.pages[p_idx]
                words = page.extract_words()
                if not words:
                    continue
                pw = page.width
                d_words = sorted([w for w in words if w["x0"] >= pw * 0.40], key=lambda w: (w["top"] + w["bottom"]) / 2.0)
                l_words = [w for w in words if w["x0"] < pw * 0.40]

                clusters = []
                for w in d_words:
                    yc = (w["top"] + w["bottom"]) / 2.0
                    placed = False
                    for c in clusters:
                        if abs(yc - c["y"]) <= 3.6:
                            c["words"].append(w)
                            c["y"] = sum((i["top"] + i["bottom"]) / 2.0 for i in c["words"]) / len(c["words"])
                            placed = True
                            break
                    if not placed:
                        clusters.append({"y": yc, "words": [w]})

                for c in sorted(clusters, key=lambda i: i["y"]):
                    yc = c["y"]
                    r_nums = parse_int_list(" ".join(w["text"] for w in sorted(c["words"], key=lambda i: i["x0"])))
                    if len(r_nums) < 3 or any(yr in r_nums for yr in YEAR_NUMS) or max(r_nums) > 500000:
                        continue
                    near_labels = sorted([w for w in l_words if abs(((w["top"] + w["bottom"]) / 2.0) - yc) <= 8.5], key=lambda i: i["x0"])
                    s_cands = []
                    for w in near_labels:
                        if pw * 0.08 <= w["x0"] <= pw * 0.30:
                            s_cands.extend([n for n in parse_int_list(w["text"]) if 1 <= n <= 85])
                    serial = s_cands[0] if s_cands else None
                    label = clean_bn(" ".join(w["text"] for w in near_labels))
                    if is_summary_row(label) or "জেলার" in label:
                        continue
                    if serial in DISTRICT_SERIALS:
                        dist_name, div_name = DISTRICT_SERIALS[serial]
                        parsed = unpack_dengue_nums(r_nums)
                        if parsed:
                            if dist_name not in districts:
                                districts[dist_name] = {"district": dist_name, "division": div_name, **parsed}
                            else:
                                cur = districts[dist_name]
                                cur["new_cases_24h"] += parsed["new_cases_24h"]
                                cur["currently_admitted"] += parsed["currently_admitted"]
                                cur["total_admitted"] += parsed["total_admitted"]
                                cur["total_deaths"] += parsed["total_deaths"]

        div_list = [{"division": k, **v} for k, v in divisions.items()]
        return {
            "report_date": rep_date,
            "pdf_url": pdf_url,
            "divisions": div_list,
            "districts": list(districts.values())
        }
    except Exception as e:
        print(f"dengue parse error -> {e}")
        return None
    finally:
        if tmp and os.path.exists(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass

def unpack_measles_nums(nums):
    if len(nums) < 6:
        return None
    peak = max(nums)
    if peak < 50 or peak > 195000:
        return None
    c_24 = nums[0]
    adm = nums[-2]
    rel = nums[-1]
    if adm < 20 or adm > 160000:
        return None
    d_24 = nums[1] if (len(nums) >= 11 and nums[1] <= 10) else 0
    tot_d = d_24
    if len(nums) >= 8 and 0 <= nums[-5] < 5000:
        tot_d = nums[-5]
    return {
        "new_cases_24h": c_24,
        "currently_admitted": max(0, adm - rel),
        "total_suspected": peak,
        "new_deaths_24h": d_24,
        "total_deaths": tot_d
    }

def scrape_measles():
    pdf_url, rep_date, pdf_bytes = find_latest_bulletin(MEASLES_INDEX_URLS, ["হাম", "measles"])
    if not pdf_url or not pdf_bytes:
        print("no live measles pdf found")
        return None

    print(f"parsing measles pdf -> {pdf_url}")
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as f:
            f.write(pdf_bytes)
            tmp = f.name

        divisions = {}
        with pdfplumber.open(tmp) as pdf:
            for page in pdf.pages:
                found = []
                for words in group_words_by_line(page, tol=4.2):
                    line = clean_bn(" ".join(w["text"] for w in words))
                    if not line or "%" in line or is_summary_row(line):
                        continue
                    nums = parse_int_list(line)
                    if any(yr in nums for yr in YEAR_NUMS):
                        continue
                    parsed = unpack_measles_nums(nums)
                    if parsed and nums[0] < 1000:
                        found.append((match_division(line), parsed))
                if len(found) >= 8:
                    for i, (div_name, stats) in enumerate(found[:8]):
                        key = div_name if (div_name and div_name not in divisions) else MEASLES_DIV_ORDER[i]
                        divisions[key] = stats
                else:
                    for div_name, stats in found:
                        if div_name and div_name not in divisions:
                            divisions[div_name] = stats

        return {
            "report_date": rep_date,
            "pdf_url": pdf_url,
            "divisions": [{"division": k, **v} for k, v in divisions.items()]
        }
    except Exception as e:
        print(f"measles parse error -> {e}")
        return None
    finally:
        if tmp and os.path.exists(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass

def main():
    os.makedirs("data", exist_ok=True)
    out_path = "data/dengue_live.json"

    existing = {}
    if os.path.exists(out_path):
        try:
            with open(out_path, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            existing = {}

    dengue_data = scrape_dengue() or existing.get("dengue", {})
    measles_data = scrape_measles() or existing.get("measles", {})

    payload = {
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "source": "DGHS HEOC & Control Room",
        "dengue": dengue_data,
        "measles": measles_data
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    d_divs = len(dengue_data.get("divisions", [])) if isinstance(dengue_data, dict) else 0
    d_dists = len(dengue_data.get("districts", [])) if isinstance(dengue_data, dict) else 0
    m_divs = len(measles_data.get("divisions", [])) if isinstance(measles_data, dict) else 0
    print(f"saved dghs data: dengue ({d_divs} divs, {d_dists} districts), measles ({m_divs} divs)")

if __name__ == "__main__":
    main()
