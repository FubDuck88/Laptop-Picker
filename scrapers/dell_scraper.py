"""
Dell Official Store Malaysia Laptop Scraper
Fetches laptop listings from dell.com/en-my/shop/laptops/sr/laptops and outputs to data/dell_laptops.csv.
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
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "dell_laptops.csv")

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


def scrape_dell():
    """Scrapes laptop listings from Dell Official Store Malaysia."""
    print("Scraping Dell Official Store Malaysia...")
    session = requests.Session()
    session.headers.update(HEADERS)

    url = "https://www.dell.com/en-my/shop/laptops/sr/laptops"
    scraped_data = []

    try:
        r = session.get(url, timeout=15)
        if r.status_code != 200:
            print(f"  HTTP {r.status_code} fetching Dell catalog.")
            return scraped_data

        soup = BeautifulSoup(r.text, "lxml")
        articles = soup.find_all(["article", "div"], class_=re.compile(r"ps-stack|stack|product-item|grid-item"))

        # Fallback search for product cards
        if not articles:
            articles = soup.find_all("div", attrs={"data-dell-product": True})

        # Process all product elements found
        card_elements = soup.select("article, .ps-stack, [class*='product-stack'], [class*='ps-title']")
        seen_titles = set()

        for card in card_elements:
            title_el = card.find(["h2", "h3", "a"], class_=re.compile(r"title|heading|ps-title"))
            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            if not title or title.lower() in ["welcome", "filters", "shopping cart"] or len(title) < 4:
                continue

            if title in seen_titles:
                continue
            seen_titles.add(title)

            # Link
            link = ""
            if title_el.name == "a" and "href" in title_el.attrs:
                link = title_el["href"]
            else:
                a_tag = card.find("a", href=True)
                if a_tag:
                    link = a_tag["href"]

            if link and not link.startswith("http"):
                link = "https://www.dell.com" + link

            # Price
            price = ""
            price_el = card.find(class_=re.compile(r"price|amount"))
            if price_el:
                p_match = re.search(r"RM\s*([\d,]+(?:\.\d{2})?)", price_el.get_text())
                if p_match:
                    price = p_match.group(1).replace(",", "")

            # Image
            img_url = ""
            img_el = card.find("img", src=True)
            if img_el:
                img_url = img_el["src"]
                if img_url.startswith("//"):
                    img_url = "https:" + img_url

            # Extract specs from card text
            card_text = card.get_text(separator=" ", strip=True)
            proc = re.search(r'(?:Intel\s+)?(?:Core\s+)?(?:Ultra\s+)?\d?\s*(?:i[3579]|CU\d)[^\s,)]*|Ryzen\s*\d?\s*\d{4}[A-Z]*', card_text, re.I)
            gpu = re.search(r'(?:GeForce\s+)?(?:RTX|GTX)\s*\d{4}[^\s,)]*|Radeon[^\s,)]*|Intel\s+Graphics', card_text, re.I)
            ram = re.search(r'\b\d+\s*GB\b(?:\s*DDR[45]|\s*LPDDR\w*)?', card_text, re.I)
            ssd = re.search(r'\b\d+(?:\.\d+)?\s*(?:TB|GB)\s*(?:SSD|NVMe|PCIe)?', card_text, re.I)
            disp = re.search(r'\d{2}(?:\.\d)?["\s]*(?:FHD|QHD|OLED|2\.8K|3K|4K|WUXGA|IPS)[^\s,)]*', card_text, re.I)

            # Dell Part ID
            dell_id = ""
            id_match = re.search(r'\b([A-Z0-9]{4,10})\b', link)
            if id_match:
                dell_id = id_match.group(1).upper()
            else:
                dell_id = "DELL-" + str(len(scraped_data) + 1)

            scraped_data.append({
                "id": dell_id,
                "title": title,
                "price": price,
                "url": link or "https://www.dell.com/en-my/shop/laptops/sr/laptops",
                "image_url": img_url,
                "series": "Dell Official",
                "processor": proc.group(0) if proc else "",
                "graphics": gpu.group(0) if gpu else "",
                "memory": ram.group(0) if ram else "",
                "storage": ssd.group(0) if ssd else "",
                "display": disp.group(0) if disp else "",
                "wifi": "",
                "battery": "",
                "others": "Windows 11 Home | Dell Official Store Warranty"
            })

        print(f"  Scraped {len(scraped_data)} laptops from Dell Official Store.")

    except Exception as e:
        print(f"  Error scraping Dell: {e}")

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
    data = scrape_dell()
    save_to_csv(data)
