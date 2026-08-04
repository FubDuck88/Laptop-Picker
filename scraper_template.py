"""
Universal Scraper Template for Laptop Picker
Use this template to add new website scrapers (e.g. HP, Dell, TMT, Shopee, etc.).

Instructions:
1. Copy this file to `<brand>_scraper.py` (e.g., `hp_scraper.py`).
2. Implement `fetch_laptops()` to retrieve laptop listings from the website/API.
3. Extract specifications into standard fields (id, title, price, url, image_url, series, processor, graphics, memory, storage, display, wifi, battery, others).
4. Run `python run_all.py` to compile all vendor CSVs into master_laptops.csv and laptops.json.
"""

import os
import sys
import csv
import json
import requests
from bs4 import BeautifulSoup


def get_base_dir():
    """Returns application directory whether running as raw script or frozen PyInstaller EXE."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


OUTPUT_DIR = get_base_dir()
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "brand_laptops.csv")

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
    "Accept": "application/json, text/html, */*",
}


def scrape_brand():
    """Fetches and parses laptop listings from target website."""
    print("Scraping New Brand Laptops...")
    scraped_data = []

    # --- Step 1: Implement site-specific fetching logic here ---
    # Example item structure:
    # item = {
    #     "id": "BRAND-12345",
    #     "title": "Brand Gaming Laptop 15",
    #     "price": "3999.00",
    #     "url": "https://www.example.com/product/12345",
    #     "image_url": "https://www.example.com/images/laptop.jpg",
    #     "series": "Brand Official Store",
    #     "processor": "Intel Core i7-13700H",
    #     "graphics": "NVIDIA GeForce RTX 4060 8GB",
    #     "memory": "16GB DDR5",
    #     "storage": "512GB NVMe SSD",
    #     "display": "15.6\" FHD 144Hz IPS",
    #     "wifi": "Wi-Fi 6",
    #     "battery": "57Wh",
    #     "others": "Windows 11 Home | 2 Years Warranty"
    # }
    # scraped_data.append(item)

    return scraped_data


def save_to_csv(rows, output_path=None):
    """Saves rows to output CSV file."""
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
    data = scrape_brand()
    save_to_csv(data)
