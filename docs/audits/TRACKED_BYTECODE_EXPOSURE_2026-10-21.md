# Tracked bytecode path exposure — 21 October 2026

Inspected all 12 Git-tracked Python 3.14 cache blobs without executing bytecode. Walked nested code filenames and string constants, with a printable-byte cross-check. Ten files contain absolute Windows paths; four expose them in code filenames. One (`test_filter`) contains a Windows user-profile path in a string constant. Exact directory and username strings are intentionally omitted from this public report.

| Tracked file | Absolute path location | User-profile path |
| --- | --- | --- |
| `__pycache__/acer_scraper.cpython-314.pyc` | constant, filename | No |
| `__pycache__/analyze_filters.cpython-314.pyc` | none | No |
| `__pycache__/analyze_specs.cpython-314.pyc` | none | No |
| `__pycache__/asus_scraper.cpython-314.pyc` | constant, filename | No |
| `__pycache__/asus_scraper_template.cpython-314.pyc` | constant | No |
| `__pycache__/inspect_images.cpython-314.pyc` | constant | No |
| `__pycache__/laptop price scapper.cpython-314.pyc` | constant | No |
| `__pycache__/lenovo_scraper.cpython-314.pyc` | constant, filename | No |
| `__pycache__/msi_scraper.cpython-314.pyc` | constant, filename | No |
| `__pycache__/run_all.cpython-314.pyc` | constant | No |
| `__pycache__/scrape_and_compile.cpython-314.pyc` | constant | No |
| `__pycache__/test_filter.cpython-314.pyc` | constant | Yes |

These are inherited tracked artifacts, outside the earlier scan of nine newly added backup files. Remove all caches in 6R and exclude them from Pages. Removing current files does not purge historical commits, clones or cached copies. No history rewrite was performed. This is a path-exposure inspection, not a comprehensive credential audit of the inherited repository.
