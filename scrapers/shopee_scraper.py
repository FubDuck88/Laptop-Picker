"""
Shopee Official Mall Laptop Scraper Template
Fetches laptop listings from Shopee Malaysia Official Brand Malls and outputs to data/shopee_laptops.csv.
Built using Playwright to handle session state and fetch JSON data directly from Shopee's search API.
"""

import os
import sys
import csv
from playwright.sync_api import sync_playwright


def get_base_dir():
    """Returns parent data directory whether running as raw script or frozen PyInstaller EXE."""
    if getattr(sys, "frozen", False):
        return os.path.join(os.path.dirname(sys.executable), "data")
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


OUTPUT_DIR = get_base_dir()
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "shopee_laptops.csv")

FIELDNAMES = [
    "id", "title", "price", "url", "image_url", "series",
    "processor", "graphics", "memory", "storage",
    "display", "wifi", "battery", "others"
]


def scrape_shopee():
    """Scrapes laptop listings from Shopee using Playwright and its search API."""
    print("Scraping Shopee Official Brand Outlets using Playwright...")
    scraped_data = []

    with sync_playwright() as p:
        # Launch browser (headless=False lets you handle any initial login/captcha once)
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 800}
        )
        page = context.new_page()

        try:
            # Go to Shopee main page first to establish valid cookies and session state
            page.goto("https://shopee.com.my/", timeout=60000)
            print("  Please log in or clear any verification prompts in the browser window if needed...")
            page.wait_for_timeout(1000000) # Give yourself 10 seconds to look or handle prompts

            # Hit Shopee's internal JSON search API endpoint directly inside the authenticated session
            api_url = (
                "https://shopee.com.my/api/v4/search/search_items?"
                "by=relevancy&keyword=laptop&limit=60&newest=0&order=desc&"
                "page_type=search&scenario=PAGE_GLOBAL_SEARCH&source=SRP&version=2"
            )
            print("  Fetching laptop data from Shopee API...")
            response = page.goto(api_url, timeout=30000)
            
            data = response.json()
            items = data.get("items", [])
            print(f"  Successfully fetched {len(items)} items from Shopee API!")
            
            for idx, item in enumerate(items):
                item_basic = item.get("item_basic", {})
                title = item_basic.get("name", "")
                
                # Shopee API returns price in cents, divide by 100 for actual currency value
                price_raw = item_basic.get("price", 0)
                price = price_raw / 100.0 if price_raw else 0.0
                
                item_id = item_basic.get("itemid", "")
                shop_id = item_basic.get("shopid", "")
                url = f"https://shopee.com.my/product/{shop_id}/{item_id}" if shop_id and item_id else ""
                
                scraped_data.append({
                    "id": f"shopee_{idx}",
                    "title": title,
                    "price": f"{price:.2f}",
                    "url": url,
                    "image_url": "",
                    "series": "Shopee Mall",
                    "processor": "",
                    "graphics": "",
                    "memory": "",
                    "storage": "",
                    "display": "",
                    "wifi": "",
                    "battery": "",
                    "others": ""
                })
        except Exception as e:
            print(f"  Failed to fetch or parse API: {e}")
        finally:
            browser.close()

    print(f"  Successfully scraped {len(scraped_data)} items from Shopee.")
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
    data = scrape_shopee()
    save_to_csv(data)