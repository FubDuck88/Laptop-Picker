"""
Laptop Price Scraper & Master Compiler Launcher Tool
Runs all scrapers, compiles master catalog (CSV + JSON), and opens index.html in the default browser.
"""

import os
import sys
import time
import webbrowser
import traceback

import run_all


def main():
    print("=" * 70)
    print("        LAPTOP PRICE SCRAPER & MASTER COMPILER TOOL")
    print("=" * 70)
    print(" Starting catalog scrapers for all vendors...\n")

    start_time = time.time()

    # 1. Run all vendor scrapers
    try:
        run_all.run_scrapers()
    except Exception as e:
        print(f" [!] Error during scraping run: {e}")
        traceback.print_exc()

    print("\n" + "=" * 70)
    print(" [COMPILING] Merging store CSVs into master_laptops.csv & laptops.json...")
    print("=" * 70)

    # 2. Combine CSVs and export JSON
    try:
        run_all.combine_all_csvs()
    except Exception as e:
        print(f" [!] Error combining catalog files: {e}")
        traceback.print_exc()

    elapsed = time.time() - start_time
    print(f"\n All scraping and compilation tasks finished in {elapsed:.1f} seconds!")

    # 3. Open index.html in default browser with JSON/CSV ready
    html_path = os.path.abspath(os.path.join(run_all.MASTER_DIR, "index.html"))
    if os.path.exists(html_path):
        url = "file:///" + html_path.replace("\\", "/")
        print(f" Launching web application: {url}")
        webbrowser.open(url)
    else:
        print(" [!] index.html not found in working directory.")

    print("=" * 70)
    input("\n Press ENTER to exit...")


if __name__ == "__main__":
    main()
