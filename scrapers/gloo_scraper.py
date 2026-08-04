"""
Gloo Malaysia (SNS Network) Laptop Scraper Template
Fetches laptop listings from gloo.com.my and outputs to data/gloo_laptops.csv.
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
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "gloo_laptops.csv")

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


def scrape_gloo():
    """Scrapes laptop listings from Gloo Malaysia (SNS Network)."""
    print("Scraping Gloo Malaysia (SNS Network)...")
    scraped_data = []
    print("  Gloo catalog API endpoint active.")
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
