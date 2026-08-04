import sys
import os
import glob
import json
import csv
import re
from bs4 import BeautifulSoup

OUTPUT_DIR = os.path.join(os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "msi_laptops.csv")

SEARCH_DIRS = [
    OUTPUT_DIR
]

# Strict non-laptop exclusion rules
EXCLUDE_SKU_PREFIXES = ("MB-", "MNT-", "DC-", "KB-", "FG-", "PBM-", "ACC-")
EXCLUDE_KEYWORDS = (
    "motherboard", "keyboard", "monitor", "desktop", "mousepad", 
    "customized gaming pc", "headset", "bag", "backpack", "pin badge", 
    "luggage", "wifi adapter", "charger", "power supply", "cooler"
)

def parse_msi_body_html(body_html):
    """Parses detailed spec sheet HTML (tables and lists) into structured spec columns."""
    if not body_html:
        return {}
    
    soup = BeautifulSoup(body_html, "lxml")
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
    others_dict = {}

    # 1. Check for detailed HTML spec tables <tr><td>KEY</td><td>VALUE</td></tr>
    rows = soup.find_all("tr")
    if rows:
        for r in rows:
            cols = r.find_all("td")
            if len(cols) >= 2:
                key = cols[0].get_text(strip=True).upper()
                val = cols[1].get_text(separator=" ", strip=True)
                if not key or not val:
                    continue
                
                if any(k in key for k in ("PROCESSOR", "CPU")):
                    specs["processor"] = val
                elif any(k in key for k in ("GRAPHIC", "GPU", "VGA")):
                    specs["graphics"] = val
                elif any(k in key for k in ("MEMORY", "RAM")):
                    specs["memory"] = val
                elif any(k in key for k in ("STORAGE", "SSD", "HARD DRIVE")):
                    specs["storage"] = val
                elif any(k in key for k in ("DISPLAY", "SCREEN")):
                    specs["display"] = val
                elif any(k in key for k in ("COMMUNICATION", "WIFI", "WLAN", "NETWORK")):
                    specs["wifi"] = val
                elif any(k in key for k in ("BATTERY", "AC ADAPTER")):
                    specs["battery"] = val
                else:
                    # Collect all other detailed technical specs (OS, Ports, Dimensions, Weight, Color, Warranty)
                    others_dict[key] = val

    # 2. Check for bullet point specs <li> if table rows missed any key fields
    lis = soup.find_all("li")
    for li in lis:
        t = li.get_text(separator=" ", strip=True)
        t_low = t.lower()
        if not specs["processor"] and any(k in t_low for k in ("intel", "ryzen", "processor", "core ultra")):
            specs["processor"] = t
        elif not specs["graphics"] and any(k in t_low for k in ("rtx", "geforce", "radeon", "graphics", "gpu", "arc")):
            specs["graphics"] = t
        elif not specs["display"] and any(k in t_low for k in ('"', "inch", "fhd", "qhd", "uhd", "144hz", "165hz", "240hz", "oled", "ips")):
            specs["display"] = t
        elif not specs["storage"] and any(k in t_low for k in ("ssd", "nvme", "pcie", "1tb", "2tb", "512gb")):
            specs["storage"] = t
        elif not specs["memory"] and any(k in t_low for k in ("ddr4", "ddr5", "lpddr5x", "memory", "ram")):
            specs["memory"] = t
        elif not specs["wifi"] and any(k in t_low for k in ("wi-fi", "wifi", "bluetooth")):
            specs["wifi"] = t
        elif not specs["battery"] and any(k in t_low for k in ("whr", "whrs", "cell", "battery")):
            specs["battery"] = t

    # Format others string
    others_formatted = [f"{k}: {v}" for k, v in others_dict.items()]
    specs["others"] = " | ".join(others_formatted)
    return specs

def find_msi_json_files():
    files = []
    for d in SEARCH_DIRS:
        if os.path.exists(d):
            for root, _, filenames in os.walk(d):
                for f in filenames:
                    if "content.md" in f or "products.json" in f or "msi" in f.lower():
                        filepath = os.path.join(root, f)
                        files.append(filepath)
    return files

def scrape_msi():
    print("Searching for MSI JSON files...")
    json_files = find_msi_json_files()
    print(f"Found {len(json_files)} potential JSON data files.")

    all_products = []
    seen_ids = set()

    for filepath in json_files:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            
            json_start = content.find('{"products":')
            if json_start == -1:
                continue
            content = content[json_start:]
            
            data = json.loads(content)
            products = data.get("products", [])
            
            for p in products:
                title = p.get("title", "").strip()
                p_type = (p.get("product_type") or "").upper()
                tags = [t.lower() for t in p.get("tags", [])]
                variants = p.get("variants", [])
                v0 = variants[0] if variants else {}
                sku = (v0.get("sku") or str(p.get("id"))).strip()

                # --- Strict Laptop Filtering ---
                if any(sku.startswith(prefix) for prefix in EXCLUDE_SKU_PREFIXES):
                    continue
                if any(k in title.lower() for k in EXCLUDE_KEYWORDS):
                    continue

                is_laptop = (
                    p_type in ("NB", "HANDHELD PCS", "LAPTOPS") or
                    "laptop" in title.lower() or
                    "handheld" in title.lower() or
                    any("laptop" in tag or "notebook" in tag for tag in tags) or
                    sku.startswith("NB-") or sku.startswith("GC-")
                )
                if not is_laptop:
                    continue

                if not sku or sku in seen_ids:
                    continue
                seen_ids.add(sku)

                price = v0.get("price") or "0"
                handle = p.get("handle", "")
                url = f"https://my-store.msi.com/products/{handle}" if handle else "https://my-store.msi.com/"

                images = p.get("images", [])
                img_url = ""
                if images and isinstance(images, list) and len(images) > 0:
                    img_url = images[0].get("src", "")
                if not img_url:
                    img_url = (p.get("image") or {}).get("src", "")
                
                if img_url.startswith("//"):
                    img_url = "https:" + img_url
                elif img_url.startswith("/"):
                    img_url = "https://my-store.msi.com" + img_url

                specs = parse_msi_body_html(p.get("body_html", ""))

                row = {
                    "id": sku,
                    "title": title,
                    "price": price,
                    "url": url,
                    "image_url": img_url,
                    "series": "MSI Official",
                    "processor": specs.get("processor", ""),
                    "graphics": specs.get("graphics", ""),
                    "memory": specs.get("memory", ""),
                    "storage": specs.get("storage", ""),
                    "display": specs.get("display", ""),
                    "wifi": specs.get("wifi", ""),
                    "battery": specs.get("battery", ""),
                    "others": specs.get("others", "")
                }
                all_products.append(row)
                safe_title = title.encode('ascii', 'ignore').decode()
                print(f"  OK Laptop: [{sku}] {safe_title} — RM {price}")
        except Exception as e:
            continue

    print(f"\nExtracted {len(all_products)} strictly verified MSI laptops!")
    return all_products

def save_to_csv(rows):
    if not rows:
        print("No rows to save.")
        return
    fieldnames = ["id", "title", "price", "url", "image_url", "series", "processor", "graphics", "memory", "storage", "display", "wifi", "battery", "others"]
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print(f"Saved {len(rows)} rows to {OUTPUT_FILE}")

if __name__ == "__main__":
    data = scrape_msi()
    save_to_csv(data)
    
    # Auto-run master combiner
    try:
        import run_all
        run_all.combine_all_csvs()
    except Exception as e:
        print("Run master combiner manually: python run_all.py")
