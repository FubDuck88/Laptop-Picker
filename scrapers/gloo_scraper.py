"""
Gloo Malaysia (SNS Network) Laptop Scraper
Fetches live laptop listings from gloo.com.my using Selenium Headless Chrome.
Outputs to data/gloo_laptops.csv.
"""

import os
import sys
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

        soup = BeautifulSoup(driver.page_source, "lxml")
        driver.quit()

        seen = set()
        for a in soup.find_all("a", href=True):
            href = a["href"]
            title = a.get_text(strip=True)
            if not title or len(title) < 8 or title in seen:
                continue

            # Filter for laptop title keywords
            t_low = title.lower()
            if not any(k in t_low for k in ["laptop", "notebook", "vivobook", "zenbook", "ideapad", "thinkpad", "rog", "tuf", "victus", "pavilion", "macbook", "predator", "nitro", "legion", "loq"]):
                continue

            seen.add(title)

            # Price lookup in container
            parent = a.find_parent(["div", "li", "article"])
            price = ""
            img_url = ""
            if parent:
                p_text = parent.get_text()
                p_match = re.search(r"RM\s*([\d,]+(?:\.\d{2})?)", p_text)
                if p_match:
                    price = p_match.group(1).replace(",", "")
                img_el = parent.find("img", src=True) or parent.find("img")
                if img_el:
                    img_url = (img_el.get("data-src") or img_el.get("data-srcset") or img_el.get("srcset") or img_el.get("src") or "").strip()
                    if img_url.startswith("//"):
                        img_url = "https:" + img_url
                    elif img_url.startswith("/"):
                        img_url = "https://www.gloo.com.my" + img_url

            if not href.startswith("http"):
                href = "https://www.gloo.com.my" + href

            # Extract specs from title
            proc = re.search(r'(?:Intel\s+)?(?:Core\s+)?(?:Ultra\s+)?\d?\s*(?:i[3579]|CU\d)[^\s,)]*|Ryzen\s*\d?\s*\d{4}[A-Z]*', title, re.I)
            gpu = re.search(r'(?:GeForce\s+)?(?:RTX|GTX)\s*\d{4}[^\s,)]*|Radeon[^\s,)]*|Intel\s+Graphics', title, re.I)
            ram = re.search(r'\b\d+\s*GB\b(?:\s*DDR[45]|\s*LPDDR\w*)?', title, re.I)
            ssd = re.search(r'\b\d+(?:\.\d+)?\s*(?:TB|GB)\s*(?:SSD|NVMe|PCIe)?', title, re.I)

            gloo_id = ""
            id_m = re.search(r'([A-Z0-9]{5,10})', title)
            if id_m:
                gloo_id = id_m.group(1)
            else:
                gloo_id = f"GLOO-{len(scraped_data)+1}"

            scraped_data.append({
                "id": gloo_id,
                "title": title,
                "price": price,
                "url": href,
                "image_url": img_url,
                "series": "Gloo Official",
                "processor": proc.group(0) if proc else "",
                "graphics": gpu.group(0) if gpu else "",
                "memory": ram.group(0) if ram else "",
                "storage": ssd.group(0) if ssd else "",
                "display": "",
                "wifi": "",
                "battery": "",
                "others": "Gloo SNS Network Official Distributor Warranty"
            })

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
