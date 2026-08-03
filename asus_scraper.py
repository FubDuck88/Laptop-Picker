import requests
import json
import csv
import time
import os
import re
from bs4 import BeautifulSoup

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "asus_laptops.csv")

BASE_API_URL = "https://odinapi.asus.com/recent-data/apiv2/SeriesFilterResult"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
}


def infer_graphics(cpu_str, title, raw_spec):
    """Fallback integrated graphics inference when summary bullet omits iGPU."""
    text = (cpu_str + " " + title + " " + raw_spec).lower()
    
    # Discrete GPUs
    rtx_m = re.search(r'\b(rtx\s*\d{4}(?:\s*ti)?)\b', text)
    if rtx_m:
        return "NVIDIA GeForce " + rtx_m.group(1).upper()
    gtx_m = re.search(r'\b(gtx\s*\d{4}(?:\s*ti)?)\b', text)
    if gtx_m:
        return "NVIDIA GeForce " + gtx_m.group(1).upper()
    rx_m = re.search(r'\b(radeon\s*rx\s*\d{4}\w*)\b', text)
    if rx_m:
        return "AMD " + rx_m.group(1).title()

    # Integrated GPUs
    if "intel arc" in text or "core ultra" in text:
        return "Intel Arc Graphics"
    if "iris xe" in text:
        return "Intel Iris Xe Graphics"
    if "radeon" in text or "ryzen" in text or "amd" in text:
        return "AMD Radeon Graphics"
    if "snapdragon" in text or "adreno" in text:
        return "Qualcomm Adreno Graphics"
    if "intel" in text or "core" in text:
        return "Intel Integrated Graphics"
    
    return "Integrated Graphics"


def parse_model_spec(html_str):
    """Parses ASUS ModelSpec HTML list into structured spec fields."""
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
    others = []

    for li in soup.find_all("li"):
        text = li.get_text(separator=" ", strip=True)
        text_low = text.lower()

        if any(k in text_low for k in ("intel", "ryzen", "processor", "core ultra")) and not specs["processor"]:
            specs["processor"] = text
        elif any(k in text_low for k in ("geforce", "rtx", "gtx", "radeon", "graphics", "gpu", "arc", "iris xe")) and not specs["graphics"]:
            specs["graphics"] = text
        elif any(k in text_low for k in ('"', "inch", "fhd", "qhd", "wuxga", "wqxga", "4k", "hz", "oled", "ips", "nebula")) and not specs["display"]:
            specs["display"] = text
        elif any(k in text_low for k in ("ssd", "nvme", "pcie", "1tb", "2tb", "512gb")) and not specs["storage"]:
            specs["storage"] = text
        elif any(k in text_low for k in ("ddr4", "ddr5", "lpddr5x", "memory", "ram")) and not specs["memory"]:
            specs["memory"] = text
        elif any(k in text_low for k in ("wi-fi", "wifi", "bluetooth")) and not specs["wifi"]:
            specs["wifi"] = text
        elif any(k in text_low for k in ("whr", "whrs", "cell", "battery")) and not specs["battery"]:
            specs["battery"] = text
        else:
            if len(text) < 100:
                others.append(text)

    specs["others"] = " | ".join(others[:4])
    return specs


def fetch_asus_laptops():
    print("Fetching ASUS Malaysia laptop lineup from OdinAPI...")
    page = 1
    page_size = 50
    all_products = []
    seen_urls = set()

    while True:
        params = {
            "CategoryName": "",
            "PageIndex": page,
            "PageSize": page_size,
            "PriceMax": "",
            "PriceMin": "",
            "ProductLevel1Code": "laptops",
            "ProductLevel2Code": "",
            "SeriesName": "",
            "Sort": "Newsest",
            "Spec": "",
            "SubSeriesName": "",
            "SubSpec": "",
            "SystemCode": "asus",
            "WebsiteCode": "my",
            "siteID": "www",
            "sitelang": ""
        }

        try:
            r = requests.get(BASE_API_URL, headers=HEADERS, params=params, timeout=12)
            r.raise_for_status()
            res = r.json().get("Result", {})
            products = res.get("ProductList", [])
            total_count = res.get("TotalCount", 0)

            print(f"  Page {page}: received {len(products)} products (Total catalog count: {total_count})")
            if not products:
                break

            for p in products:
                raw_name = p.get("Name", "")
                soup = BeautifulSoup(raw_name, "lxml")
                title = soup.get_text(strip=True)
                
                url = p.get("ProductURL") or p.get("ProductCardURL") or ""
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)

                sku = p.get("PartNo") or p.get("SalesModelName") or p.get("ProductID") or p.get("PDWebPath") or ""

                raw_price = p.get("SortPrice") or p.get("Price") or p.get("RegularPrice") or ""
                try:
                    price_val = float(str(raw_price).replace(",", "").strip())
                    price_str = f"{price_val:.2f}"
                except ValueError:
                    price_str = ""

                specs = parse_model_spec(p.get("ModelSpec", ""))
                
                # Extract image URL
                img_list = p.get("ImageList", [])
                img_url = ""
                if img_list and isinstance(img_list, list) and len(img_list) > 0:
                    urls = img_list[0].get("ImageURL", [])
                    if urls and isinstance(urls, list) and len(urls) > 0:
                        img_url = urls[0]
                if not img_url:
                    img_url = p.get("ProductImage", "") or ""
                
                if img_url.startswith("//"):
                    img_url = "https:" + img_url
                elif img_url.startswith("/"):
                    img_url = "https://dlcdnwebimgs.asus.com" + img_url

                # Apply graphics inference fallback if blank
                if not specs["graphics"]:
                    specs["graphics"] = infer_graphics(specs["processor"], title, specs["others"])

                row = {
                    "id": sku,
                    "title": title,
                    "price": price_str,
                    "url": url,
                    "image_url": img_url,
                    "series": "ASUS Official",
                    "processor": specs.get("processor", ""),
                    "graphics": specs.get("graphics", ""),
                    "memory": specs.get("memory", ""),
                    "storage": specs.get("storage", ""),
                    "display": specs.get("display", ""),
                    "wifi": specs.get("wifi", ""),
                    "battery": specs.get("battery", ""),
                    "others": specs.get("others", "")
                }
                all_products.append(row)
                safe_title = title.encode('ascii', 'ignore').decode()
                print(f"    OK: [{sku}] {safe_title} — GPU: {row['graphics']}")

            if len(all_products) >= total_count or len(products) < page_size:
                break

            page += 1
            time.sleep(0.5)

        except Exception as e:
            print(f"  Error on page {page}: {e}")
            break

    print(f"\nSuccessfully scraped {len(all_products)} unique ASUS laptops!")
    return all_products


def save_to_csv(rows):
    if not rows:
        print("No rows to save.")
        return
    fieldnames = ["id", "title", "price", "url", "image_url", "series", "processor", "graphics", "memory", "storage", "display", "wifi", "battery", "others"]
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print(f"Saved {len(rows)} rows to {OUTPUT_FILE}")


if __name__ == "__main__":
    data = fetch_asus_laptops()
    save_to_csv(data)

    # Auto-run master combiner
    try:
        import run_all
        run_all.combine_all_csvs()
    except Exception as e:
        print("Run master combiner manually: python run_all.py")
