"""
Gloo Malaysia (SNS Network) Laptop Scraper
Fetches live laptop listings from gloo.com.my using Selenium Headless Chrome.
Outputs to data/gloo_laptops.csv.
"""

import os
import sys
if __package__ in (None, ""):
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from source_photos import element_photo, photo_url
from source_normalization import title_specs
import csv
import re
import time
from bs4 import BeautifulSoup


def get_base_dir():
    """Returns parent data directory whether running as raw script or frozen PyInstaller EXE."""
    if getattr(sys, "frozen", False):
        return os.path.join(os.path.dirname(sys.executable), "data")
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


OUTPUT_DIR = get_base_dir()
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "gloo_laptops.csv")

FIELDNAMES = [
    "id", "title", "price", "url", "image_url", "series",
    "processor", "graphics", "memory", "storage",
    "display", "wifi", "battery", "others"
]


def extract_products_from_page(html):
    """Only product cards may supply a photo; navigation links are not offers.

    html.parser recovers the product cards from the captured Gloo page markup.
    This legacy extractor does not qualify Gloo for the verified catalog.
    """
    soup = BeautifulSoup(html, "html.parser")
    rows, seen = [], set()
    for card in soup.select(".product-layout"):
        anchor = card.select_one(".product-image-container a[href]") or card.select_one("h4 a[href]")
        if anchor is None:
            continue
        url = photo_url(anchor.get("href"), "https://www.gloo.com.my/")
        image = card.select_one(".product-image-container img") or card.select_one(".image img")
        title = (anchor.get("title") or (image.get("alt") if image else None) or anchor.get_text(" ", strip=True)).strip()
        price = card.select_one(".price-new") or card.select_one(".price")
        match = re.search(r"RM\s*([\d,]+(?:\.\d{2})?)", price.get_text(" ", strip=True)) if price else None
        if not url or not title or not match or url in seen:
            continue
        seen.add(url)
        button = card.select_one("[onclick*='cart.add']")
        identifier = re.search(r"cart\.add\('([^']+)'", button.get("onclick", "")) if button else None
        # Stable URL identity if the vendor's explicit product ID is absent.
        row = dict.fromkeys(FIELDNAMES, "")
        row.update(title_specs(title))
        row.update(id=identifier[1] if identifier else url, title=title,
                   price=match[1].replace(",", ""), url=url,
                   image_url=element_photo(image, url) or "", series="Gloo Official",
                   others="Gloo SNS Network Official Distributor Warranty")
        rows.append(row)
    return rows


def scrape_gloo():
    """Scrapes laptop listings from Gloo Malaysia (SNS Network) via Selenium Headless Chrome."""
    print("Scraping Gloo Malaysia (SNS Network) via Selenium...")
    scraped_data = []

    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options

        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        )

        driver = webdriver.Chrome(options=chrome_options)
        driver.get("https://www.gloo.com.my/laptops")
        time.sleep(6)

        # Scroll down to load all items
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        html = driver.page_source
        driver.quit()
        scraped_data = extract_products_from_page(html)

        print(f"  Scraped {len(scraped_data)} laptops from Gloo Malaysia.")

    except Exception as e:
        print(f"  Error running Gloo Selenium scraper: {e}")

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
    data = scrape_gloo()
    save_to_csv(data)
