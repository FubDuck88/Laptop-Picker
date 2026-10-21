"""Variant-safe adapters, conservative matching, and real captured source examples."""

from copy import deepcopy
from datetime import datetime
import json
import tempfile
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

import requests

from catalog_v2 import SourceResult, build_catalog, validate_catalog
from source_adapters import allit_records, collect_allit, collect_sources, legacy_shopify_rows, match_catalog, new_condition_proof
from source_normalization import capacity, cpu_model, display_spec, manufacturer_part_number, title_specs
from test_catalog_v2 import GENERATED, record, source


FIXTURES = Path(__file__).parent / "fixtures"
OBSERVED = "2026-10-20T00:15:00Z"
CONDITION_HTML = '<script type="application/ld+json">{"@type":"Product","offers":[{"@type":"Offer","itemCondition":"https://schema.org/NewCondition"}]}</script>'
CONDITION = new_condition_proof(CONDITION_HTML, "https://www.allithypermarket.com.my/products/test", OBSERVED)


def product():
    value = json.loads((FIXTURES / "regressions.json").read_text(encoding="utf-8"))["shopify_variants"]
    value["title"] = "HP Test Laptop 15-FA2547TX 16GB / 32GB"
    value["product_type"] = "NOTEB"
    value["options"] = [{"name": "Memory", "position": 1}]
    value["variants"][0]["option1"] = "16GB"
    value["variants"][1]["option1"] = "32GB"
    return value


def response(products=None, status=200, malformed=False):
    result = Mock(status_code=status)
    result.json.return_value = {} if malformed else {"products": products or []}
    if status >= 400:
        result.raise_for_status.side_effect = requests.HTTPError(f"HTTP {status}")
    return result


def detail_responses():
    html = response()
    html.text = CONDITION_HTML
    detail = response()
    detail.json.return_value = {"product": product()}
    return [html, detail]


class SourceNormalizationTests(unittest.TestCase):
    def test_memory_and_storage_never_take_gpu_vram(self):
        specs = title_specs('Laptop i7-13650HX/RTX4060 8GB GDDR6/32GB DDR5/1TB SSD/15.6"FHD 144Hz')
        self.assertEqual(specs["memory"], "32GB DDR5")
        self.assertEqual(specs["storage"], "1TB SSD")
        self.assertEqual(specs["processor"], "Intel Core i7-13650HX")
        self.assertIsNone(capacity("RTX4060 8GB GDDR6", "memory"))

    def test_repeated_total_labels_are_not_alternative_configurations(self):
        self.assertEqual(capacity("8GB DDR4 / 8GB", "memory")["capacity_gb"], 8)
        self.assertEqual(capacity("16GB DDR5 Memory Configuration: 1 x 16GB", "memory")["capacity_gb"], 16)
        self.assertIsNone(capacity("16GB / 32GB", "memory"))
        self.assertIsNone(capacity("8GB DDR4 / 8GB DDR5", "memory"))

    def test_part_numbers_require_model_evidence_and_reject_abbreviated_alternatives(self):
        self.assertIsNone(manufacturer_part_number("Acer Acer Aspire 7 Laptop", "4711721057414"))
        self.assertIsNone(manufacturer_part_number("HP 14-hu0084TU/hu0085TU laptop"))
        self.assertIsNone(manufacturer_part_number("Lenovo laptop", "83RWCTO1WWMY2"))
        self.assertEqual(manufacturer_part_number("HP 14-EM0299AU (E15ZZPA) laptop"), "E15ZZPA")
        self.assertEqual(manufacturer_part_number("Lenovo LOQ 83DV01JTMJ laptop"), "83DV01JTMJ")

    def test_hardware_model_labels_are_bounded_and_gpu_is_not_inferred(self):
        from scrapers.asus_scraper import infer_graphics
        self.assertEqual(infer_graphics("Intel Core Ultra 7", "ASUS laptop", ""), "")
        self.assertEqual(cpu_model("AMD Ryzen 7 7730U, up to 4.5GHz, 8 cores"), "AMD Ryzen 7 7730U")
        self.assertEqual(cpu_model("Intel Core 5 processor 120U"), "Intel Core 5 120U")
        self.assertEqual(cpu_model("Up to Intel Core Ultra 7"), "")
        self.assertEqual(cpu_model("Intel i5-13420H / AMD Ryzen 7 7730U"), "")
        self.assertEqual(display_spec('15.6" FHD 144Hz')["resolution_width"], 1920)
        self.assertEqual(display_spec('15.6" Full HD IPS')["resolution_width"], 1920)
        self.assertIn("IPS", display_spec('15.6" Full HD IPS')["label"])
        self.assertIsNone(display_spec('16" 2560x1600 IPS up to 240Hz')["refresh_hz"])
        self.assertEqual(display_spec('16" 2560x1600 IPS up to 240Hz')["resolution_width"], 2560)


class ShopifyAdapterTests(unittest.TestCase):
    def test_variants_have_correct_prices_ram_stock_and_deep_links(self):
        value = product()
        value["variants"][1]["available"] = False
        records = allit_records(value, OBSERVED, condition_evidence=CONDITION)
        result = build_catalog([source(records, source_id="allit")], generated_at=GENERATED)
        self.assertEqual(len(result.catalog["offers"]), 2)
        configs = {item["id"]: item for item in result.catalog["configurations"]}
        offers = {item["variant_id"]: item for item in result.catalog["offers"]}
        self.assertEqual(offers["101"]["price_sen"], 399900)
        self.assertEqual(configs[offers["101"]["configuration_id"]]["memory"]["capacity_gb"], 16)
        self.assertIn("variant=101", offers["101"]["url"])
        self.assertEqual(offers["102"]["availability"], "out_of_stock")
        self.assertEqual(configs[offers["102"]["configuration_id"]]["memory"]["capacity_gb"], 32)
        self.assertEqual({offer["seller"] for offer in offers.values()}, {"ALL IT"})

    def test_model_aliases_and_title_body_conflicts_become_diagnostics(self):
        value = product()
        value["title"] = "HP 14-hu0084TU/hu0085TU laptop"
        result = build_catalog([source(allit_records(value, OBSERVED, condition_evidence=CONDITION), source_id="allit")], generated_at=GENERATED)
        self.assertEqual(result.catalog["offers"], [])
        self.assertEqual(result.catalog["run_reports"][0]["issues"][0]["code"], "ambiguous_identity")
        value = product()
        value["options"] = []
        value["variants"] = [{"id": 101, "sku": "HP-16", "title": "Silver", "price": "3999.00"}]
        value["title"] = "HP 15-FA2547TX laptop 16GB DDR5"
        result = build_catalog([source(allit_records(value, OBSERVED, condition_evidence=CONDITION), source_id="allit")], generated_at=GENERATED)
        self.assertEqual(result.catalog["offers"], [])

    def test_non_laptops_and_refurbished_products_are_excluded(self):
        for title in ("HP laptop backpack", "HP refurbished laptop 15-FA2547TX", "2-in-1 Laptops"):
            value = product()
            value["title"] = title
            result = build_catalog([source(allit_records(value, OBSERVED, condition_evidence=CONDITION), source_id="allit")], generated_at=GENERATED)
            self.assertEqual(result.catalog["offers"], [])

    def test_acer_fallback_uses_retailer_identity_and_variant_prices(self):
        value = product()
        value["vendor"] = "Acer"
        rows = legacy_shopify_rows(value)
        self.assertEqual([row["price"] for row in rows], ["3999.00", "4499.00"])
        self.assertEqual({row["series"] for row in rows}, {"ALL IT"})

    def test_complete_pagination_returns_a_standard_source_result(self):
        session = Mock(headers={})
        session.get.side_effect = [response([product()]), *detail_responses(), response([])]
        result = collect_allit(session=session, clock=lambda: OBSERVED, sleep=Mock(), page_size=1)
        self.assertEqual(result.status, "complete")
        self.assertEqual(len(result.records), 2)
        self.assertEqual(session.get.call_count, 4)
        validate_catalog(build_catalog([result], generated_at=GENERATED).catalog)

    def test_condition_proof_requests_html_instead_of_json(self):
        session = Mock(headers={})
        session.get.side_effect = [response([product()]), *detail_responses(), response([])]
        result = collect_allit(session=session, clock=lambda: OBSERVED, sleep=Mock(), page_size=1)
        self.assertEqual(result.status, "complete")
        self.assertEqual(session.get.call_args_list[1].kwargs.get("headers", {}).get("Accept"), "text/html")
        self.assertEqual(session.get.call_args_list[2].kwargs.get("headers", {}).get("Accept"), "application/json")

    def test_pagination_failure_and_repeated_pages_cannot_become_complete(self):
        for second in (response(status=403), response([product()])):
            session = Mock(headers={})
            session.get.side_effect = [response([product()]), *detail_responses(), second]
            result = collect_allit(session=session, clock=lambda: OBSERVED, sleep=Mock(), page_size=1)
            self.assertEqual(result.status, "partial")
            self.assertTrue(result.error)
            self.assertEqual(build_catalog([result], generated_at=GENERATED).catalog["offers"], [])

    def test_bad_response_and_rate_limit_fail_explicitly(self):
        for bad in (response(malformed=True), response(status=429)):
            session = Mock(headers={})
            session.get.return_value = bad
            result = collect_allit(session=session, clock=lambda: OBSERVED, sleep=Mock())
            self.assertEqual(result.status, "failed")
            self.assertTrue(result.error)
            self.assertLessEqual(session.get.call_count, 3)

    def test_unqualified_sources_are_truthfully_deferred(self):
        results = collect_sources(["shopee", "msi", "lenovo"])
        catalog = build_catalog(results, generated_at="2099-01-01T00:00:00Z").catalog
        self.assertEqual(catalog["offers"], [])
        self.assertTrue(all(report["status"] == "not_run" for report in catalog["run_reports"]))
        self.assertTrue(all(report["started_at"] is None for report in catalog["run_reports"]))


class MatchingAndEnrichmentTests(unittest.TestCase):
    def test_equivalent_complete_configurations_merge_without_moving_prices(self):
        result = build_catalog([source(source_id="seller_a"), source(source_id="seller_b")], generated_at=GENERATED)
        matched = match_catalog(result)
        self.assertEqual(len(matched.catalog["configurations"]), 1)
        self.assertEqual(len(matched.catalog["offers"]), 2)
        self.assertEqual(len(matched.catalog["observations"]), 2)
        self.assertEqual({offer["price_sen"] for offer in matched.catalog["offers"]}, {399900})
        self.assertEqual(len(result.catalog["configurations"]), 2)
        validate_catalog(matched.catalog)

    def test_unknown_and_conflicting_configuration_facts_never_merge(self):
        for field in ("unknown", "memory", "display"):
            second = record()
            if field == "unknown": second["configuration"]["display"]["refresh_hz"] = None
            if field == "memory": second["configuration"]["memory"] = {"capacity_gb": 32, "label": "32GB DDR5"}
            if field == "display": second["configuration"]["display"] = {"diagonal_inches": 16, "resolution_width": 2560, "resolution_height": 1600, "refresh_hz": 165, "label": "16 inch 2560x1600 165Hz"}
            result = build_catalog([source(source_id="seller_a"), source([second], source_id="seller_b")], generated_at=GENERATED)
            self.assertEqual(len(match_catalog(result).catalog["configurations"]), 2)

    def test_two_unknown_gpu_descriptions_do_not_establish_equivalence(self):
        for kind in ("unknown", "discrete"):
            value = record()
            value["configuration"]["gpu_kind"] = kind
            value["configuration"]["vram_gb"] = None
            result = build_catalog([source([deepcopy(value)], source_id="seller_a"), source([deepcopy(value)], source_id="seller_b")], generated_at=GENERATED)
            self.assertEqual(len(match_catalog(result).catalog["configurations"]), 2)

    def test_master_lenovo_entrypoint_enriches_missing_fields(self):
        from scrapers import lenovo_scraper as lenovo
        listing = {"data": {"pageCount": 1, "data": [{"products": [{"productCode": "83DV01JTMJ", "summary": "Lenovo LOQ laptop", "url": "/p/laptop/83DV01JTMJ", "finalPrice": "3999.00", "classification": [{"a": "Processor", "b": "Intel Core i5-13450HX"}]}]}]}}
        specs = {"data": {"tables": [{"specs": [{"headline": "Memory", "text": "<p>16GB DDR5</p>"}, {"headline": "Graphics", "text": "RTX 4050"}]}]}}
        with patch.object(lenovo, "fetch_listing", return_value=listing), patch.object(lenovo, "fetch_tech_specs", return_value=specs) as fetch:
            rows = lenovo.fetch_all_products("test")
        fetch.assert_called_once()
        self.assertEqual(rows[0]["memory"], "16GB DDR5")
        self.assertEqual(rows[0]["graphics"], "RTX 4050")
        self.assertEqual(rows[0]["processor"], "Intel Core i5-13450HX")

    def test_captured_collection_keeps_every_rejection_and_never_uses_build_time(self):
        pages = [json.loads(path.read_text(encoding="utf-8")) for path in sorted((FIXTURES / "captured").glob("allit_page*.json"))]
        details = json.loads((FIXTURES / "captured/allit_verified_details.json").read_text(encoding="utf-8"))["records"]
        verified = {str(item["product"]["id"]): item for item in details}
        records = []
        for page in pages:
            for item in page["payload"]["products"]:
                check = verified.get(str(item["id"]))
                records.extend(allit_records(check["product"], check["observed_at"], condition_evidence=check["condition_evidence"]) if check else allit_records(item, page["observed_at"]))
        finished = max(item["observed_at"] for item in details)
        result = build_catalog([SourceResult("allit", "complete", records, started_at=pages[0]["observed_at"], finished_at=finished)], generated_at="2099-01-01T00:00:00Z")
        report, = result.catalog["run_reports"]
        self.assertEqual(sum(len(page["payload"]["products"]) for page in pages), 60)
        self.assertEqual(report["record_count"], report["accepted_count"] + report["rejected_count"])
        self.assertEqual(report["accepted_count"], 19)
        self.assertEqual(report["rejected_count"], 41)
        self.assertEqual({item["observed_at"] for item in result.catalog["observations"]}, {item["observed_at"] for item in details})

    def test_new_condition_requires_explicit_source_evidence(self):
        for html in ("<html></html>", CONDITION_HTML.replace("NewCondition", "UsedCondition")):
            with self.assertRaises(ValueError):
                new_condition_proof(html, "https://example.com/product", OBSERVED)
        result = build_catalog([source(allit_records(product(), OBSERVED), source_id="allit")], generated_at=GENERATED)
        self.assertEqual(result.catalog["offers"], [])



class CandidateCommandTests(unittest.TestCase):
    def test_candidate_command_writes_separate_validated_output(self):
        from tools.collect_catalog_v2 import main
        with tempfile.TemporaryDirectory() as directory:
            with patch("tools.collect_catalog_v2.collect_sources", return_value=[source(source_id="allit")]):
                self.assertEqual(main(["--output-dir", directory]), 0)
            saved = json.loads((Path(directory) / "catalog.v2.json").read_text(encoding="utf-8"))
            validate_catalog(saved)
            self.assertEqual(len(saved["offers"]), 1)

    def test_deferred_source_returns_failure_and_truthful_report(self):
        from tools.collect_catalog_v2 import main
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(main(["--sources", "msi", "--output-dir", directory]), 1)
            saved = json.loads((Path(directory) / "catalog.v2.json").read_text(encoding="utf-8"))
            self.assertEqual(saved["offers"], [])
            self.assertEqual(saved["run_reports"][0]["mode"], "deferred")


if __name__ == "__main__":
    unittest.main()
