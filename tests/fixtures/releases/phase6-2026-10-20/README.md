# Frozen Phase 6 catalog fixture

Historical public seller evidence from the local 20 October 2026 release. This is test data, not a fresh price check or operational validation receipt.

- Release SHA-256: `116059d4de1016c9ceba960b43fa8d827a598bdcd8d17a75caef1ddc45620268`.
- Release format: **1**; catalog schema: **2**. The exact catalog JSON Schema is copied here and its hash is recorded in `manifest.json`.
- `clock.json` fixes time at `2026-10-20T16:00:00Z` (21 October 00:00 MYT). Apply this clock before loading application scripts; preserve all real observation timestamps.
- `current.json` and `releases/` are byte-for-byte copies from the named local release. They can be served by test routing through the ordinary hash-checked reader. No live seller requests are needed.
- The local `.gitattributes` disables line-ending conversion in this folder so checkout cannot invalidate recorded hashes.
- `manifest.json` records counts, schema version/hashes, provenance and deterministic zero/one-result scenarios. No exact Ryzen CPU or RM4,500 budget is asserted as a user choice.

## Compatibility contract

Keep this fixture immutable. Any later schema/reader change must explicitly retain a version-1/schema-2 read path or provide a tested compatibility adapter outside this folder. Do not overwrite the old payload or its hash to make a new validator pass. Add a separately versioned fixture for new formats and verify both intended compatibility and intentional rejection cases.

The schema snapshot describes the catalog. Release/history invariants remain the responsibility of the versioned release validator; a schema version alone does not guarantee compatibility. Wire the frozen-clock scenarios into the unified UI suite in 7B and run them after any 6R/7C parser or reader change. Fixture metadata and bytes must be included in the 7F implementation fingerprint before its gate starts; the current implementation digest does not recursively include test JSON files.

Exclude this folder from the production Pages artifact. Source repository storage is intentional; production deployment must use an allowlist. No new production data or observation timestamps were generated when creating the fixture.
