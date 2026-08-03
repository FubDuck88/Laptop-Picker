import os
import glob
import csv
import subprocess

# Use current working directory dynamically so it works on both Windows and GitHub Linux runners
MASTER_DIR = os.path.dirname(os.path.abspath(__file__))
MASTER_FILE = os.path.join(MASTER_DIR, "master_laptops.csv")

FIELDNAMES = [
    "id", "title", "price", "url", "image_url", "series",
    "processor", "graphics", "memory", "storage",
    "display", "wifi", "battery", "others"
]

def run_scrapers():
    """Runs all individual scraper scripts sequentially."""
    scraper_scripts = ["acer_scraper.py", "allit_scraper.py", "asus_scraper.py", "lenovo_scraper.py", "msi_scraper.py", "pcimage_scraper.py", "techhypermart_scraper.py"]
    
    for script in scraper_scripts:
        script_path = os.path.join(MASTER_DIR, script)
        if os.path.exists(script_path):
            print(f"Running {script}...")
            try:
                subprocess.run(["python", script_path], check=True)
                print(f"Finished {script}")
            except subprocess.CalledProcessError as e:
                print(f"Error executing {script}: {e}")
        else:
            print(f"Skipping {script} (file not found)")

def combine_all_csvs():
    csv_files = glob.glob(os.path.join(MASTER_DIR, "*_laptops.csv"))
    if not csv_files:
        print("No individual scraper CSV files found (*_laptops.csv).")
        return
        
    master_rows = []
    seen_ids = set()
    
    for filepath in csv_files:
        filename = os.path.basename(filepath)
        if filename == "master_laptops.csv":
            continue
        print(f"Reading {filename}...")
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                count = 0
                for row in reader:
                    title = (row.get('title') or '').strip()
                    rid = (row.get('id') or '').strip()
                    if not title or not rid or title.lower() == 'untitled model':
                        continue
                    unique_key = f"{row.get('series', '')}_{rid}"
                    if unique_key in seen_ids:
                        continue
                    seen_ids.add(unique_key)
                    master_rows.append(row)
                    count += 1
                print(f"  Loaded {count} rows from {filename}")
        except Exception as e:
            print(f"  Error reading {filename}: {e}")

    with open(MASTER_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(master_rows)

    print(f"\nSuccessfully combined {len(master_rows)} laptops into master_laptops.csv!")

if __name__ == "__main__":
    run_scrapers()
    combine_all_csvs()