"""Collect qualified sources into a candidate catalog, without publishing website data."""

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT))

from catalog_v2 import CatalogValidationError, build_catalog, write_catalog
from source_adapters import SOURCE_IDS, collect_sources, match_catalog


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources", nargs="+", choices=SOURCE_IDS, default=["allit"])
    parser.add_argument("--output-dir", type=Path, default=ROOT / "data" / "candidates")
    args = parser.parse_args(argv)
    try:
        results = collect_sources(args.sources)
        build = match_catalog(build_catalog(results))
        write_catalog(build, args.output_dir)
        for report in build.catalog["run_reports"]:
            print(f"{report['source_id']}: {report['status']}; "
                  f"{report['accepted_count']} accepted, {report['rejected_count']} rejected")
        print(f"Candidate files: {args.output_dir.resolve()}")
        return 0 if build.catalog["offers"] and all(result.status == "complete" for result in results) else 1
    except (CatalogValidationError, ValueError, OSError) as error:
        print(f"Collection error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
