"""Build the diagnostic-only v2 legacy import, or validate an existing v2 catalog."""

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT))

from catalog_v2 import CatalogValidationError, build_legacy_catalog, validate_catalog, write_catalog


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--data-dir", type=Path, default=None, help="Source/output directory (default: project data/)")
    group.add_argument("--validate", type=Path, help="Validate a catalog without writing anything")
    args = parser.parse_args()
    try:
        if args.validate:
            catalog = json.loads(args.validate.read_text(encoding="utf-8"))
            validate_catalog(catalog)
            print(f"Valid catalog v2: {len(catalog['offers'])} offers")
        else:
            directory = args.data_dir or ROOT / "data"
            if not directory.is_dir():
                parser.error("The data directory must already exist")
            paths = [path for path in directory.glob("*_laptops.csv") if path.name != "master_laptops.csv"]
            if not paths:
                parser.error("No source CSV files found; no output written")
            build = build_legacy_catalog(paths)
            write_catalog(build, directory)
            count = sum(report["rejected_count"] for report in build.catalog["run_reports"])
            print(f"Wrote catalog.v2.json and catalog.v2.diagnostics.json: {count} unverified legacy rows, no certified offers")
            if any(report["status"] == "failed" for report in build.catalog["run_reports"]):
                print("One or more input files could not be read; see run_reports.", file=sys.stderr)
                return 1
    except (CatalogValidationError, ValueError, OSError) as error:
        print(f"Catalog error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
