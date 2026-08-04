"""
Master Laptop Combiner with Cross-Vendor Price & Deal Comparison
Combines all scraped CSV files into master_laptops.csv.
Groups identical laptop models (by Part Number / MPN and hardware spec) across vendors so users can compare prices.
"""

import os
import glob
import csv
import re
import subprocess
from collections import defaultdict

import sys
import importlib

def get_base_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

MASTER_DIR = get_base_dir()
DATA_DIR = os.path.join(MASTER_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)
MASTER_FILE = os.path.join(DATA_DIR, "master_laptops.csv")

FIELDNAMES = [
    "id", "title", "price", "best_vendor", "vendor_prices", "vendor_count", 
    "url", "vendor_urls", "image_url", "series",
    "processor", "graphics", "memory", "storage",
    "display", "wifi", "battery", "others"
]


def extract_part_number(title, rid):
    """Extracts official part number / model code from title or ID."""
    text = (rid + " " + title).upper()

    # 1. Lenovo MTM (10 characters: 83xxxxxx, 21xxxxxx, 22xxxxxx)
    m = re.search(r'\b(83[A-Z0-9]{8}|21[A-Z0-9]{8}|22[A-Z0-9]{8})\b', text)
    if m:
        return m.group(1)

    # 2. ASUS Part Numbers: FA608U-HITU066W, FX608J-MRRV058W, GA403G-MSY018W, G614P-HTS157WP
    m = re.search(r'\b([A-Z]{2}\d{3}[A-Z]{1,2}[-\s][A-Z0-9]{4,10})\b', text)
    if m:
        return m.group(1).replace(" ", "-")

    # 3. HP Part Numbers: 15-FA2547TX, 16-AM0166TX, 15-FB3220AX, 16-AP0057AX, 14-FB0045TX
    m = re.search(r'\b(\d{2}-[A-Z]{2}\d{4,5}[A-Z]{1,2})\b', text)
    if m:
        return m.group(1)

    # 4. MSI Part Numbers: C13WFO-419MY, B8WH-026MY, E8WGK-036MY, A2WJ-1230MY, B13UC-3456MY
    m = re.search(r'\b([A-Z0-9]{4,6}[-\s][0-9]{3,4}MY)\b', text)
    if m:
        return m.group(1).replace(" ", "-")

    # 5. Acer Part Numbers: A715-59G-501E, PHN16-71-72SS, PHN16-I31-551G, A715-59G-527W
    m = re.search(r'\b([A-Z0-9]{4,6}[-\s][A-Z0-9]{2,4}[-\s][A-Z0-9]{3,6})\b', text)
    if m:
        return m.group(1).replace(" ", "-")

    # 6. Generic model code pattern
    m = re.search(r'\b([A-Z]{2}\d{3}[A-Z]{1,2}[-\s][A-Z0-9]{5,10})\b', text)
    if m:
        return m.group(1).replace(" ", "-")

    return None


def extract_specs_from_title(title, existing_item):
    """
    Intelligently extracts missing CPU, GPU, RAM, Storage, and Display specs 
    from product title or description text if fields were left empty by scrapers.
    """
    text = (title + " " + (existing_item.get("others") or "")).strip()
    
    # 1. Processor (CPU)
    proc = existing_item.get("processor", "").strip()
    if not proc or len(proc) < 3:
        m = re.search(r'\b(Intel®?\s*Core™?\s*(?:Ultra\s*)?[iI\d][\w\d-]+\s*(?:processor)?|AMD\s*Ryzen™?\s*\d[\w\d-]+|Core\s*Ultra\s*\d\s*\d+[\w\d]*|[iI][3579][-\s]\d{4,5}[\w\d]*|Athlon[\w\d\s-]*|C5-\d+[\w\d]*|CU5-\d+[\w\d]*)\b', text, re.IGNORECASE)
        if m:
            proc = m.group(1).strip()

    # 2. Graphics (GPU)
    gfx = existing_item.get("graphics", "").strip()
    if not gfx or len(gfx) < 3:
        m = re.search(r'\b(NVIDIA®?\s*GeForce\s*RTX™?\s*\d{4}\b[\w\d\s]*|RTX\s*\d{4}\b[\w\d\s]*|GTX\s*\d{4}\b[\w\d\s]*|AMD\s*Radeon™?\s*[\w\d\s]*|Intel®?\s*(?:Arc|Graphics|Iris\s*Xe)\b[\w\d\s]*)\b', text, re.IGNORECASE)
        if m:
            gfx = m.group(1).strip()

    # 3. Memory (RAM)
    mem = existing_item.get("memory", "").strip()
    if not mem or len(mem) < 2:
        m_ram = re.search(r'\b([8|12|16|24|32|64]{1,2}\s*GB(?:\s*(?:D5|D4|DDR[45]\w*|LPDDR[45]X?|RAM))?)\b', text, re.IGNORECASE)
        if m_ram:
            mem = m_ram.group(1).strip()

    # 4. Storage (SSD/HDD)
    sto = existing_item.get("storage", "").strip()
    if not sto or len(sto) < 2:
        m_sto = re.search(r'\b((?:128|256|512|1024)\s*GB(?:\s*(?:G[345]|SSD|NVMe|PCIe|Gen\d))?|\d\s*TB(?:\s*(?:G[345]|SSD|NVMe|PCIe|Gen\d))?)\b', text, re.IGNORECASE)
        if m_sto:
            sto = m_sto.group(1).strip()

    # Disambiguate if storage was incorrectly populated with RAM value (e.g. storage = '16GB D5')
    if sto and mem and (sto.lower() == mem.lower() or (re.search(r'^\d{1,2}\s*GB', sto, re.IGNORECASE) and not re.search(r'SSD|NVMe|PCIe|Gen\d|G[345]|M\.2', sto, re.IGNORECASE))):
        sto = ""
        m_sto_fallback = re.search(r'\b((?:256|512|1024)\s*GB|\d\s*TB)\b', text, re.IGNORECASE)
        if m_sto_fallback and m_sto_fallback.group(1).lower() != mem.lower():
            sto = m_sto_fallback.group(1).strip()

    # 5. Display
    disp = existing_item.get("display", "").strip()
    if not disp or len(disp) < 3:
        m = re.search(r'\b(1[34567]\.?[0-6]?"?\s*(?:diagonal)?\s*(?:FHD|WUXGA|QHD\+?|4K|2\.5K|OLED|IPS|144Hz|165Hz|240Hz)?)\b', text, re.IGNORECASE)
        if m:
            disp = m.group(1).strip()

    return {
        "processor": proc,
        "graphics": gfx,
        "memory": mem,
        "storage": sto,
        "display": disp
    }


def clean_vendor_name(series_str, source_file):
    """Normalizes vendor name for deal comparison strings."""
    if "allit" in source_file:
        return "ALL IT"
    if "pcimage" in source_file:
        return "PC Image"
    if "techhypermart" in source_file:
        return "TechHypermart"
    if "acer" in source_file:
        return "Acer Official"
    if "asus" in source_file:
        return "ASUS Official"
    if "lenovo" in source_file:
        return "Lenovo Official"
    if "msi" in source_file:
        return "MSI Official"
    if "hp" in source_file:
        return "HP Official"
    if "dell" in source_file:
        return "Dell Official"
    if "tmt" in source_file:
        return "TMT"
    if "gloo" in source_file:
        return "Gloo"
    if "shopee" in source_file:
        return "Shopee Official"
    return series_str or "Retailer"


def run_scrapers():
    """Runs all individual scraper scripts sequentially in Python."""
    scrapers = [
        ("Acer", "scrapers.acer_scraper", lambda m: m.scrape_acer() if hasattr(m, 'scrape_acer') else None),
        ("ALL IT", "scrapers.allit_scraper", lambda m: m.scrape_allit() if hasattr(m, 'scrape_allit') else None),
        ("ASUS", "scrapers.asus_scraper", lambda m: m.fetch_asus_laptops() if hasattr(m, 'fetch_asus_laptops') else None),
        ("Dell", "scrapers.dell_scraper", lambda m: m.scrape_dell() if hasattr(m, 'scrape_dell') else None),
        ("Gloo", "scrapers.gloo_scraper", lambda m: m.scrape_gloo() if hasattr(m, 'scrape_gloo') else None),
        ("HP", "scrapers.hp_scraper", lambda m: m.scrape_hp() if hasattr(m, 'scrape_hp') else None),
        ("Lenovo", "scrapers.lenovo_scraper", lambda m: m.fetch_all_products("47af9ba7-cab2-4e61-9b10-2283ac14c87c") if hasattr(m, 'fetch_all_products') else None),
        ("MSI", "scrapers.msi_scraper", lambda m: m.scrape_msi() if hasattr(m, 'scrape_msi') else None),
        ("PC Image", "scrapers.pcimage_scraper", lambda m: m.scrape_pcimage() if hasattr(m, 'scrape_pcimage') else None),
        ("Shopee", "scrapers.shopee_scraper", lambda m: m.scrape_shopee() if hasattr(m, 'scrape_shopee') else None),
        ("TechHypermart", "scrapers.techhypermart_scraper", lambda m: m.scrape_techhypermart() if hasattr(m, 'scrape_techhypermart') else None),
        ("TMT", "scrapers.tmt_scraper", lambda m: m.scrape_tmt() if hasattr(m, 'scrape_tmt') else None),
    ]

    for name, module_name, runner in scrapers:
        print(f"Running {name} Scraper ({module_name})...")
        try:
            mod = importlib.import_module(module_name)
            if hasattr(mod, 'OUTPUT_DIR'):
                mod.OUTPUT_DIR = DATA_DIR
                if hasattr(mod, 'OUTPUT_FILE'):
                    mod.OUTPUT_FILE = os.path.join(DATA_DIR, os.path.basename(mod.OUTPUT_FILE))
            res = runner(mod)
            if isinstance(res, list) and hasattr(mod, 'save_to_csv'):
                mod.save_to_csv(res)
            print(f"Finished {name} Scraper")
        except Exception as e:
            print(f"Error executing {name} Scraper ({module_name}): {e}")


def combine_all_csvs():
    """Combines all *_laptops.csv files into master_laptops.csv with vendor price comparison."""
    csv_files = glob.glob(os.path.join(DATA_DIR, "*_laptops.csv"))
    if not csv_files:
        # Fallback check root if data folder empty
        csv_files = glob.glob(os.path.join(MASTER_DIR, "*_laptops.csv"))
    if not csv_files:
        print("No individual scraper CSV files found (*_laptops.csv).")
        return

    all_items = []
    for filepath in csv_files:
        filename = os.path.basename(filepath)
        if filename == "master_laptops.csv":
            continue
        print(f"Reading {filename}...")
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                count = 0
                for row in reader:
                    row["source_file"] = filename
                    all_items.append(row)
                    count += 1
                print(f"  Loaded {count} rows from {filename}")
        except Exception as e:
            print(f"  Error reading {filename}: {e}")

    # Group items by Part Number (MPN) or unique hardware signature
    groups = defaultdict(list)
    for item in all_items:
        title = (item.get("title") or "").strip()
        rid = (item.get("id") or "").strip()
        if not title or not rid or title.lower() in ["untitled model", "untitled"]:
            continue

        # Fill missing specs from title text
        parsed_specs = extract_specs_from_title(title, item)
        for k, v in parsed_specs.items():
            if v and not item.get(k):
                item[k] = v

        mpn = extract_part_number(title, rid)
        if mpn:
            key = mpn
        else:
            # Build unique hardware signature for models sharing base names
            cpu_sig = re.sub(r'\s+', '', (item.get("processor") or "").lower())[:12]
            gpu_sig = re.sub(r'\s+', '', (item.get("graphics") or "").lower())[:10]
            ram_sig = re.sub(r'\s+', '', (item.get("memory") or "").lower())[:6]
            sto_sig = re.sub(r'\s+', '', (item.get("storage") or "").lower())[:6]
            title_clean = re.sub(r'[^a-zA-Z0-9]', '', title.lower())[:25]
            
            key = f"{title_clean}_{cpu_sig}_{gpu_sig}_{ram_sig}_{sto_sig}"

        groups[key].append(item)

    master_rows = []

    for mpn_key, items in groups.items():
        # Parse vendor offers
        offers = []
        for item in items:
            try:
                p_val = float(re.sub(r'[^\d.]', '', item.get("price", "0")))
            except Exception:
                p_val = 0.0

            v_name = clean_vendor_name(item.get("series", ""), item.get("source_file", ""))
            offers.append({
                "vendor": v_name,
                "price": p_val,
                "url": item.get("url", ""),
                "item": item
            })

        # Sort valid offers by price ascending
        valid_offers = [o for o in offers if o["price"] > 0]
        if valid_offers:
            valid_offers.sort(key=lambda x: x["price"])
            best_offer = valid_offers[0]
        else:
            best_offer = offers[0]

        master_item = best_offer["item"].copy()

        # Build vendor price & link comparison strings
        vendor_prices_list = []
        vendor_urls_list = []
        seen_vendors = set()

        for o in valid_offers:
            v_name = o["vendor"]
            if v_name in seen_vendors:
                continue
            seen_vendors.add(v_name)

            vendor_prices_list.append(f"{v_name}: RM {o['price']:,.2f}")
            if o["url"]:
                vendor_urls_list.append(f"{v_name}: {o['url']}")

        # Merge specs (pick most complete non-empty string across vendor offers)
        for field in ["processor", "graphics", "memory", "storage", "display", "wifi", "battery"]:
            best_spec = master_item.get(field, "")
            for o in offers:
                cand = o["item"].get(field, "")
                if len(cand) > len(best_spec):
                    best_spec = cand
            master_item[field] = best_spec

        master_item["id"] = mpn_key
        master_item["price"] = f"{best_offer['price']:.2f}" if best_offer['price'] > 0 else master_item.get("price", "")
        master_item["best_vendor"] = f"{best_offer['vendor']} (RM {best_offer['price']:,.2f})" if best_offer['price'] > 0 else best_offer['vendor']
        master_item["vendor_prices"] = " | ".join(vendor_prices_list) if vendor_prices_list else f"{best_offer['vendor']}: RM {master_item['price']}"
        master_item["vendor_count"] = len(seen_vendors) if seen_vendors else 1
        master_item["url"] = best_offer["url"]
        master_item["vendor_urls"] = " | ".join(vendor_urls_list)

        master_rows.append(master_item)

    with open(MASTER_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(master_rows)

    # Also export as compact JSON for faster frontend loading
    export_json(master_rows)

    multi_count = sum(1 for r in master_rows if r["vendor_count"] > 1)
    print(f"\nSuccessfully combined {len(master_rows)} unique laptops into master_laptops.csv!")
    print(f"  ({multi_count} laptops are available from multiple vendors with price comparisons)")


def export_json(master_rows):
    """Exports master data as compact JSON and data.js for zero-CORS local file:// browser compatibility."""
    import json
    json_file = os.path.join(DATA_DIR, "laptops.json")
    js_file = os.path.join(DATA_DIR, "data.js")
    
    json_rows = []
    for row in master_rows:
        jr = {}
        for field in FIELDNAMES:
            val = row.get(field, "")
            if val is None:
                val = ""
            jr[field] = val
        json_rows.append(jr)

    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(json_rows, f, separators=(",", ":"), ensure_ascii=False)

    with open(js_file, "w", encoding="utf-8") as f:
        f.write("window.preloadedRows = ")
        json.dump(json_rows, f, separators=(",", ":"), ensure_ascii=False)
        f.write(";")

    csv_size = os.path.getsize(MASTER_FILE)
    json_size = os.path.getsize(json_file)
    js_size = os.path.getsize(js_file)
    print(f"  Exported laptops.json ({json_size/1024:.0f}KB) and data.js ({js_size/1024:.0f}KB) for zero-CORS browser loading")


if __name__ == "__main__":
    combine_all_csvs()