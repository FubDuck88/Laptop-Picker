import sys
"""
PC Image Malaysia Gaming Laptop Scraper
Fetches laptop listings from store.pcimage.com.my/collection/gaming-laptop
and outputs to pcimage_laptops.csv.
"""

import requests
import json
import csv
import os
import re
import math
import time

OUTPUT_DIR = os.path.join(os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "pcimage_laptops.csv")

BASE_URL = "https://store.pcimage.com.my"
COLLECTION_URL = f"{BASE_URL}/collection/gaming-laptop"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def parse_specs_from_title(title):
    """Parses processor, graphics, memory, storage, and display from PC Image title strings."""
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

    # Processor patterns
    proc_pats = [
        r'(?:Intel\s+)?(?:Core\s+)?(?:Ultra\s+)?\d?\s*(?:i[3579]|C[UuA]\d)[^\s/]*(?:-\d+[A-Z]*)?',
        r'R[3579]\s*\d{3,4}[A-Z]*',
        r'Ryzen\s*\d?\s*\d{4}[A-Z]*',
        r'Athlon[^\s/]*',
    ]
    for pat in proc_pats:
        m = re.search(pat, title, re.IGNORECASE)
        if m:
            specs["processor"] = m.group(0).strip()
            break

    # Memory (RAM)
    m = re.search(r'(\d+GB\s*(?:D5|D4|DDR[45]\w*|LPDDR\w*|RAM)?[^\s/]*)', title, re.IGNORECASE)
    if m:
        specs["memory"] = m.group(1).strip()

    # Storage
    m = re.search(r'(\d+(?:GB|TB)\s*(?:G[34]|SSD|NVMe|PCIe)?[^\s/]*)', title, re.IGNORECASE)
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


def extract_products_from_html(html_text):
    """Extracts productListingPagination data from Next.js push calls."""
    pushes = re.findall(r'self\.__next_f\.push\((\[.*?\])\)</script>', html_text, re.DOTALL)
    
    for p in pushes:
        if "productListingPagination" in p:
            try:
                push_args = json.loads(p)
                str_content = push_args[1]
                idx = str_content.find("productListingPagination")
                if idx != -1:
                    start_idx = str_content.find("{", idx)
                    if start_idx != -1:
                        decoder = json.JSONDecoder()
                        data_obj, _ = decoder.raw_decode(str_content[start_idx:])
                        products = data_obj.get("data", [])
                        total = data_obj.get("total", 0)
                        return products, total
            except Exception as e:
                continue

    return [], 0


def scrape_pcimage():
    """Scrapes gaming laptops from PC Image E-Store."""
    print("Scraping PC Image Gaming Laptops...")
    session = requests.Session()
    session.headers.update(HEADERS)

    all_products = []
    seen_ids = set()
    page = 1
    total_pages = 1

    while page <= total_pages:
        url = f"{COLLECTION_URL}?page={page}"
        print(f"  Fetching page {page}...")

        try:
            r = session.get(url, timeout=30)
            if r.status_code != 200:
                print(f"  Page {page} HTTP status: {r.status_code}")
                break

            products, total_count = extract_products_from_html(r.text)
            print(f"  Page {page}: got {len(products)} products (Total: {total_count})")

            if total_count > 0:
                total_pages = math.ceil(total_count / 24)

            if not products:
                break

            for p in products:
                product_id = str(p.get("id") or "")
                sku = (p.get("sku") or product_id).strip()
                name = (p.get("name") or "").strip()
                brand_info = p.get("brands") or {}
                brand_name = brand_info.get("name") if isinstance(brand_info, dict) else ""

                if not sku or sku in seen_ids:
                    continue
                seen_ids.add(sku)

                # Price calculation (special_price if available, else price)
                price_obj = p.get("special_price") or p.get("price") or "0"
                if isinstance(price_obj, dict):
                    price_val = price_obj.get("price") or price_obj.get("converted_price") or "0"
                else:
                    price_val = str(price_obj)

                # URL
                seo = p.get("seo") or {}
                handle = seo.get("url_handle", "") if isinstance(seo, dict) else ""
                product_url = f"{BASE_URL}/product/{handle}" if handle else BASE_URL

                # Image URL
                images = p.get("images") or []
                img_url = ""
                if images and isinstance(images, list) and len(images) > 0:
                    img_url = images[0].get("x420_url") or images[0].get("url") or ""

                # Parse specs
                specs = parse_specs_from_title(name)

                row = {
                    "id": sku,
                    "title": name,
                    "price": str(price_val),
                    "url": product_url,
                    "image_url": img_url,
                    "series": f"PC Image - {brand_name}" if brand_name else "PC Image Gaming",
                    "processor": specs["processor"],
                    "graphics": specs["graphics"],
                    "memory": specs["memory"],
                    "storage": specs["storage"],
                    "display": specs["display"],
                    "wifi": specs["wifi"],
                    "battery": specs["battery"],
                    "others": "",
                }
                all_products.append(row)
                safe_title = name.encode('ascii', 'ignore').decode()
                print(f"    OK: [{sku[:20]}] {safe_title[:65]} — RM {price_val}")

            page += 1
            time.sleep(1)

        except Exception as e:
            print(f"  Error on page {page}: {e}")
            break

    print(f"\nExtracted {len(all_products)} gaming laptops from PC Image!")
    return all_products


def save_to_csv(rows):
    """Saves scraped rows to CSV file. Preserves existing file if 0 rows returned."""
    if not rows:
        if os.path.exists(OUTPUT_FILE):
            print(f"  No new rows scraped; preserving existing {OUTPUT_FILE}")
        else:
            print("  No rows to save.")
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
    data = scrape_pcimage()
    save_to_csv(data)

    # Auto-run master combiner
    try:
        import run_all
        run_all.combine_all_csvs()
    except Exception as e:
        print("Run master combiner manually: python run_all.py")
