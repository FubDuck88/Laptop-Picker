import os
import sys
import time
import csv
import traceback

def main():
    print("=" * 70)
    print("        LAPTOP PRICE SCRAPER & MASTER COMPILER TOOL")
    print("=" * 70)
    print(" Starting catalog scrapers for Lenovo, MSI, and ASUS...\n")

    start_time = time.time()

    # 1. Scrape Lenovo
    print(" [1/3] Running Lenovo Scraper...")
    try:
        import lenovo_scraper
        lenovo_data = lenovo_scraper.fetch_all_products("47af9ba7-cab2-4e61-9b10-2283ac14c87c")
        lenovo_scraper.save_to_csv(lenovo_data)
        print(f"   --> Lenovo complete: {len(lenovo_data)} laptops scraped.")
    except Exception as e:
        print(f"   [!] Error scraping Lenovo: {e}")
        traceback.print_exc()

    print("\n" + "-" * 70 + "\n")

    # 2. Scrape MSI
    print(" [2/3] Running MSI Scraper...")
    try:
        import msi_scraper
        msi_data = msi_scraper.scrape_msi()
        msi_scraper.save_to_csv(msi_data)
        print(f"   --> MSI complete: {len(msi_data)} laptops scraped.")
    except Exception as e:
        print(f"   [!] Error scraping MSI: {e}")
        traceback.print_exc()

    print("\n" + "-" * 70 + "\n")

    # 3. Scrape ASUS
    print(" [3/3] Running ASUS Scraper...")
    try:
        import asus_scraper
        asus_data = asus_scraper.fetch_asus_laptops()
        asus_scraper.save_to_csv(asus_data)
        print(f"   --> ASUS complete: {len(asus_data)} laptops scraped.")
    except Exception as e:
        print(f"   [!] Error scraping ASUS: {e}")
        traceback.print_exc()

    print("\n" + "=" * 70)
    print(" [COMPILING] Merging all store CSV files into master_laptops.csv...")
    print("=" * 70)

    try:
        import run_all
        run_all.combine_all_csvs()
    except Exception as e:
        print(f"   [!] Error combining CSV files: {e}")
        traceback.print_exc()

    elapsed = time.time() - start_time
    print(f"\n All tasks finished in {elapsed:.1f} seconds!")
    print(f" Output file: master_laptops.csv in {os.getcwd()}")
    print("=" * 70)
    
    input("\n Press ENTER to exit...")

if __name__ == "__main__":
    main()
