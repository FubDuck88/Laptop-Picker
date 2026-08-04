"""
HP Official Store Malaysia Laptop Scraper
Fetches laptop listings from hp.com/my-en/shop/laptops.html and outputs to data/hp_laptops.csv.
Built using scrapers/scraper_template.py architecture.
"""

import os
import sys
import csv
import re
import time
import requests
from bs4 import BeautifulSoup


def get_base_dir():
    """Returns parent data directory whether running as raw script or frozen PyInstaller EXE."""
    if getattr(sys, "frozen", False):
        return os.path.join(os.path.dirname(sys.executable), "data")
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


OUTPUT_DIR = get_base_dir()
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "hp_laptops.csv")

FIELDNAMES = [
    "id", "title", "price", "url", "image_url", "series",
    "processor", "graphics", "memory", "storage",
    "display", "wifi", "battery", "others"
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def parse_hp_item(item, soup_item):
    """Parses single HP product item HTML element into structured laptop spec dictionary."""
    row = {
        "id": "", "title": "", "price": "", "url": "", "image_url": "", "series": "HP Official",
        "processor": "", "graphics": "", "memory": "", "storage": "",
        "display": "", "wifi": "", "battery": "", "others": ""
    }

    title_el = soup_item.find("a", class_=re.compile(r"product-item-link"))
    if title_el:
        row["title"] = title_el.get_text(strip=True)
        if "href" in title_el.attrs:
            row["url"] = title_el["href"]

    # Image URL
    img_el = soup_item.find("img", class_=re.compile(r"product-image-photo"))
    if img_el and "src" in img_el.attrs:
        row["image_url"] = img_el["src"]

    # Price
    price_box = soup_item.find("span", class_="price")
    if price_box:
        raw_price = price_box.get_text(strip=True).replace("RM", "").replace(",", "").strip()
        try:
            row["price"] = f"{float(raw_price):.2f}"
        except ValueError:
            row["price"] = raw_price

    # Part Number / SKU from attribute
    sku_el = soup_item.find(attrs={"data-sku": True})
    if sku_el:
        row["id"] = sku_el["data-sku"].strip()

    # Parse specifications from item details text
    details_el = soup_item.find("div", class_="product-item-details")
    if details_el:
        lines = [line.strip() for line in details_el.get_text(separator="\n", strip=True).split("\n") if line.strip()]
        others_list = []
        for line in lines:
            l_low = line.lower()
            if "processor" in l_low or "intel" in l_low or "ryzen" in l_low or "athlon" in l_low:
                if not row["processor"] and any(k in l_low for k in ["core", "ultra", "ryzen", "processor", "i3", "i5", "i7", "i9"]):
                    row["processor"] = line
            elif "graphics" in l_low or "geforce" in l_low or "rtx" in l_low or "radeon" in l_low or "arc" in l_low:
                if not row["graphics"]:
                    row["graphics"] = line
            elif "ram" in l_low or "ddr" in l_low or "memory" in l_low:
                if not row["memory"] and "gb" in l_low:
                    row["memory"] = line
            elif "ssd" in l_low or "storage" in l_low or "hard drive" in l_low:
                if not row["storage"]:
                    row["storage"] = line
            elif "display" in l_low or "screen" in l_low or 'diagonal' in l_low or '"' in l_low:
                if not row["display"] and any(k in l_low for k in ['"', "fhd", "qhd", "oled", "wuxga", "wqxga", "ips", "display", "screen"]):
                    row["display"] = line
            elif "windows" in l_low or "warranty" in l_low or "security" in l_low:
                others_list.append(line)

        if others_list:
            row["others"] = " | ".join(others_list)

    if not row["id"]:
        # Fallback SKU from URL
        sku_m = re.search(r'-([a-z0-9]{6,10})\.html', row["url"], re.I)
        if sku_m:
            row["id"] = sku_m.group(1).upper()

    return row


def scrape_hp():
    """Scrapes all laptop listings from HP Official Store Malaysia."""
    print("Scraping HP Official Store Malaysia...")
    session = requests.Session()
    session.headers.update(HEADERS)

    scraped_data = []
    seen_ids = set()
    page = 1

    while True:
        url = f"https://www.hp.com/my-en/shop/laptops.html?p={page}&product_list_limit=36"
        print(f"  Fetching HP Page {page}...")

        try:
            r = session.get(url, timeout=15)
            if r.status_code != 200:
                print(f"  HTTP {r.status_code} on page {page}. Stopping.")
                break

            soup = BeautifulSoup(r.text, "lxml")
            items = soup.find_all("li", class_="product-item")
            if not items:
                print(f"  No product items found on page {page}. Finished.")
                break

            added = 0
            for item in items:
                row = parse_hp_item(item, item)
                if not row["title"] or not row["url"]:
                    continue
                item_id = row["id"] or row["url"]
                if item_id in seen_ids:
                    continue
                seen_ids.add(item_id)
                scraped_data.append(row)
                added += 1

            print(f"  Page {page}: scraped {added} laptops (total: {len(scraped_data)})")
            if added == 0 or page >= 10:
                break
            page += 1
            time.sleep(1)

        except Exception as e:
            print(f"  Error fetching HP page {page}: {e}")
            break

    return scraped_data


def save_to_csv(rows, output_path=None):
    """Saves scraped laptop rows to CSV file."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = output_path or OUTPUT_FILE
    if not rows:
        print(f"No rows to save for {os.path.basename(filepath)}.")
        return

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print(f"Saved {len(rows)} laptops to {os.path.basename(filepath)}")


if __name__ == "__main__":
    data = scrape_hp()
    save_to_csv(data)
