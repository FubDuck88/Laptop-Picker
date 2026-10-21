# Laptop Picker

A Malaysian laptop comparison project with source-backed configurations, seller offers and observed prices. Buyers purchase directly from the seller.

## Current work

The verified catalog is live. Phase 6R implementation and cutover checks pass; full closure awaits the first successful scheduled publication, nominally 22 October 2026 at 08:00 MYT. The recorded snapshot contains 22 ALL IT configurations; other sellers remain unqualified. Parsed fields are not automatically human-reviewed. Phase 7A has an isolated design study; phase 7B implementation/release gates are in the [phase plan](docs/IMPLEMENTATION_PHASES.md).

See [6R evidence](docs/PHASE6R_IMPLEMENTATION.md), [the product/design plan](docs/DESIGN_OVERHAUL_PLAN.md), and [7A preview notes](docs/PHASE7A_DESIGN.md).

## Local collection and checks

Use Python 3.10 or later (CI uses 3.14), Node 22 or later, and install the test/runtime dependencies:

```sh
python -m pip install -r requirements-test.txt
python -B tools/check.py
python -B tools/run_daily.py --sources allit
python -B tools/run_daily.py --validate
python -m http.server 8000
```

Open localhost port 8000 in a browser. Integrity checking requires HTTP/HTTPS. `ScrapeLaptops.bat` runs the same verified collector/validator and propagates failures. The obsolete executable is removed.

Optional Chromium checks require Playwright and its browser runtime:

```sh
python -m pip install playwright
python -m playwright install chromium
python -B tools/browser_smoke.py --output-dir artifacts/browser
```

## Releases and hosting

The browser loads `data/current.json`, verifies its immutable release SHA-256 and recalculates freshness. Unknown values stay unknown; prices become stale after 48 hours and expire after seven days. System RAM and VRAM are separate fields. History contains actual offer observations only.

Repository data is the seed/development snapshot. The hosted active pointer is on Pages; the authoritative hosted archive pins and operation outcomes are on the `codex/deployment-state` branch. Exact recovery archives are durable GitHub Release assets. Generated diagnostics and captured raw responses belong under ignored `artifacts/`, never the Pages artifact.

The checked Pages workflow stages a candidate under its own data root while retaining the previous public root, verifies it, then deploys a separately checked public artifact. Failed publication retains/restores the known-good archive. Notification and scheduled-proof gates prevent treating a manual dispatch as the first unattended run. The static design preview is excluded from the runtime package.
