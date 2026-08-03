import requests
import json
import csv
import time
import os
from bs4 import BeautifulSoup

LISTING_URL = "https://openapi.lenovo.com/my/en/ofp/search/dlp/product/query/get/_tsc"
SPECS_URL = "https://openapi.lenovo.com/my/en/online/product/getTechSpecs"
SITE_DOMAIN = "https://www.lenovo.com"

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
REQUEST_DELAY = 0.5
MAX_CONSECUTIVE_ERRORS = 3

# Strict non-laptop exclusion rules
EXCLUDE_KEYWORDS = (
    "monitor", "desktop", "tower", "tiny", "all-in-one", "aio",
    "mouse", "keyboard", "headset", "dock", "backpack", "bag", 
    "charger", "power supply", "adapter"
)

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.lenovo.com/",
    "Origin": "https://www.lenovo.com",
}


def build_url(raw_url, title):
    """Turns a relative/absolute Lenovo URL into a full MY/EN localized link."""
    LOCALE_PREFIX = "/my/en"
    if raw_url:
        if raw_url.startswith("http"):
            from urllib.parse import urlparse, urlunparse
            parsed = urlparse(raw_url)
            path = parsed.path
            if not path.startswith(LOCALE_PREFIX):
                import re as _re
                path = _re.sub(r'^/[a-z]{2}/[a-z]{2}/', LOCALE_PREFIX + '/', path)
                if not path.startswith(LOCALE_PREFIX):
                    path = LOCALE_PREFIX + path
            return urlunparse(parsed._replace(path=path))
        path = raw_url if raw_url.startswith('/') else '/' + raw_url
        if not path.startswith(LOCALE_PREFIX):
            path = LOCALE_PREFIX + path
        return SITE_DOMAIN + path
    query = (title or "").replace(" ", "+")
    return f"{SITE_DOMAIN}{LOCALE_PREFIX}/search?text={query}"


def fetch_listing(page_filter_id, page=1, page_size=50, session=None):
    params_obj = {
        "classificationGroupIds": "400001",
        "pageFilterId": page_filter_id,
        "facets": [],
        "page": str(page),
        "pageSize": page_size,
        "groupCode": "",
        "init": False,
        "sorts": ["Recommended", "shippingDate"],
        "version": "v2",
        "enablePreselect": True,
        "subseriesCode": "",
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


def parse_classification(cls_list):
    """Extracts standard spec fields from product.classification array."""
    specs = {}
    if not cls_list:
        return specs
    for item in cls_list:
        k = item.get("a")
        v = item.get("b")
        if k and v:
            specs[k.strip()] = v.strip()
    return specs


def fetch_all_products(page_filter_id, page_size=50, session=None):
    """Fetches all pages for a given pageFilterId and parses rich classification specs."""
    all_products = []
    page = 1
    while True:
        data = fetch_listing(page_filter_id, page=page, page_size=page_size, session=session)
        meta = data.get("data", {})
        page_count = meta.get("pageCount", 1)
        
        page_products = []
        for group in meta.get("data", []):
            for p in group.get("products", []):
                cls = parse_classification(p.get("classification", []))
                
                title = (p.get("summary") or p.get("productName") or "").strip()
                code = (p.get("productCode") or p.get("id") or "").strip()
                
                # Skip empty/invalid items without title or ID
                if not title or not code:
                    continue

                # Exclude non-laptop accessories or desktops if any
                if any(k in title.lower() for k in EXCLUDE_KEYWORDS):
                    continue

                price = p.get("finalPrice") or p.get("instantSavingPrice") or p.get("webPrice") or ""
                p_url = build_url(p.get("url"), title)
                
                # Extract image URL
                media = p.get("media", {})
                gallery = media.get("gallery", [])
                img_url = ""
                if gallery and isinstance(gallery, list) and len(gallery) > 0:
                    img_url = gallery[0].get("imageAddress", "")
                if not img_url:
                    img_url = media.get("productImage", "") or p.get("smallImage", "") or ""
                
                if img_url.startswith("//"):
                    img_url = "https:" + img_url
                elif img_url.startswith("/"):
                    img_url = "https://p3-ofp.static.pub" + img_url

                os_str = cls.get("Operating System", "")
                warr_str = cls.get("Warranty", "")
                card_sum = p.get("cardSummary", "")
                others_parts = []
                if os_str: others_parts.append(f"OS: {os_str}")
                if warr_str: others_parts.append(f"Warranty: {warr_str}")
                if card_sum: others_parts.append(card_sum)
                
                prod_dict = {
                    "id": code,
                    "title": title,
                    "price": price,
                    "url": p_url,
                    "image_url": img_url,
                    "series": "Lenovo Official",
                    "processor": cls.get("Processor", ""),
                    "graphics": cls.get("Graphic Card") or cls.get("Graphics", ""),
                    "memory": cls.get("Memory", ""),
                    "storage": cls.get("Storage", ""),
                    "display": cls.get("Display", ""),
                    "wifi": "",
                    "battery": "",
                    "others": " | ".join(others_parts),
                }
                page_products.append(prod_dict)
                
        all_products.extend(page_products)
        print(f"    Page {page}/{page_count} — got {len(page_products)} products")
        if page >= page_count:
            break
        page += 1
        time.sleep(REQUEST_DELAY)
    return all_products


def fetch_tech_specs(product_number, session=None):
    r = (session or requests).get(
        SPECS_URL,
        headers=headers,
        params={"productNumber": product_number},
        timeout=10,
    )
    r.raise_for_status()
    return r.json()


def save_to_csv(rows, filename="lenovo_laptops.csv"):
    if not rows:
        print("No rows to save.")
        return
    filepath = os.path.join(OUTPUT_DIR, filename)

    fixed_cols = ["id", "title", "price", "url", "image_url", "series"]
    spec_cols = ["processor", "graphics", "memory", "storage", "display", "wifi", "battery", "others"]
    fieldnames = fixed_cols + spec_cols

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print(f"Saved {len(rows)} rows to {filepath}")


if __name__ == "__main__":
    SERIES = {
        "All Laptops": "47af9ba7-cab2-4e61-9b10-2283ac14c87c",
        # You can add specific series pageFilterIds here if needed:
        # "IdeaPad 5": "24cff72a-5814-4bed-94c8-38d5991d2544",
    }

    session = requests.Session()
    session.headers.update(headers)

    all_rows = []
    seen_ids = set()

    for series_name, page_filter_id in SERIES.items():
        print(f"\n{'='*60}")
        print(f"Scraping series: {series_name}  (filter={page_filter_id})")
        print(f"{'='*60}")

        try:
            products = fetch_all_products(page_filter_id, session=session)
        except Exception as e:
            print(f"  Could not fetch listing for '{series_name}': {e}")
            continue

        print(f"  Found {len(products)} products total for {series_name}")

        for p in products:
            if not p["id"] or p["id"] in seen_ids:
                continue

            # Fallback to secondary tech specs endpoint if primary classification specs are missing
            if not p.get("processor") and not p.get("graphics"):
                try:
                    specs = fetch_tech_specs(p["id"], session=session)
                    tables = specs.get("data", {}).get("tables", [])
                    for group in tables:
                        for spec in group.get("specs", []):
                            headline = (spec.get("headline") or "").strip()
                            raw_html = spec.get("text") or ""
                            clean_text = BeautifulSoup(raw_html, "lxml").get_text(separator=" ", strip=True)
                            if headline == "Processor": p["processor"] = clean_text
                            elif headline in ("Graphics", "Graphic Card"): p["graphics"] = clean_text
                            elif headline == "Memory": p["memory"] = clean_text
                            elif headline == "Storage": p["storage"] = clean_text
                            elif headline == "Display": p["display"] = clean_text
                            elif headline == "WIFI": p["wifi"] = clean_text
                            elif headline == "Battery": p["battery"] = clean_text
                except Exception as e:
                    print(f"  Fallback tech specs failed for {p['id']}: {e}")

            p["series"] = series_name
            all_rows.append(p)
            seen_ids.add(p["id"])
            safe_title = p['title'].encode('ascii', 'ignore').decode()
            print(f"  OK: [{p['id']}] {safe_title} — RM {p['price']}")

    print(f"\nTotal scraped: {len(all_rows)} unique products across {len(SERIES)} series")
    save_to_csv(all_rows)

    # Auto-run master combiner
    try:
        import run_all
        run_all.combine_all_csvs()
    except Exception as e:
        print("Run master combiner manually: python run_all.py")
