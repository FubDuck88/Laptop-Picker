import sys
"""
TechHypermart Notebook Scraper
Uses undetected_chromedriver to bypass Cloudflare protection and fetch notebook listings
from techhypermart.com/notebooks, outputting to techhypermart_laptops.csv.
"""

import os
import re
import csv
import time
from bs4 import BeautifulSoup

try:
    import undetected_chromedriver as uc
    HAS_UC = True
except ImportError:
    HAS_UC = False

OUTPUT_DIR = os.path.join(os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "techhypermart_laptops.csv")

BASE_URL = "https://www.techhypermart.com"
CATEGORY_URL = f"{BASE_URL}/notebooks"


def parse_specs_from_title(title):
    """Parses processor, graphics, memory, storage, and display from TechHypermart title strings."""
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
        r'(?:Intel\s+)?(?:Core\s+)?(?:Ultra\s+)?\d?\s*(?:i[3579]|C[UuA]\d)[^\s,()]*',
        r'Core\s+[^\s,()]+',
        r'R[3579][-\s]\d{3,4}[A-Z]*',
        r'Ryzen\s*\d?\s*\d{4}[A-Z]*',
        r'Athlon[^\s,()]*',
        r'Celeron[^\s,()]*',
    ]
    for pat in proc_pats:
        m = re.search(pat, title, re.IGNORECASE)
        if m:
            specs["processor"] = m.group(0).strip()
            break

    # Memory (RAM)
    m_ram = re.search(r'\b([8|12|16|24|32|64]{1,2}\s*GB(?:\s*(?:D5|D4|DDR[45]\w*|LPDDR[45]X?|RAM))?)\b', title, re.IGNORECASE)
    if m_ram:
        specs["memory"] = m_ram.group(1).strip()

    # Storage (256GB, 512GB, 1TB, 2TB, SSD, NVMe, PCIe, G4, G3)
    m_sto = re.search(r'\b((?:128|256|512|1024)\s*GB(?:\s*(?:G[345]|SSD|NVMe|PCIe|Gen\d))?|\d\s*TB(?:\s*(?:G[345]|SSD|NVMe|PCIe|Gen\d))?)\b', title, re.IGNORECASE)
    if m_sto:
        specs["storage"] = m_sto.group(1).strip()

    # Fix case where storage matched RAM
    if specs["storage"].lower() == specs["memory"].lower() or (re.search(r'^\d{1,2}\s*GB', specs["storage"], re.IGNORECASE) and not re.search(r'SSD|NVMe|PCIe|Gen\d|G[345]|M\.2', specs["storage"], re.IGNORECASE)):
        specs["storage"] = ""
        m_sto_fallback = re.search(r'\b((?:256|512|1024)\s*GB|\d\s*TB)\b', title, re.IGNORECASE)
        if m_sto_fallback and m_sto_fallback.group(1).lower() != specs["memory"].lower():
            specs["storage"] = m_sto_fallback.group(1).strip()

    # Display
    m = re.search(r'(\d+\.?\d*["\u201d]?\s*(?:FHD|QHD|WUXGA|WQXGA|UHD|HD|OLED|IPS)[^\s,()]*(\s*\d+Hz)?)', title, re.IGNORECASE)
    if m:
        specs["display"] = m.group(1).strip()

    # Graphics
    m = re.search(r'((?:NV\s*)?(?:RTX|GTX|GeForce|Radeon|Arc)\s*\d+[^\s,()]*)', title, re.IGNORECASE)
    if m:
        specs["graphics"] = m.group(1).strip()

    return specs


def extract_products_from_page(html_content):
    """Parses OpenCart product layouts from page HTML."""
    soup = BeautifulSoup(html_content, "lxml")
    items = soup.select(".product-layout")
    parsed_rows = []

    for item in items:
        # Title and URL
        img_tag = item.select_one(".product-img img") or item.select_one("a.product-img img") or item.select_one(".image img") or item.select_one("img")
        title = (img_tag.get("alt") or "").strip() if img_tag else ""
        if not title:
            caption_a = item.select_one(".caption h4 a")
            title = caption_a.get_text(strip=True) if caption_a else ""

        link_tag = item.select_one("a.product-img") or item.select_one(".caption h4 a")
        product_url = link_tag.get("href", "").strip() if link_tag else ""

        # Image URL (Check data-src, srcset, src)
        img_url = ""
        if img_tag:
            img_url = (img_tag.get("data-src") or img_tag.get("src") or img_tag.get("srcset") or "").strip()
            if img_url.startswith("//"):
                img_url = "https:" + img_url
            elif img_url.startswith("/"):
                img_url = BASE_URL + img_url
            elif img_url.startswith("image/"):
                img_url = BASE_URL + "/" + img_url

        # Price
        price_el = item.select_one(".price-new") or item.select_one(".price")
        price_raw = price_el.get_text(strip=True) if price_el else ""
        price_clean = re.sub(r'[^\d.]', '', price_raw.split("Ex Tax")[0]) if price_raw else "0"

        # Product ID / SKU
        quickview = item.select_one("[onclick*='quickview']")
        product_id = ""
        if quickview:
            m = re.search(r"quickview\('(\d+)'\)", quickview.get("onclick", ""))
            if m:
                product_id = m.group(1)

        if not product_id and product_url:
            # Fallback to URL slug hash
            product_id = product_url.rstrip("/").split("/")[-1][:30]

        if not title or not product_id:
            continue

        # Series / Brand detection from title
        brand = "TechHypermart"
        for b in ["Acer", "ASUS", "HP", "Lenovo", "MSI", "Dell", "Apple", "Huawei", "Gigabyte", "ROG"]:
            if b.lower() in title.lower():
                brand = f"TechHypermart - {b}"
                break

        specs = parse_specs_from_title(title)

        parsed_rows.append({
            "id": product_id,
            "title": title,
            "price": price_clean,
            "url": product_url,
            "image_url": img_url,
            "series": brand,
            "processor": specs["processor"],
            "graphics": specs["graphics"],
            "memory": specs["memory"],
            "storage": specs["storage"],
            "display": specs["display"],
            "wifi": specs["wifi"],
            "battery": specs["battery"],
            "others": "",
        })

    return parsed_rows, soup


def scrape_techhypermart(max_pages=20):
    """Scrapes laptops from TechHypermart using undetected_chromedriver."""
    if not HAS_UC:
        print("  undetected_chromedriver is not installed. Skipping TechHypermart live scrape.")
        return []

    print("Scraping TechHypermart Notebooks (Cloudflare Bypassed)...")
    options = uc.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    try:
        try:
            driver = uc.Chrome(options=options, version_main=150)
        except Exception:
            driver = uc.Chrome(options=options)
    except Exception as e:
        print(f"  Unable to launch Chrome driver (e.g. headless CI environment): {e}")
        return []

    all_products = []
    seen_ids = set()
    page = 1

    try:
        while page <= max_pages:
            url = f"{CATEGORY_URL}?page={page}"
            print(f"  Fetching page {page}: {url}")

            driver.get(url)
            time.sleep(6 if page == 1 else 3)

            if "Just a moment..." in driver.title:
                print("  Cloudflare challenge detected, waiting up to 10s...")
                for _ in range(10):
                    time.sleep(1)
                    if "Just a moment..." not in driver.title:
                        break

            if "Just a moment..." in driver.title:
                print(f"  Failed to pass Cloudflare on page {page}. Stopping.")
                break

            rows, soup = extract_products_from_page(driver.page_source)
            print(f"  Page {page}: got {len(rows)} products")

            if not rows:
                print(f"  No products found on page {page}. Stopping.")
                break

            new_count = 0
            for r in rows:
                rid = r["id"]
                if rid not in seen_ids:
                    seen_ids.add(rid)
                    all_products.append(r)
                    new_count += 1
                    safe_title = r["title"].encode('ascii', 'ignore').decode()
                    print(f"    OK: [{rid}] {safe_title[:65]} — RM {r['price']}")

            if new_count == 0:
                print("  No new products on this page. Stopping.")
                break

            next_a = soup.find("a", string=">") or soup.find("a", href=re.compile(r"page=" + str(page + 1)))
            if not next_a and page > 1:
                print("  No next page link found. Stopping.")
                break

            page += 1

    finally:
        try:
            driver.quit()
        except Exception:
            pass

    print(f"\nExtracted {len(all_products)} laptops from TechHypermart!")
    return all_products


def save_to_csv(rows):
    """Saves scraped rows to CSV file. Preserves existing CSV if 0 rows returned."""
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
    data = scrape_techhypermart()
    save_to_csv(data)

    # Auto-run master combiner
    try:
        import run_all
        run_all.combine_all_csvs()
    except Exception as e:
        print("Run master combiner manually: python run_all.py")
