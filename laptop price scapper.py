import requests
import json
import csv
import time
import os
from bs4 import BeautifulSoup

LISTING_URL = "https://openapi.lenovo.com/my/en/ofp/search/dlp/product/query/get/_tsc"
SPECS_URL = "https://openapi.lenovo.com/my/en/online/product/getTechSpecs"

OUTPUT_DIR = r"D:\User\docu\Python\Laptop Price Scapper"
REQUEST_DELAY = 1.5
MAX_CONSECUTIVE_ERRORS = 3

# Headlines you specifically want as their own columns.
# Key = exact headline text from Lenovo's JSON, value = your CSV column name.
WANTED_SPECS = {
    "Processor": "processor",
    "Graphics": "graphics",
    "Graphic Card": "graphics",  # some responses use this label instead of "Graphics"
    "Memory": "memory",
    "Storage": "storage",
    "Display": "display",
    "WIFI": "wifi",
    "Battery": "battery",
}

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Referer": "https://www.lenovo.com/my/en/laptops/subseries-results/",
}


def fetch_listing(page_filter_id, page=1, page_size=30, session=None):
    params_obj = {
        "classificationGroupIds": "400001",
        "pageFilterId": page_filter_id,
        "facets": [],
        "page": str(page),
        "pageSize": page_size,
        "groupCode": "",
        "init": True,
        "sorts": ["newest"],
        "version": "v2",
        "enablePreselect": True,
        "seriesCode": "",
    }
    query_params = {
        "pageFilterId": page_filter_id,
        "subSeriesCode": "",
        "loyalty": "false",
        "params": json.dumps(params_obj),
    }
    r = (session or requests).get(LISTING_URL, headers=headers, params=query_params, timeout=10)
    r.raise_for_status()
    return r.json()


def extract_listing_products(raw_json):
    results = []
    for group in raw_json.get("data", {}).get("data", []):
        for p in group.get("products", []):
            results.append({
                "id": p.get("productCode"),
                "title": p.get("productName"),
                "price": p.get("finalPrice"),
            })
    return results


def fetch_tech_specs(product_number, session=None):
    r = (session or requests).get(
        SPECS_URL,
        headers=headers,
        params={"productNumber": product_number},
        timeout=10,
    )
    r.raise_for_status()
    return r.json()


def extract_all_specs(specs_json, wanted):
    """
    Splits every spec in the response into named columns (for headlines
    listed in `wanted`) vs. a combined 'others' string for everything else.
    """
    found = {}
    others = []

    tables = specs_json.get("data", {}).get("tables", [])
    for group in tables:
        for spec in group.get("specs", []):
            headline = (spec.get("headline") or "").strip()
            raw_html = spec.get("text") or ""
            clean_text = BeautifulSoup(raw_html, "lxml").get_text(separator=" ", strip=True)

            if headline in wanted:
                found[wanted[headline]] = clean_text
            elif headline:
                others.append(f"{headline}: {clean_text}")

    found["others"] = " | ".join(others)
    return found


def save_to_csv(rows, filename="lenovo_laptops.csv"):
    if not rows:
        print("No rows to save.")
        return
    filepath = os.path.join(OUTPUT_DIR, filename)

    fixed_cols = ["id", "title", "price"]
    spec_cols = ["processor", "graphics", "memory", "storage", "display", "wifi", "battery", "others"]
    fieldnames = fixed_cols + spec_cols

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print(f"Saved {len(rows)} rows to {filepath}")


if __name__ == "__main__":
    PAGE_FILTER_ID = "24cff72a-5814-4bed-94c8-38d5991d2544"

    session = requests.Session()
    session.headers.update(headers)

    listing = fetch_listing(PAGE_FILTER_ID, session=session)
    products = extract_listing_products(listing)

    rows = []
    consecutive_errors = 0

    for p in products:
        try:
            specs = fetch_tech_specs(p["id"], session=session)
            p.update(extract_all_specs(specs, WANTED_SPECS))
            rows.append(p)
            consecutive_errors = 0
            print(f"OK: {p['title']} — {p.get('processor')}")
        except requests.exceptions.RequestException as e:
            consecutive_errors += 1
            print(f"Failed on {p['id']}: {e} (consecutive errors: {consecutive_errors})")
            if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                print(f"Stopping — {MAX_CONSECUTIVE_ERRORS} consecutive failures.")
                break

        time.sleep(REQUEST_DELAY)

    save_to_csv(rows)