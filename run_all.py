import os
import glob
import csv

MASTER_DIR = r"D:\User\docu\Python\Laptop Price Scapper"
MASTER_FILE = os.path.join(MASTER_DIR, "master_laptops.csv")

FIELDNAMES = [
    "id", "title", "price", "url", "image_url", "series",
    "processor", "graphics", "memory", "storage",
    "display", "wifi", "battery", "others"
]

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

    print(f"\nSuccessfully combined {len(master_rows)} laptops from {len(csv_files)} files into master_laptops.csv!")

if __name__ == "__main__":
    combine_all_csvs()
