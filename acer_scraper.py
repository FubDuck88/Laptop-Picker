"""
Acer Malaysia Laptop Scraper
Fetches laptop listings from Acer's catalog API and outputs to acer_laptops.csv.

Strategy: Tries the Acer Magento GraphQL API first. If that fails (timeouts/blocks),
falls back to scraping Acer laptops from ALL IT Hypermarket's Shopify API.
"""

import requests
import json
import csv
import os
import re
import time
from bs4 import BeautifulSoup

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "acer_laptops.csv")

# --- Acer Magento GraphQL (Primary) ---
GRAPHQL_URL = "https://store.acer.com/en-my/graphql"
GRAPHQL_QUERY = """
query GetAcerLaptops($currentPage: Int!, $pageSize: Int!) {
  products(
    filter: { category_id: { eq: "laptops" } }
    currentPage: $currentPage
    pageSize: $pageSize
  ) {
    total_count
    items {
      sku
      name
      url_key
      price_range {
        minimum_price {
          final_price {
            value
            currency
          }
        }
      }
      short_description {
        html
      }
    }
  }
}
"""

# --- ALL IT Hypermarket Fallback ---
ALLIT_BASE_URL = "https://www.allithypermarket.com.my"
ALLIT_PRODUCTS_API = f"{ALLIT_BASE_URL}/collections/laptop/products.json"

BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}


def parse_acer_specs(html_str):
    """Parses Acer short description HTML into structured specs."""
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
    if not html_str:
        return specs
        
    soup = BeautifulSoup(html_str, "lxml")
    others_parts = []

    # Collect all text from paragraphs, list items, table cells
    elements = soup.find_all(["p", "li", "td", "span"])
    text_lines = []
    for el in elements:
        t = el.get_text(separator=" ", strip=True)
        if not t or t in ("•", "-", " "):
            continue
        t = re.sub(r'^[•\-]\s*', '', t).strip()
        if t:
            text_lines.append(t)

    # First pass: "Key: Value" format
    i = 0
    while i < len(text_lines):
        line = text_lines[i]
        key_match = re.match(r'^([\w\s/&]+):\s*$', line)
        if key_match and i + 1 < len(text_lines):
            key = key_match.group(1).strip().upper()
            val = text_lines[i + 1].strip()
            _assign_spec(specs, key, val, others_parts)
            i += 2
            continue
        kv_match = re.match(r'^([\w\s/&]+):\s+(.+)$', line)
        if kv_match:
            key = kv_match.group(1).strip().upper()
            val = kv_match.group(2).strip()
            _assign_spec(specs, key, val, others_parts)
            i += 1
            continue
        i += 1

    # Second pass: keyword fallback
    for line in text_lines:
        t_low = line.lower()
        if not specs["processor"] and any(k in t_low for k in ("intel", "ryzen", "processor", "core ultra", "core™", "athlon")):
            if not re.match(r'^processor\s*:?\s*$', t_low):
                specs["processor"] = line
        elif not specs["graphics"] and any(k in t_low for k in ("geforce", "rtx", "radeon", "graphics", "gpu", "arc", "nvidia")):
            if not re.match(r'^graphics\s*:?\s*$', t_low):
                specs["graphics"] = line
        elif not specs["display"] and any(k in t_low for k in ('"', "inch", "fhd", "qhd", "wuxga", "wqxga", "144hz", "165hz", "oled", "ips", "1920")):
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


# ===== PRIMARY: Acer Magento GraphQL =====

def scrape_acer_graphql():
    """Tries scraping from Acer's Magento GraphQL API."""
    print("  Trying Acer Magento GraphQL API...")
    scraped_rows = []
    
    # Quick connectivity check with short timeout
    try:
        test_r = requests.head(
            "https://store.acer.com/en-my/",
            headers={"User-Agent": BROWSER_HEADERS["User-Agent"]},
            timeout=10
        )
        print(f"  Store reachable (HTTP {test_r.status_code})")
    except Exception as e:
        print(f"  Store unreachable: {e}")
        return None  # Signal to use fallback
    
    page = 1
    while True:
        payload = {
            "query": GRAPHQL_QUERY,
            "variables": {"currentPage": page, "pageSize": 30}
        }
        try:
            r = requests.post(
                GRAPHQL_URL, 
                json=payload, 
                headers={
                    "User-Agent": BROWSER_HEADERS["User-Agent"],
                    "Accept": "application/json, text/plain, */*",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Referer": "https://store.acer.com/en-my/",
                    "Content-Type": "application/json"
                }, 
                timeout=30
            )
            if r.status_code != 200:
                print(f"  Page {page} status: {r.status_code}")
                if not scraped_rows:
                    return None  # No data at all, use fallback
                break
            
            data = r.json()
            products_data = data.get("data", {}).get("products", {})
            items = products_data.get("items", [])
            total = products_data.get("total_count", 0)
            
            print(f"  Page {page}: got {len(items)} items (Total: {total})")
            if not items:
                break
                
            for item in items:
                sku = item.get("sku", "")
                name = item.get("name", "")
                price_val = item.get("price_range", {}).get("minimum_price", {}).get("final_price", {}).get("value", "")
                url_key = item.get("url_key", "")
                url = f"https://store.acer.com/en-my/{url_key}.html" if url_key else "https://store.acer.com/en-my/"
                
                short_desc = item.get("short_description", {}).get("html", "")
                specs = parse_acer_specs(short_desc)
                
                scraped_rows.append({
                    "id": sku,
                    "title": name,
                    "price": str(price_val),
                    "url": url,
                    "image_url": "",
                    "series": "Acer Official",
                    "processor": specs["processor"],
                    "graphics": specs["graphics"],
                    "memory": specs["memory"],
                    "storage": specs["storage"],
                    "display": specs["display"],
                    "wifi": specs["wifi"],
                    "battery": specs["battery"],
                    "others": ""
                })
                
            if len(scraped_rows) >= total or len(items) < 30:
                break
            page += 1
            time.sleep(1)
        except requests.exceptions.Timeout:
            print(f"  Timeout on page {page}")
            if not scraped_rows:
                return None  # No data, use fallback
            break
        except Exception as e:
            print(f"  Error on page {page}: {e}")
            if not scraped_rows:
                return None
            break
            
    return scraped_rows


# ===== FALLBACK: ALL IT Hypermarket (Acer products only) =====

def fetch_json_with_retry(session, url, max_retries=5, initial_wait=5):
    """Fetches JSON from URL with exponential backoff for rate limiting."""
    for attempt in range(max_retries):
        try:
            r = session.get(url, timeout=30)
            if r.status_code == 429:
                retry_after = int(r.headers.get("Retry-After", initial_wait))
                wait_time = max(retry_after, initial_wait * (attempt + 1))
                print(f"    Rate limited (429). Waiting {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
                continue
            if r.status_code != 200:
                print(f"    HTTP {r.status_code}")
                return None
            return r.json()
        except Exception as e:
            print(f"    Error (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(initial_wait * (attempt + 1))
                continue
            return None
    print(f"    Exhausted all {max_retries} retries.")
    return None


def scrape_acer_from_allit():
    """Fallback: scrapes Acer laptops from ALL IT Hypermarket."""
    print("  Using fallback: ALL IT Hypermarket (Acer laptops)...")
    
    session = requests.Session()
    session.headers.update(BROWSER_HEADERS)
    
    # Warm up session
    try:
        session.get(ALLIT_BASE_URL, timeout=30)
    except Exception:
        pass
    time.sleep(3)
    
    session.headers["Accept"] = "application/json, text/plain, */*"
    session.headers["Referer"] = f"{ALLIT_BASE_URL}/collections/laptop"
    
    all_products = []
    seen_ids = set()
    page = 1
    
    while True:
        url = f"{ALLIT_PRODUCTS_API}?limit=250&page={page}"
        print(f"  Fetching page {page}...")
        
        data = fetch_json_with_retry(session, url)
        if data is None:
            break
        
        products = data.get("products", [])
        print(f"  Page {page}: got {len(products)} products")
        
        if not products:
            break
        
        for p in products:
            vendor = (p.get("vendor") or "").strip()
            # Only keep Acer products
            if vendor.lower() != "acer":
                continue
            
            product_id = str(p.get("id", ""))
            title = (p.get("title") or "").strip()
            handle = p.get("handle", "")
            body_html = p.get("body_html", "")
            
            variants = p.get("variants", [])
            v0 = variants[0] if variants else {}
            sku = (v0.get("sku") or product_id).strip()
            price = v0.get("price") or "0"
            
            if sku in seen_ids:
                continue
            seen_ids.add(sku)
            
            product_url = f"{ALLIT_BASE_URL}/products/{handle}" if handle else ALLIT_BASE_URL
            
            images = p.get("images", [])
            img_url = ""
            if images and isinstance(images, list) and len(images) > 0:
                img_url = images[0].get("src", "")
            if img_url.startswith("//"):
                img_url = "https:" + img_url
            
            specs = parse_acer_specs(body_html)
            
            all_products.append({
                "id": sku,
                "title": title,
                "price": price,
                "url": product_url,
                "image_url": img_url,
                "series": "Acer (via ALL IT)",
                "processor": specs.get("processor", ""),
                "graphics": specs.get("graphics", ""),
                "memory": specs.get("memory", ""),
                "storage": specs.get("storage", ""),
                "display": specs.get("display", ""),
                "wifi": specs.get("wifi", ""),
                "battery": specs.get("battery", ""),
                "others": specs.get("others", ""),
            })
            safe_title = title.encode('ascii', 'ignore').decode()
            print(f"    OK: [{sku}] {safe_title} — RM {price}")
        
        if len(products) < 250:
            break
        page += 1
        time.sleep(2)
    
    return all_products


# ===== MAIN =====

def scrape_acer():
    """Scrapes Acer Malaysia laptops. Tries official store first, falls back to ALL IT."""
    print("Scraping Acer Malaysia laptops...")
    
    # Try primary source (Acer Magento GraphQL)
    rows = scrape_acer_graphql()
    
    if rows is None or len(rows) == 0:
        print("  Acer store unavailable. Falling back to ALL IT Hypermarket...")
        rows = scrape_acer_from_allit()
    
    if rows:
        print(f"\nExtracted {len(rows)} Acer laptops!")
    else:
        print("\nNo Acer laptops could be scraped from any source.")
    
    return rows or []


def save_to_csv(rows):
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
    data = scrape_acer()
    save_to_csv(data)
    
    # Auto-run master combiner
    try:
        import run_all
        run_all.combine_all_csvs()
    except Exception as e:
        print("Run master combiner manually: python run_all.py")
