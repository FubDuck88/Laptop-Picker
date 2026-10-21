"""Validated catalog records. Legacy CSV imports are diagnostic evidence only.

Source adapters supply exact configurations and observed offers to build_catalog.
The old compiler can call build_legacy_catalog without certifying its saved data.
"""

from copy import deepcopy
import csv
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
from urllib.parse import urlsplit

from jsonschema import Draft202012Validator, FormatChecker


SCHEMA_PATH = Path(__file__).resolve().parent / "schemas" / "catalog-v2.schema.json"
FAMILY_TEXT = re.compile(r"\b(?:up\s+to|starting\s+(?:at|from)|configurable|varies)\b", re.I)
TIME_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|[+-]\d{2}:\d{2})\Z")


class CatalogValidationError(ValueError):
    def __init__(self, issues):
        self.issues = issues
        super().__init__("; ".join(f"{item['field']}: {item['message']}" for item in issues))


@dataclass
class SourceResult:
    source_id: str
    status: str
    records: list = field(default_factory=list)
    started_at: str | None = None
    finished_at: str | None = None
    mode: str = "live"
    error: str | None = None
    input_name: str | None = None


@dataclass
class CatalogBuild:
    catalog: dict
    diagnostics: dict


def _issue(code, field_name, message, product_id=None):
    return {"source_product_id": product_id, "field": field_name, "code": code, "message": message}


def _time(value):
    if not isinstance(value, str) or not TIME_PATTERN.fullmatch(value):
        raise ValueError("Use a timezone-qualified RFC 3339 timestamp")
    if not value.endswith("Z") and (int(value[-5:-3]) > 23 or int(value[-2:]) > 59):
        raise ValueError("Invalid timezone offset")
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


@lru_cache(maxsize=1)
def _schema():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return schema


@lru_cache(maxsize=None)
def _validator(definition=None):
    schema = _schema()
    if definition:
        schema = {"$defs": schema["$defs"], "$ref": f"#/$defs/{definition}"}
    checker = FormatChecker()

    @checker.checks("date-time", raises=(ValueError, TypeError))
    def valid_time(value):
        if not isinstance(value, str):
            return True
        _time(value)
        return True

    return Draft202012Validator(schema, format_checker=checker)


def _shape_issues(value, definition=None):
    try:
        json.dumps(value, allow_nan=False)
    except (TypeError, ValueError) as error:
        return [_issue("invalid_json", "", str(error))]
    errors = sorted(_validator(definition).iter_errors(value), key=lambda e: str(list(e.path)))
    return [_issue("schema", ".".join(map(str, error.path)), error.message) for error in errors]


def _valid_url(value):
    try:
        url = urlsplit(value)
        return (url.scheme in {"http", "https"} and bool(url.hostname)
                and url.username is None and url.password is None
                and not re.search(r"\s", value) and url.port != 0)
    except ValueError:
        return False


def _price_sen(value):
    # No floats, exponent notation, ranges, negative values, installments, or rounding.
    if not isinstance(value, str):
        raise ValueError("price_myr must be an exact decimal string")
    amount = value.strip()
    if amount.startswith("RM"):
        amount = amount[2:].strip()
    if not re.fullmatch(r"(?:[0-9]+|[0-9]{1,3}(?:,[0-9]{3})+)(?:\.[0-9]{1,2})?", amount):
        raise ValueError("Expected one positive MYR amount with at most two decimal places")
    sen = int(Decimal(amount.replace(",", "")) * 100)
    if sen <= 0:
        raise ValueError("Price must be greater than zero")
    return sen


def _stable_id(prefix, value):
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    return prefix + "_" + hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:24]


def _evidence_issues(record, required, observed_at):
    issues = []
    for name in required:
        if name not in record["evidence"]:
            issues.append(_issue("missing_evidence", f"evidence.{name}", "Known facts need source evidence"))
    for name, evidence in record["evidence"].items():
        if not _valid_url(evidence["source_url"]):
            issues.append(_issue("invalid_url", f"evidence.{name}.source_url", "Expected a public HTTP(S) URL without credentials"))
        if _time(evidence["observed_at"]) > observed_at:
            issues.append(_issue("future_evidence", f"evidence.{name}.observed_at", "Evidence cannot be newer than the offer observation"))
    return issues


def _capacity_issues(name, capacity):
    label, value = capacity["label"], capacity["capacity_gb"]
    if name == "memory" and label and re.search(r"GDDR|VRAM", label, re.I):
        return [_issue("vram_as_ram", name, "Graphics memory cannot become system RAM")]
    if value is None:
        if label and len(re.findall(r"\b\d+(?:\.\d+)?\s*(?:GB|TB)\b", label, re.I)) > 1:
            return [_issue("ambiguous_capacity", name, "Alternative capacities cannot describe one configuration")]
        return []
    if not label:
        return [_issue("missing_label", name, "A normalized capacity requires its source label")]
    match = re.fullmatch(r".*?\b(\d+)\s*[x×]\s*(\d+(?:\.\d+)?)\s*(GB|TB)\b.*", label, re.I)
    if match:
        expected = Decimal(match[1]) * Decimal(match[2]) * (1000 if match[3].upper() == "TB" else 1)
    else:
        tokens = re.findall(r"\b(\d+(?:\.\d+)?)\s*(GB|TB)\b", label, re.I)
        if len(tokens) != 1:
            return [_issue("ambiguous_capacity", name, "Use a single installed capacity, not alternatives or maxima")]
        number, unit = tokens[0]
        expected = Decimal(number) * (1000 if unit.upper() == "TB" else 1)
    if expected != value:
        return [_issue("conflicting_capacity", name, "Normalized capacity disagrees with its source label (1 TB = 1000 GB)")]
    return []


def _display_issues(display):
    issues = []
    label = display["label"]
    numeric = ("diagonal_inches", "resolution_width", "resolution_height", "refresh_hz")
    if any(display[name] is not None for name in numeric) and not label:
        return [_issue("missing_label", "display", "Normalized display values require a source label")]
    if not label:
        return issues
    patterns = {
        "diagonal_inches": r'\b(\d{1,2}(?:\.\d+)?)\s*(?:["”]|inch(?:es)?\b)',
        "refresh_hz": r"\b(\d+(?:\.\d+)?)\s*Hz\b",
    }
    for name, pattern in patterns.items():
        values = {Decimal(match) for match in re.findall(pattern, label, re.I)}
        if len(values) > 1 or (values and display[name] is not None and Decimal(str(display[name])) not in values):
            issues.append(_issue("conflicting_display", f"display.{name}", "Display value disagrees with its label or lists alternatives"))
    resolutions = set(re.findall(r"\b(\d{3,5})\s*[x×]\s*(\d{3,5})\b", label, re.I))
    if len(resolutions) > 1 or (resolutions and display["resolution_width"] is not None and
                              (str(display["resolution_width"]), str(display["resolution_height"])) not in resolutions):
        issues.append(_issue("conflicting_display", "display", "Resolution disagrees with its label or lists alternatives"))
    return issues


def _record_issues(configuration, offer, generated_at):
    issues = _shape_issues(configuration, "configuration") + _shape_issues(offer, "offer")
    if issues:
        return issues
    observed = _time(offer["observed_at"])
    if type(offer["price_sen"]) is not int:
        issues.append(_issue("invalid_price", "price_sen", "Sen must be an integer, not a float or boolean"))
    if observed > generated_at:
        issues.append(_issue("future_observation", "observed_at", "An observation cannot be newer than this build"))
    if not _valid_url(offer["url"]):
        issues.append(_issue("invalid_url", "url", "Expected an HTTP(S) purchase URL without credentials"))
    # The contract accepts explicit model fields, never family descriptions or free-form 'others'.
    for name in ("title", "cpu_model", "gpu_model"):
        if configuration[name] and FAMILY_TEXT.search(configuration[name]):
            issues.append(_issue("family_level", name, "Family maxima are not an exact configuration"))
        if name != "title" and configuration[name] and re.search(r"/|\bor\b|\boptions?\b", configuration[name], re.I):
            issues.append(_issue("ambiguous_model", name, "A model field must identify one installed component"))
    for name in ("memory", "storage", "display"):
        label = configuration[name]["label"]
        if label and FAMILY_TEXT.search(label):
            issues.append(_issue("family_level", name, "Family maxima are not installed specifications"))
    for name in ("memory", "storage"):
        issues.extend(_capacity_issues(name, configuration[name]))
    display = configuration["display"]
    issues.extend(_display_issues(display))
    if (display["resolution_width"] is None) != (display["resolution_height"] is None):
        issues.append(_issue("incomplete_resolution", "display", "Resolution needs both width and height"))
    if configuration["gpu_kind"] == "integrated" and configuration["vram_gb"] is not None:
        issues.append(_issue("integrated_vram", "vram_gb", "Shared system memory is not dedicated GPU VRAM"))

    required = {"brand", "manufacturer_part_number", "product_type", "identity_scope"}
    for name in ("cpu_model", "gpu_model", "vram_gb", "battery_wh", "weight_kg", "wifi", "ports", "warranty"):
        if configuration[name] is not None:
            required.add(name)
    if configuration["gpu_kind"] != "unknown":
        required.add("gpu_kind")
    for name in ("memory", "storage", "display"):
        if any(value is not None for value in configuration[name].values()):
            required.add(name)
    issues.extend(_evidence_issues(configuration, required, observed))
    required_offer = {"seller", "source_product_id", "variant_id", "url", "price", "price_basis", "condition"}
    if offer.get("image_url") is not None:
        required_offer.add("image_url")
        if not _valid_url(offer["image_url"]):
            issues.append(_issue("invalid_image_url", "image_url", "Expected an HTTP(S) source photo URL without credentials"))
    if offer["availability"] != "unknown":
        required_offer.add("availability")
    issues.extend(_evidence_issues(offer, required_offer, observed))
    image_proof = offer["evidence"].get("image_url")
    if offer.get("image_url") and image_proof and image_proof["raw_value"] != offer["image_url"]:
        issues.append(_issue("conflicting_image", "image_url", "Photo URL disagrees with its source evidence"))
    price_evidence = offer["evidence"].get("price")
    if price_evidence:
        try:
            if _price_sen(price_evidence["raw_value"]) != offer["price_sen"]:
                issues.append(_issue("conflicting_price", "price_sen", "Price disagrees with its source evidence"))
        except ValueError as error:
            issues.append(_issue("invalid_price_evidence", "evidence.price", str(error)))
    for name in ("price", "availability"):
        evidence = offer["evidence"].get(name)
        if evidence and _time(evidence["observed_at"]) != observed:
            issues.append(_issue("stale_evidence", f"evidence.{name}", "Price and stock evidence must come from this observation"))
    return issues


def validate_catalog(catalog):
    """Validate shape, references, evidence, counts and chronology; raise on any issue."""
    issues = _shape_issues(catalog)
    if issues:
        raise CatalogValidationError(issues)
    generated = _time(catalog["generated_at"])
    maps = {}
    for name, key in (("configurations", "id"), ("offers", "id"), ("observations", "id"), ("run_reports", "source_id")):
        maps[name] = {row[key]: row for row in catalog[name]}
        if len(maps[name]) != len(catalog[name]):
            issues.append(_issue("duplicate_id", name, "Identifiers must be unique"))

    for report in catalog["run_reports"]:
        if report["record_count"] != report["accepted_count"] + report["rejected_count"]:
            issues.append(_issue("invalid_counts", report["source_id"], "Accepted and rejected counts must account for every input record"))
        if report["mode"] in {"legacy_import", "deferred"}:
            if report["status"] not in {"not_run", "failed"} or report["accepted_count"] or report["started_at"] or report["finished_at"]:
                issues.append(_issue("unverified_import", report["source_id"], "Imports and deferred sources cannot assert a live run, accepted offers, or collection times"))
            if report["mode"] == "deferred" and (report["status"] != "not_run" or not report["error"]):
                issues.append(_issue("invalid_deferral", report["source_id"], "Deferred sources need not_run status and a reason"))
        else:
            if report["status"] == "not_run" or not report["started_at"] or not report["finished_at"]:
                issues.append(_issue("missing_run_time", report["source_id"], "Live results require status and actual start/finish times"))
            elif not (_time(report["started_at"]) <= _time(report["finished_at"]) <= generated):
                issues.append(_issue("invalid_run_time", report["source_id"], "Collection must finish after it starts and before the build"))
        if report["status"] in {"partial", "failed"} and not report["error"]:
            issues.append(_issue("missing_failure_reason", report["source_id"], "Incomplete results require an explanation"))
        if report["status"] == "complete" and report["error"] is not None:
            issues.append(_issue("conflicting_status", report["source_id"], "A complete result cannot carry a collection error"))

    used_configurations = set()
    variant_configurations = {}
    for offer in catalog["offers"]:
        variant = (offer["source_id"], offer["source_product_id"], offer["variant_id"])
        if variant in variant_configurations:
            code = "conflicting_variant" if variant_configurations[variant] != offer["configuration_id"] else "duplicate_offer"
            issues.append(_issue(code, offer["id"], "One source variant must identify one current configuration and offer"))
        variant_configurations[variant] = offer["configuration_id"]
        configuration = maps["configurations"].get(offer["configuration_id"])
        report = maps["run_reports"].get(offer["source_id"])
        if configuration is None or report is None:
            issues.append(_issue("missing_reference", offer["id"], "Offer needs an existing configuration and source report"))
            continue
        if report["mode"] in {"legacy_import", "deferred"}:
            issues.append(_issue("unverified_import", offer["id"], "Imports and deferred sources cannot certify offers"))
        used_configurations.add(configuration["id"])
        issues.extend(_record_issues(configuration, offer, generated))

    for configuration in catalog["configurations"]:
        if configuration["id"] not in used_configurations:
            issues.append(_issue("orphan_configuration", configuration["id"], "Verified configurations must have an accepted offer"))
    current_observations = set()
    observation_keys = set()
    for observation in catalog["observations"]:
        if type(observation["price_sen"]) is not int:
            issues.append(_issue("invalid_price", observation["id"], "Observation sen must be an integer"))
        offer = maps["offers"].get(observation["offer_id"])
        if offer is None or observation["configuration_id"] != offer["configuration_id"]:
            issues.append(_issue("missing_reference", observation["id"], "Observation must reference its offer's configuration"))
            continue
        observed = _time(observation["observed_at"])
        current = _time(offer["observed_at"])
        key = (offer["id"], observed)
        if key in observation_keys:
            issues.append(_issue("duplicate_observation", observation["id"], "One observation per offer and instant is allowed"))
        observation_keys.add(key)
        if observed > current:
            issues.append(_issue("future_observation", observation["id"], "History cannot be newer than its current offer"))
        if observed == current:
            if any(observation[name] != offer[name] for name in ("price_sen", "currency", "availability")):
                issues.append(_issue("conflicting_observation", observation["id"], "Latest observation must agree with the current offer"))
            current_observations.add(offer["id"])
    if current_observations != set(maps["offers"]):
        issues.append(_issue("missing_observation", "observations", "Every current offer needs its actual price observation"))
    if issues:
        raise CatalogValidationError(issues)


def _prepare_record(record, source_id):
    if not isinstance(record, dict) or set(record) != {"configuration", "offer"}:
        raise ValueError("Each native record requires configuration and offer objects only")
    configuration, offer = deepcopy(record["configuration"]), deepcopy(record["offer"])
    if not isinstance(configuration, dict) or not isinstance(offer, dict):
        raise ValueError("Configuration and offer must be objects")
    defaults = {
        "cpu_model": None, "gpu_model": None, "gpu_kind": "unknown", "vram_gb": None,
        "memory": {"capacity_gb": None, "label": None},
        "storage": {"capacity_gb": None, "label": None},
        "display": {"diagonal_inches": None, "resolution_width": None, "resolution_height": None, "refresh_hz": None, "label": None},
        "battery_wh": None, "weight_kg": None, "wifi": None, "ports": None, "warranty": None, "evidence": {},
    }
    for name, value in defaults.items():
        configuration.setdefault(name, value)
        if isinstance(value, dict) and name != "evidence" and isinstance(configuration[name], dict):
            configuration[name] = {**value, **configuration[name]}
    for name in ("brand", "manufacturer_part_number", "title"):
        if isinstance(configuration.get(name), str):
            configuration[name] = configuration[name].strip()
    if isinstance(configuration.get("manufacturer_part_number"), str):
        configuration["manufacturer_part_number"] = configuration["manufacturer_part_number"].upper()
    if "price_myr" in offer:
        if "price_sen" in offer:
            raise ValueError("Supply price_myr or price_sen, not both")
        offer["price_sen"] = _price_sen(offer.pop("price_myr"))
    offer.setdefault("currency", "MYR")
    offer.setdefault("availability", "unknown")
    offer.setdefault("evidence", {})
    if "source_id" in offer and offer["source_id"] != source_id:
        raise ValueError("Offer source_id disagrees with its SourceResult")
    offer["source_id"] = source_id
    # Source-scoped IDs deliberately do not perform cross-store matching in Phase 2.
    identity = [source_id, offer.get("source_product_id"), offer.get("variant_id")]
    specs = {name: value for name, value in configuration.items() if name not in {"id", "title", "evidence"}}
    configuration_id = _stable_id("cfg", [identity, specs])
    if configuration.get("id", configuration_id) != configuration_id:
        raise ValueError("Configuration id disagrees with its identity and specifications")
    configuration["id"] = configuration_id
    offer_id = _stable_id("offer", [identity, configuration_id])
    for name, value in (("id", offer_id), ("configuration_id", configuration_id)):
        if offer.get(name, value) != value:
            raise ValueError(f"Offer {name} disagrees with its configuration identity")
        offer[name] = value
    return configuration, offer


def _prepare_result(result, generated):
    prepared, identities = [], {}
    for record in result.records:
        if isinstance(record, dict) and isinstance(record.get("rejection"), dict):
            rejected = record["rejection"]
            prepared.append((None, None, [_issue(str(rejected.get("code") or "source_rejected"), "", str(rejected.get("message") or "Source could not establish this configuration"))]))
            continue
        try:
            configuration, offer = _prepare_record(record, result.source_id)
            issues = _record_issues(configuration, offer, generated)
            if not issues and result.started_at and result.finished_at and not (_time(result.started_at) <= _time(offer["observed_at"]) <= _time(result.finished_at)):
                issues = [_issue("outside_run", "observed_at", "A new observation must occur within the source run")]
            if not issues:
                key = (offer["source_product_id"], offer["variant_id"])
                state = (configuration["id"], offer["price_sen"], offer["availability"], offer["seller"],
                         offer["url"], _time(offer["observed_at"]).astimezone(timezone.utc))
                identities.setdefault(key, set()).add(state)
        except (ValueError, TypeError) as error:
            configuration = offer = None
            issues = [_issue("invalid_record", "", str(error))]
        prepared.append((configuration, offer, issues))
    # Reject both sides of a conflict; input order must not pick a winning build.
    for configuration, offer, issues in prepared:
        if not issues and len(identities[(offer["source_product_id"], offer["variant_id"])]) > 1:
            issues.append(_issue("conflicting_variant", "variant_id", "The same source variant asserts conflicting configurations or offer observations"))
    return prepared


def _diagnostic_record(record):
    try:
        json.dumps(record, allow_nan=False)
        return deepcopy(record)
    except (ValueError, TypeError):
        return {"unserializable_record": repr(record)[:2048]}


def build_catalog(source_results, *, generated_at=None):
    """Build from explicit source results; reject bad records without inventing evidence."""
    if generated_at is None:
        generated_at = datetime.now(timezone.utc).isoformat()
    generated = _time(generated_at)
    catalog = {"schema_version": 2, "generated_at": generated_at,
               "configurations": [], "offers": [], "observations": [], "run_reports": []}
    diagnostics = {"schema_version": 2, "generated_at": generated_at, "records": []}
    source_results = list(source_results)
    # Reject malformed collection metadata before inspecting any records.
    for result in source_results:
        if not isinstance(result, SourceResult) or not isinstance(result.records, list):
            raise CatalogValidationError([_issue("invalid_source_result", "", "Supply SourceResult objects with records lists")])
        header = {"source_id": result.source_id, "mode": result.mode, "status": result.status,
                  "started_at": result.started_at, "finished_at": result.finished_at,
                  "record_count": len(result.records), "accepted_count": 0, "rejected_count": 0,
                  "error": result.error, "issues": []}
        issues = _shape_issues(header, "run_report")
        if issues:
            raise CatalogValidationError(issues)
    seen_sources, seen_offers = set(), set()
    for result in sorted(source_results, key=lambda item: item.source_id):
        if result.source_id in seen_sources:
            raise CatalogValidationError([_issue("duplicate_source", "source_id", "Supply one result per source")])
        seen_sources.add(result.source_id)
        report = {"source_id": result.source_id, "mode": result.mode, "status": result.status,
                  "started_at": result.started_at, "finished_at": result.finished_at,
                  "record_count": len(result.records), "accepted_count": 0, "rejected_count": 0,
                  "error": result.error, "issues": []}
        prepared = _prepare_result(result, generated) if result.mode == "live" and result.status == "complete" else []
        for index, record in enumerate(result.records, start=1):
            configuration = offer = None
            product_id = None
            if isinstance(record, dict):
                if result.mode == "legacy_import":
                    product_id = record.get("id")
                elif isinstance(record.get("offer"), dict):
                    product_id = record["offer"].get("source_product_id")
                elif isinstance(record.get("rejection"), dict):
                    product_id = record["rejection"].get("source_product_id")
            if product_id is not None:
                product_id = str(product_id)
            if result.mode == "deferred":
                issues = [_issue("source_deferred", "", result.error or "Source has not been qualified")]
            elif result.mode == "legacy_import":
                issues = [_issue("legacy_unverified", "", "Saved CSV has no verified variant identity or observation time")]
                if isinstance(record, dict) and any(FAMILY_TEXT.search(str(record.get(name, ""))) for name in ("title", "processor", "graphics", "memory", "storage", "display")):
                    issues.append(_issue("family_level", "configuration", "Family maxima cannot become exact offers"))
            elif result.status != "complete":
                issues = [_issue("incomplete_source", "", "Only a complete live source result may contribute new offers")]
            else:
                configuration, offer, issues = prepared[index - 1]
                if not issues and offer["id"] in seen_offers:
                    issues = [_issue("duplicate_offer", "id", "Duplicate product/variant/configuration in the same build")]
            if issues:
                report["rejected_count"] += 1
                for issue in issues:
                    issue["source_product_id"] = product_id
                report["issues"].extend(issues)
                diagnostics["records"].append({"source_id": result.source_id, "input_name": result.input_name,
                                               "row_number": index, "source_product_id": product_id,
                                               "issues": deepcopy(issues), "record": _diagnostic_record(record)})
                continue
            seen_offers.add(offer["id"])
            report["accepted_count"] += 1
            catalog["configurations"].append(configuration)
            catalog["offers"].append(offer)
            catalog["observations"].append({
                "id": _stable_id("obs", [offer["id"], _time(offer["observed_at"]).astimezone(timezone.utc).isoformat()]),
                "offer_id": offer["id"], "configuration_id": configuration["id"],
                **{name: offer[name] for name in ("observed_at", "currency", "price_sen", "availability")},
            })
        catalog["run_reports"].append(report)
    for name in ("configurations", "offers", "observations"):
        catalog[name].sort(key=lambda item: item["id"])
    validate_catalog(catalog)
    return CatalogBuild(catalog, diagnostics)


def build_legacy_catalog(csv_paths, *, generated_at=None):
    """Read source CSVs without using file times, compiler guesses, or merged output."""
    results = []
    for path in sorted(map(Path, csv_paths)):
        if path.name == "master_laptops.csv":
            continue
        source_id = path.stem.removesuffix("_laptops")
        try:
            with path.open(encoding="utf-8-sig", newline="") as handle:
                records = list(csv.DictReader(handle))
            result = SourceResult(source_id, "not_run", records, mode="legacy_import", input_name=path.name)
        except (OSError, UnicodeError, csv.Error) as error:
            result = SourceResult(source_id, "failed", mode="legacy_import", error=str(error), input_name=path.name)
        results.append(result)
    return build_catalog(results, generated_at=generated_at)


def write_catalog(build, directory):
    """Validate before touching output, then replace each artifact without truncation."""
    validate_catalog(build.catalog)
    outputs = {
        "catalog.v2.diagnostics.json": build.diagnostics,
        "catalog.v2.json": build.catalog,
    }
    encoded = {name: json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n"
               for name, value in outputs.items()}
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    for name, content in encoded.items():
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=directory, prefix=".catalog-", suffix=".tmp", delete=False) as handle:
                temporary = Path(handle.name)
                handle.write(content)
            os.replace(temporary, directory / name)
        finally:
            if temporary and temporary.exists():
                temporary.unlink()
