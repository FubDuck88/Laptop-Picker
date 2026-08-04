"""
ALL IT Hypermarket Laptop Scraper
Fetches laptop listings from allithypermarket.com.my Shopify JSON API
and outputs to allit_laptops.csv.

Strategy: Uses Shopify's /collections/laptop/products.json endpoint with
session-based requests and robust rate-limit handling.
"""

import requests
import json
import csv
import os
import re
import time
from bs4 import BeautifulSoup

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "allit_laptops.csv")

BASE_URL = "https://www.allithypermarket.com.my"
COLLECTION_API = f"{BASE_URL}/collections/laptop/products.json"
PAGE_SIZE = 30  # Use smaller page size to reduce server load

# Full browser-like headers to avoid bot detection
BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Sec-Ch-Ua": '"Chromium";v="131", "Not_A Brand";v="24"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
}


def parse_allit_body_html(body_html):
    """Parses ALL IT product body_html into structured spec columns.

    The body_html typically contains <p> tags with specs in two formats:
      - "Key: Value" pairs (e.g., "Processor: Intel® Core™ i7-13700H")
      - Bullet-point highlights (e.g., "• 16GB DDR5 RAM for smooth multitasking")
    """
    specs = {
        "processor": "",
        "graphics": "",
        "memory": "",
        "storage": "",
        "display": "",
        "wifi": "",
        "battery": "",
        "others": ""
    }
    if not body_html:
        return specs

    soup = BeautifulSoup(body_html, "lxml")
    others_parts = []

    # Collect all text lines from paragraphs, list items, and table cells
    elements = soup.find_all(["p", "li", "td", "span"])

    # Build a list of clean text lines, merging "Key:" on one line with value on next
    text_lines = []
    for el in elements:
        t = el.get_text(separator=" ", strip=True)
        # Skip empty lines and decorative content
        if not t or t in ("•", "-", " "):
            continue
        # Remove leading bullet characters
        t = re.sub(r'^[•\-]\s*', '', t).strip()
        if t:
            text_lines.append(t)

    # First pass: try "Key: Value" format (e.g., "Processor: Intel Core i7")
    i = 0
    while i < len(text_lines):
        line = text_lines[i]

        # Check if this line is a key label ending with ":"
        # and the next line is the value
        key_match = re.match(r'^([\w\s/&]+):\s*$', line)
        if key_match and i + 1 < len(text_lines):
            key = key_match.group(1).strip().upper()
            val = text_lines[i + 1].strip()
            _assign_spec(specs, key, val, others_parts)
            i += 2
            continue

        # Check if this line is "Key: Value" on a single line
        kv_match = re.match(r'^([\w\s/&]+):\s+(.+)$', line)
        if kv_match:
            key = kv_match.group(1).strip().upper()
            val = kv_match.group(2).strip()
            _assign_spec(specs, key, val, others_parts)
            i += 1
            continue

        i += 1

    # Second pass: fallback keyword matching for any specs still empty
    for line in text_lines:
        t_low = line.lower()
        if not specs["processor"] and any(k in t_low for k in ("intel", "ryzen", "processor", "core ultra", "core™", "athlon", "snapdragon")):
            if not re.match(r'^processor\s*:?\s*$', t_low):
                specs["processor"] = line
        elif not specs["graphics"] and any(k in t_low for k in ("geforce", "rtx", "radeon", "graphics", "gpu", "arc", "nvidia")):
            if not re.match(r'^graphics\s*:?\s*$', t_low):
                specs["graphics"] = line
        elif not specs["display"] and any(k in t_low for k in ('"', "inch", "fhd", "qhd", "wuxga", "wqxga", "uhd", "144hz", "165hz", "240hz", "oled", "ips", "1920")):
            if not re.match(r'^display\s*:?\s*$', t_low):
                specs["display"] = line
        elif not specs["storage"] and any(k in t_low for k in ("ssd", "nvme", "pcie", "1tb", "2tb", "512gb", "256gb")):
            if not re.match(r'^storage\s*:?\s*$', t_low):
                specs["storage"] = line
        elif not specs["memory"] and any(k in t_low for k in ("ddr4", "ddr5", "lpddr", "memory", "ram", "16gb", "32gb", "8gb")):
            if not re.match(r'^memory\s*:?\s*$', t_low):
                specs["memory"] = line
        elif not specs["wifi"] and any(k in t_low for k in ("wi-fi", "wifi", "bluetooth", "wireless")):
            if not re.match(r'^(connection type|wifi|wireless)\s*:?\s*$', t_low):
                specs["wifi"] = line
        elif not specs["battery"] and any(k in t_low for k in ("whr", "whrs", "cell", "battery")):
            if not re.match(r'^battery\s*:?\s*$', t_low):
                specs["battery"] = line

    if others_parts:
        specs["others"] = " | ".join(others_parts)

    return specs


def _assign_spec(specs, key, val, others_parts):
    """Assigns a key-value pair to the correct spec field."""
    if any(k in key for k in ("PROCESSOR", "CPU")):
        if not specs["processor"]:
            specs["processor"] = val
    elif any(k in key for k in ("GRAPHIC", "GPU", "VGA")):
        if not specs["graphics"]:
            specs["graphics"] = val
    elif any(k in key for k in ("MEMORY", "RAM")):
        if not specs["memory"]:
            specs["memory"] = val
    elif any(k in key for k in ("STORAGE", "SSD", "HARD DRIVE")):
        if not specs["storage"]:
            specs["storage"] = val
    elif any(k in key for k in ("DISPLAY", "SCREEN")):
        if not specs["display"]:
            specs["display"] = val
    elif any(k in key for k in ("CONNECTION", "WIFI", "WLAN", "WIRELESS", "NETWORK")):
        if not specs["wifi"]:
            specs["wifi"] = val
    elif any(k in key for k in ("BATTERY",)):
        if not specs["battery"]:
            specs["battery"] = val
    elif key not in ("BRAND", "PRODUCT TYPE", "WHAT'S IN THE BOX", "WARRANTY",
                     "WARRANTY DURATION", "WARRANTY TYPE", "SOFTWARE INCLUDED",
                     "PRODUCT HIGHLIGHTS", "KEY SPECIFICATIONS", "AVAILABLE COLOURS",
                     "MODEL", "SERIES", ""):
        others_parts.append(f"{key}: {val}")


def parse_specs_from_title(title):
    """Fallback: extract basic specs directly from product title.
    
    ALL IT titles often contain specs inline, e.g.:
    'HP AI Laptop 15-fd2115TU CU5-225U/16GB DDR5/512GB SSD/15.6"FHD'
    """
    specs = {
        "processor": "",
        "graphics": "",
        "memory": "",
        "storage": "",
        "display": "",
        "wifi": "",
        "battery": "",
        "others": ""
    }
    if not title:
        return specs
    
    t_low = title.lower()
    
    # Processor patterns
    proc_patterns = [
        r'(?:Intel\s+)?(?:Core\s+)?(?:Ultra\s+)?\d?\s*(?:i[3579]|C[UuA]\d)[^\s/]*(?:-\d+[A-Z]*)?',
        r'Ryzen\s*\d?\s*\d{4}[A-Z]*',
        r'Athlon[^\s/]*',
        r'Snapdragon[^\s/]*',
    ]
    for pat in proc_patterns:
        m = re.search(pat, title, re.IGNORECASE)
        if m:
            specs["processor"] = m.group(0).strip()
            break
    
    # Memory (RAM) 
    m = re.search(r'(\d+GB\s*(?:DDR[45]\w*|LPDDR\w*|RAM))', title, re.IGNORECASE)
    if m:
        specs["memory"] = m.group(1).strip()
    
    # Storage
    m = re.search(r'(\d+(?:GB|TB)\s*(?:SSD|NVMe|PCIe)[^\s/]*)', title, re.IGNORECASE)
    if m:
        specs["storage"] = m.group(1).strip()
    
    # Display
    m = re.search(r'(\d+\.?\d*["\u201d]?\s*(?:FHD|QHD|WUXGA|WQXGA|UHD|HD|OLED)[^\s/]*(?:\s*\d+Hz)?)', title, re.IGNORECASE)
    if m:
        specs["display"] = m.group(1).strip()
    
    # Graphics
    m = re.search(r'((?:RTX|GTX|GeForce|Radeon)\s*\d+[^\s/]*)', title, re.IGNORECASE)
    if m:
        specs["graphics"] = m.group(1).strip()
    
    return specs


def create_session():
    """Creates a requests session with browser-like headers."""
    session = requests.Session()
    session.headers.update(BROWSER_HEADERS)
    return session


def fetch_json_with_retry(session, url, max_retries=2, initial_wait=2):
    """Fetches JSON from URL with rate-limit protection and fast fail on non-JSON response."""
    for attempt in range(max_retries):
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                "Accept": "application/json, text/plain, */*"
            }
            r = requests.get(url, headers=headers, timeout=15)

            if r.status_code == 429:
                wait_time = initial_wait * (attempt + 1)
                print(f"    Rate limited (429). Waiting {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
                continue

            if r.status_code != 200:
                print(f"    HTTP {r.status_code}")
                return None

            text = r.text.strip()
            if not text.startswith("{") and not text.startswith("["):
                print(f"    Non-JSON response received (starts with '{text[:30]}'). Skipping.")
                return None

            return json.loads(text)

        except Exception as e:
            print(f"    Error (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(initial_wait)
                continue
            return None

    return None


def scrape_allit():
    """Scrapes all laptops from ALL IT Hypermarket via Shopify JSON API."""
    print("Scraping ALL IT Hypermarket laptops...")
    print("  (Note: This site has aggressive rate limiting. Retries may take a while.)")
    
    session = create_session()
    all_products = []
    seen_ids = set()
    page = 1

    # Warm up session with main page visit
    print("  Warming up session...")
    try:
        session.get(BASE_URL, timeout=30)
    except Exception:
        pass
    time.sleep(3)

    # Update headers for JSON requests
    session.headers["Accept"] = "application/json, text/plain, */*"
    session.headers["Referer"] = f"{BASE_URL}/collections/laptop"

    while True:
        url = f"{COLLECTION_API}?limit={PAGE_SIZE}&page={page}"
        print(f"  Fetching page {page}...")

        data = fetch_json_with_retry(session, url, max_retries=5, initial_wait=5)
        if data is None:
            print(f"  Failed to fetch page {page}. Stopping.")
            break

        products = data.get("products", [])
        print(f"  Page {page}: got {len(products)} products")

        if not products:
            break

        for p in products:
            product_id = str(p.get("id", ""))
            title = (p.get("title") or "").strip()
            handle = p.get("handle", "")
            vendor = p.get("vendor", "")
            body_html = p.get("body_html", "")

            # Skip Acer products — handled by acer_scraper.py
            if vendor.lower() == "acer":
                continue

            # Get variant info (use first variant for price/sku)
            variants = p.get("variants", [])
            v0 = variants[0] if variants else {}
            sku = (v0.get("sku") or product_id).strip()
            price = v0.get("price") or "0"

            # Skip duplicates
            if sku in seen_ids:
                continue
            seen_ids.add(sku)

            # Build product URL
            product_url = f"{BASE_URL}/products/{handle}" if handle else BASE_URL

            # Get image URL
            images = p.get("images", [])
            img_url = ""
            if images and isinstance(images, list) and len(images) > 0:
                img_url = images[0].get("src", "")
            if img_url.startswith("//"):
                img_url = "https:" + img_url

            # Parse specs from body HTML, with title fallback
            specs = parse_allit_body_html(body_html)
            
            # If body_html parsing missed specs, try extracting from title
            title_specs = parse_specs_from_title(title)
            for key in ("processor", "graphics", "memory", "storage", "display"):
                if not specs[key] and title_specs.get(key):
                    specs[key] = title_specs[key]

            row = {
                "id": sku,
                "title": title,
                "price": price,
                "url": product_url,
                "image_url": img_url,
                "series": f"ALL IT - {vendor}" if vendor else "ALL IT Hypermarket",
                "processor": specs.get("processor", ""),
                "graphics": specs.get("graphics", ""),
                "memory": specs.get("memory", ""),
                "storage": specs.get("storage", ""),
                "display": specs.get("display", ""),
                "wifi": specs.get("wifi", ""),
                "battery": specs.get("battery", ""),
                "others": specs.get("others", ""),
            }
            all_products.append(row)
            safe_title = title.encode('ascii', 'ignore').decode()
            print(f"    OK: [{sku}] {safe_title} — RM {price}")

        # Check if there are more pages
        if len(products) < PAGE_SIZE:
            break

        page += 1
        time.sleep(3)  # Be polite between pages

    print(f"\nExtracted {len(all_products)} laptops from ALL IT Hypermarket!")
    return all_products


def save_to_csv(rows):
    """Saves scraped rows to CSV file."""
    if not rows:
        print("No rows to save.")
        return
    fieldnames = [
        "id", "title", "price", "url", "image_url", "series",
        "processor", "graphics", "memory", "storage",
        "display", "wifi", "battery", "others"
    ]
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print(f"Saved {len(rows)} rows to {OUTPUT_FILE}")


if __name__ == "__main__":
    data = scrape_allit()
    save_to_csv(data)

    # Auto-run master combiner
    try:
        import run_all
        run_all.combine_all_csvs()
    except Exception as e:
        print("Run master combiner manually: python run_all.py")
