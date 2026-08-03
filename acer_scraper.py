"""
Acer Malaysia Laptop Scraper
Fetches laptop listings from Acer's catalog API and outputs to acer_laptops.csv.
"""

import requests
import json
import csv
import os
import time
from bs4 import BeautifulSoup

OUTPUT_DIR = r"D:\User\docu\Python\Laptop Price Scapper"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "acer_laptops.csv")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://store.acer.com/en-my/",
}

# Example GraphQL Query for Acer Magento Store
GRAPHQL_URL = "https://store.acer.com/en-my/graphql"
GRAPHQL_QUERY = """
query GetAcerLaptops($currentPage: Int!, $pageSize: Int!) {
  products(
    filter: { category_id: { eq: "laptops" } }
    currentPage: $currentPage
    pageSize: $pageSize
  ) {
    total_count
    items {
      sku
      name
      url_key
      price_range {
        minimum_price {
          final_price {
            value
            currency
          }
        }
      }
      short_description {
        html
      }
    }
  }
}
"""

def parse_acer_specs(html_str):
    """Parses Acer short description HTML into structured specs."""
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
    if not html_str:
        return specs
        
    soup = BeautifulSoup(html_str, "lxml")
    for li in soup.find_all(["li", "p"]):
        t = li.get_text(separator=" ", strip=True)
        t_low = t.lower()
        if any(k in t_low for k in ("intel", "ryzen", "processor", "core ultra")) and not specs["processor"]:
            specs["processor"] = t
        elif any(k in t_low for k in ("geforce", "rtx", "radeon", "graphics", "gpu", "arc")) and not specs["graphics"]:
            specs["graphics"] = t
        elif any(k in t_low for k in ('"', "inch", "fhd", "qhd", "wuxga", "144hz", "oled", "ips")) and not specs["display"]:
            specs["display"] = t
        elif any(k in t_low for k in ("ssd", "nvme", "pcie", "1tb", "512gb")) and not specs["storage"]:
            specs["storage"] = t
        elif any(k in t_low for k in ("ddr4", "ddr5", "memory", "ram")) and not specs["memory"]:
            specs["memory"] = t
            
    return specs

def scrape_acer():
    print("Scraping Acer Malaysia laptops...")
    scraped_rows = []
    
    # 1. Query GraphQL / REST API
    page = 1
    while True:
        payload = {
            "query": GRAPHQL_QUERY,
            "variables": {"currentPage": page, "pageSize": 30}
        }
        try:
            r = requests.post(GRAPHQL_URL, json=payload, headers=HEADERS, timeout=10)
            if r.status_code != 200:
                print(f"  Page {page} status: {r.status_code}")
                break
            
            data = r.json()
            products_data = data.get("data", {}).get("products", {})
            items = products_data.get("items", [])
            total = products_data.get("total_count", 0)
            
            print(f"  Page {page}: got {len(items)} items (Total: {total})")
            if not items:
                break
                
            for item in items:
                sku = item.get("sku", "")
                name = item.get("name", "")
                price_val = item.get("price_range", {}).get("minimum_price", {}).get("final_price", {}).get("value", "")
                url_key = item.get("url_key", "")
                url = f"https://store.acer.com/en-my/{url_key}.html" if url_key else "https://store.acer.com/en-my/"
                
                short_desc = item.get("short_description", {}).get("html", "")
                specs = parse_acer_specs(short_desc)
                
                scraped_rows.append({
                    "id": sku,
                    "title": name,
                    "price": str(price_val),
                    "url": url,
                    "series": "Acer Official",
                    "processor": specs["processor"],
                    "graphics": specs["graphics"],
                    "memory": specs["memory"],
                    "storage": specs["storage"],
                    "display": specs["display"],
                    "wifi": specs["wifi"],
                    "battery": specs["battery"],
                    "others": ""
                })
                
            if len(scraped_rows) >= total or len(items) < 30:
                break
            page += 1
            time.sleep(1)
        except Exception as e:
            print(f"  Error on page {page}: {e}")
            break
            
    return scraped_rows

def save_to_csv(rows):
    if not rows:
        print("No rows to save.")
        return
    fieldnames = ["id", "title", "price", "url", "series", "processor", "graphics", "memory", "storage", "display", "wifi", "battery", "others"]
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print(f"Saved {len(rows)} rows to {OUTPUT_FILE}")

if __name__ == "__main__":
    data = scrape_acer()
    save_to_csv(data)
    
    # Auto-run master combiner
    try:
        import run_all
        run_all.combine_all_csvs()
    except Exception as e:
        print("Run master combiner manually: python run_all.py")
