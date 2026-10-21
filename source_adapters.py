"""Native source collectors and variant-scoped normalization for catalog v2."""

from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import time
from urllib.parse import urlencode

from bs4 import BeautifulSoup
import requests

from catalog_v2 import SourceResult, build_catalog, validate_catalog
from source_photos import shopify_photo
from source_normalization import (capacity, clean, cpu_model, display_spec, gpu_model, gpu_details,
                                  is_family_level, is_laptop_listing, manufacturer_part_number)


ALLIT_URL = "https://www.allithypermarket.com.my"
SOURCE_IDS = ("acer", "allit", "asus", "dell", "gloo", "hp", "lenovo", "msi", "pcimage", "shopee", "techhypermart", "tmt")


def now():
    return datetime.now(timezone.utc).isoformat()


def rejection(product_id, code, message, raw):
    return {"rejection": {"source_product_id": str(product_id or ""), "code": code, "message": message}, "raw": raw}


def labeled_specs(body_html):
    soup = BeautifulSoup(body_html or "", "lxml")
    values = {}
    labels = {"processor": r"processor|cpu", "graphics": r"graphics?|gpu|vga",
              "memory": r"memory|ram", "storage": r"storage|ssd|hard drive", "display": r"display|screen"}

    def assign(key, value):
        key, value = clean(key).strip(":"), clean(value)
        for name, pattern in labels.items():
            if re.fullmatch(pattern, key, re.I) and value:
                if name in values and values[name] != value:
                    values[name] += " / " + value
                else:
                    values[name] = value

    for row in soup.find_all("tr"):
        cells = row.find_all(["td", "th"], recursive=False)
        if len(cells) == 2:
            assign(cells[0].get_text(" ", strip=True), cells[1].get_text(" ", strip=True))
    for item in soup.find_all(["p", "li"]):
        # Bound each labeled value at the next label instead of taking a whole marketing paragraph.
        text = item.get_text(" ", strip=True)
        pieces = re.split(r"\b(Processor|CPU|Graphics|GPU|Memory|RAM|Storage|SSD|Display|Screen)\s*:\s*", text, flags=re.I)
        for index in range(1, len(pieces) - 1, 2):
            assign(pieces[index], pieces[index + 1])
    return values


def _variant_specs(product, variant):
    base = labeled_specs(product.get("body_html"))
    scoped = {}
    for index, option in enumerate(product.get("options") or [], start=1):
        name = clean(option.get("name"))
        value = clean(variant.get(f"option{index}"))
        mapping = {"memory": "memory", "ram": "memory", "storage": "storage", "ssd": "storage",
                   "processor": "processor", "cpu": "processor", "graphics": "graphics", "gpu": "graphics", "display": "display"}
        if name.lower() in mapping and value:
            scoped[mapping[name.lower()]] = value
    # Some Shopify feeds expose only a compact variant title rather than named options.
    variant_title = clean(variant.get("title"))
    for name in ("memory", "storage"):
        parsed = capacity(variant_title, name)
        if parsed:
            scoped.setdefault(name, parsed["label"])
    return base, scoped


def _resolve_specs(product, variant):
    base, scoped = _variant_specs(product, variant)
    title = product.get("title") or ""
    result, evidence = {}, {}
    parsers = {"processor": cpu_model, "graphics": gpu_model,
               "memory": lambda text: capacity(text, "memory"),
               "storage": lambda text: capacity(text, "storage"), "display": display_spec}
    for name, parse in parsers.items():
        if name in scoped:
            raw, method = scoped[name], "structured"
            value = parse(raw)
        else:
            raw, method = base.get(name) or title, "labeled" if base.get(name) else "title"
            value = parse(raw)
            title_value = parse(title)
            # A product-wide value may not silently override a different title configuration.
            if base.get(name) and value and title_value:
                if name in {"memory", "storage"}:
                    conflict = value["capacity_gb"] != title_value["capacity_gb"]
                    body_type = re.search(r"(?:LP)?DDR[345]X?", value["label"], re.I)
                    title_type = re.search(r"(?:LP)?DDR[345]X?", title_value["label"], re.I)
                    conflict = conflict or bool(body_type and title_type and body_type[0].upper() != title_type[0].upper())
                elif name == "display":
                    conflict = any(value[key] is not None and title_value[key] is not None and value[key] != title_value[key]
                                   for key in ("diagonal_inches", "resolution_width", "resolution_height", "refresh_hz"))
                    panel_a = re.search(r"\b(OLED|IPS(?:-Level)?|TN|VA)\b", value["label"] or "", re.I)
                    panel_b = re.search(r"\b(OLED|IPS(?:-Level)?|TN|VA)\b", title_value["label"] or "", re.I)
                    conflict = conflict or bool(panel_a and panel_b and panel_a[0].upper() != panel_b[0].upper())
                else:
                    conflict = value.casefold() != title_value.casefold()
                if conflict:
                    raise ValueError(f"Conflicting {name} between title and specifications")
        family_value = re.sub(r"up to\s*\d+(?:\.\d+)?\s*Hz", "", base.get(name, ""), flags=re.I) if name == "display" else base.get(name, "")
        if family_value and is_family_level({name: family_value}) and name not in scoped:
            raise ValueError(f"Family-level {name} is not an installed specification")
        if name in {"memory", "storage"} and raw and len(re.findall(r"\b\d+\s*(?:GB|TB)\b", raw, re.I)) > 1 and not value and name in base:
            raise ValueError(f"Ambiguous {name} alternatives")
        result[name] = value
        if value and (name != "display" or value["label"]):
            evidence[name] = (raw, method)
    return result, evidence


def legacy_shopify_rows(product, seller="ALL IT"):
    """Compatibility output; never pair first-variant pricing with shared variant specs."""
    if not is_laptop_listing(product.get("title"), product.get("product_type", "")):
        return []
    rows = []
    for variant in product.get("variants") or []:
        try:
            specs, _ = _resolve_specs(product, variant)
        except ValueError:
            continue
        variant_id = variant.get("id")
        sku = clean(variant.get("sku")) or str(variant_id or "")
        if not sku or not product.get("handle"):
            continue
        title = clean(product.get("title"))
        if variant.get("title") and variant["title"] != "Default Title":
            title += " — " + clean(variant["title"])
        image = shopify_photo(product, variant, ALLIT_URL + "/products/" + product["handle"]) or ""
        rows.append({"id": sku, "title": title, "price": str(variant.get("price") or ""),
                     "url": f"{ALLIT_URL}/products/{product['handle']}?{urlencode({'variant': variant_id})}",
                     "image_url": image, "series": seller,
                     "processor": specs["processor"], "graphics": specs["graphics"],
                     "memory": specs["memory"]["label"] if specs["memory"] else "",
                     "storage": specs["storage"]["label"] if specs["storage"] else "",
                     "display": specs["display"]["label"] or "", "wifi": "", "battery": "", "others": "",
                     "availability": "in_stock" if variant.get("available") is True else "out_of_stock" if variant.get("available") is False else "unknown"})
    return rows


def allit_records(product, observed_at, *, condition_evidence=None):
    """One native record per actual source variant; unsafe inputs retain explicit rejections."""
    raw_id = product.get("id")
    title, brand = clean(product.get("title")), clean(product.get("vendor"))
    if not is_laptop_listing(title, product.get("product_type", "")):
        return [rejection(raw_id, "non_laptop", "Product is not a laptop listing", product)]
    if is_family_level({"title": title}):
        return [rejection(raw_id, "family_level", "Product title describes family-level specifications", product)]
    part = manufacturer_part_number(title)
    if not part:
        return [rejection(raw_id, "ambiguous_identity", "No unique manufacturer part number for this product; do not map color variants to model aliases by order", product)]
    if re.search(r"\b(?:used|refurbished|renewed|pre-owned|demo unit)\b", title, re.I):
        return [rejection(raw_id, "unsupported_condition", "Only new laptops are in scope", product)]
    if not brand or not raw_id or not product.get("handle") or not product.get("variants"):
        return [rejection(raw_id, "missing_identity", "Brand, product ID, handle, and variants are required", product)]
    records = []
    for variant in product["variants"]:
        try:
            if not variant.get("id") or not clean(variant.get("sku")):
                raise ValueError("Variant needs an explicit ID and SKU")
            if any(clean(variant.get(name)) for name in ("selling_plan", "selling_plan_id")):
                raise ValueError("Conditional selling-plan price cannot become a public offer")
            specs, raw_specs = _resolve_specs(product, variant)
            url = f"{ALLIT_URL}/products/{product['handle']}?{urlencode({'variant': variant['id']})}"

            def proof(raw, method="structured"):
                return {"source_url": url, "observed_at": observed_at, "method": method, "raw_value": str(raw)}

            configuration = {"brand": brand, "manufacturer_part_number": part, "title": f"{brand} {part} — {clean(variant.get('title'))}",
                             "product_type": "laptop", "identity_scope": "exact_variant", "evidence": {
                                 "brand": proof(brand), "manufacturer_part_number": proof(title, "title"),
                                 "product_type": proof(product.get("product_type") or title),
                                 "identity_scope": proof(f"Product {raw_id}, variant {variant['id']}, SKU {variant['sku']}")}}
            mapping = {"processor": "cpu_model", "graphics": "gpu_model", "memory": "memory", "storage": "storage", "display": "display"}
            for old, new in mapping.items():
                value = specs[old]
                if value and (old != "display" or value["label"]):
                    configuration[new] = value
                    configuration["evidence"][new] = proof(*raw_specs[old])
            if "graphics" in raw_specs:
                gpu_raw, gpu_method = raw_specs["graphics"]
                for name, value in gpu_details(gpu_raw, bounded=gpu_method != "title").items():
                    if value is not None and value != "unknown":
                        configuration[name] = value
                        configuration["evidence"][name] = proof(gpu_raw, gpu_method)
            available = variant.get("available")
            availability = "in_stock" if available is True else "out_of_stock" if available is False else "unknown"
            offer = {"source_product_id": str(raw_id), "variant_id": str(variant["id"]), "seller": "ALL IT",
                     "url": url, "price_myr": variant.get("price"), "currency": "MYR", "price_basis": "public",
                     "condition": "new", "availability": availability, "observed_at": observed_at, "evidence": {}}
            for name in ("source_product_id", "variant_id", "seller", "url", "price_basis"):
                raw = {"seller": ALLIT_URL, "condition": f"product_type={product.get('product_type')}; title={title}", "price_basis": "Public Shopify variant price"}.get(name, offer[name])
                offer["evidence"][name] = proof(raw)
            if condition_evidence and condition_evidence.get("raw_value") in {"https://schema.org/NewCondition", "http://schema.org/NewCondition"}:
                offer["evidence"]["condition"] = deepcopy(condition_evidence)
            image = shopify_photo(product, variant, url)
            if image:
                offer["image_url"] = image
                offer["evidence"]["image_url"] = proof(image)
            offer["evidence"]["price"] = proof(variant.get("price"))
            if availability != "unknown":
                offer["evidence"]["availability"] = proof(f"available={available}")
            records.append({"configuration": configuration, "offer": offer})
        except (ValueError, TypeError) as error:
            records.append(rejection(variant.get("sku") or raw_id, "conflicting_specifications", str(error), {"product": product, "variant": variant}))
    return records


def new_condition_proof(html, url, observed_at):
    soup = BeautifulSoup(html, "lxml")
    offers = []

    def visit(value):
        if isinstance(value, dict):
            if value.get("@type") == "Offer":
                offers.append(value)
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        try:
            visit(json.loads(script.string or script.get_text()))
        except (ValueError, TypeError):
            continue
    if not offers or any(offer.get("itemCondition") not in {"https://schema.org/NewCondition", "http://schema.org/NewCondition"} for offer in offers):
        raise ValueError("Product page does not explicitly establish new condition for every offer")
    return {"source_url": url, "observed_at": observed_at, "method": "structured", "raw_value": "https://schema.org/NewCondition"}


def collect_allit(*, session=None, clock=now, sleep=time.sleep, page_size=30, max_pages=100):
    started = clock()
    records, seen_products = [], set()
    session = session or requests.Session()
    session.headers.update({"User-Agent": "LaptopPicker/1.0 (+public laptop comparison)", "Accept": "application/json"})
    def get(url, accept="application/json"):
        for attempt in range(3):
            try:
                response = session.get(url, timeout=20, headers={"Accept": accept})
                if response.status_code != 429 and response.status_code < 500:
                    response.raise_for_status()
                    return response
                response.raise_for_status()
            except requests.RequestException:
                if attempt == 2 or ('response' in locals() and response.status_code in {401, 403, 404}):
                    raise
            sleep(2 ** attempt)
        raise ValueError("Request retries exhausted")

    error = None
    status = "complete"
    for page in range(1, max_pages + 1):
        url = f"{ALLIT_URL}/collections/laptop/products.json?limit={page_size}&page={page}"
        try:
            response = get(url)
            payload = response.json()
            if not isinstance(payload, dict) or not isinstance(payload.get("products"), list):
                raise ValueError("Response does not contain a products list")
            products = payload["products"]
            observed = clock()
            if not products:
                break
            ids = [str(product.get("id") or "") for product in products]
            if not all(ids) or len(set(ids)) != len(ids) or any(item in seen_products for item in ids):
                raise ValueError("Missing/repeated product IDs: pagination cannot be certified complete")
            seen_products.update(ids)
            for product in products:
                preliminary = allit_records(product, observed)
                if not any("offer" in item for item in preliminary):
                    records.extend(preliminary)
                    continue
                product_url = f"{ALLIT_URL}/products/{product['handle']}"
                condition_response = get(product_url, accept="text/html")
                condition_response.raise_for_status()
                try:
                    condition = new_condition_proof(condition_response.text, product_url, clock())
                except ValueError as unknown_condition:
                    records.append(rejection(product.get("id"), "unknown_condition", str(unknown_condition), product))
                    continue
                # Re-read price AFTER condition evidence so no later evidence is attached to an older price.
                detail_response = get(product_url + ".json")
                detail_response.raise_for_status()
                detail = detail_response.json().get("product")
                if not isinstance(detail, dict) or str(detail.get("id")) != str(product.get("id")):
                    raise ValueError("Product detail does not match its listing identity")
                records.extend(allit_records(detail, clock(), condition_evidence=condition))
            if len(products) < page_size:
                break
            if page == max_pages:
                raise ValueError("Pagination reached safety limit before completion")
            sleep(0.5)
        except (requests.RequestException, ValueError, TypeError, AttributeError) as failure:
            error = str(failure)
            status = "partial" if records else "failed"
            break
    return SourceResult("allit", status, records, started_at=started, finished_at=clock(), error=error)


def match_catalog(build):
    """Group only fully described, equivalent manufacturer configurations across sellers."""
    catalog = deepcopy(build.catalog)
    configurations = {row["id"]: row for row in catalog["configurations"]}
    groups = {}
    for offer in catalog["offers"]:
        configuration = configurations[offer["configuration_id"]]
        display = configuration["display"]
        complete = (configuration["cpu_model"] and configuration["gpu_model"]
                    and configuration["gpu_kind"] != "unknown"
                    and (configuration["gpu_kind"] != "discrete" or configuration["vram_gb"] is not None)
                    and configuration["memory"]["capacity_gb"] and configuration["storage"]["capacity_gb"]
                    and all(display[name] is not None for name in ("diagonal_inches", "resolution_width", "resolution_height", "refresh_hz")))
        if complete:
            facts = {name: value for name, value in configuration.items() if name not in {"id", "title", "evidence"}}
            key = json.dumps(facts, sort_keys=True)
        else:
            key = configuration["id"]
        groups.setdefault(key, []).append(offer)
    retained, remap = [], {}
    for offers in groups.values():
        # Earliest proof is valid for every later offer; never choose a longer description.
        earliest = min(offers, key=lambda item: (datetime.fromisoformat(item["observed_at"].replace("Z", "+00:00")), item["id"]))
        canonical = deepcopy(configurations[earliest["configuration_id"]])
        retained.append(canonical)
        for offer in offers:
            remap[offer["configuration_id"]] = canonical["id"]
            offer["configuration_id"] = canonical["id"]
    catalog["configurations"] = sorted(retained, key=lambda item: item["id"])
    for observation in catalog["observations"]:
        observation["configuration_id"] = remap[observation["configuration_id"]]
    validate_catalog(catalog)
    return type(build)(catalog, deepcopy(build.diagnostics))


def collect_sources(source_ids, **kwargs):
    """Unqualified integrations return an explicit deferred report without collecting."""
    results = []
    for source_id in source_ids:
        if source_id not in SOURCE_IDS:
            raise ValueError(f"Unknown source: {source_id}")
        if source_id == "allit":
            results.append(collect_allit(**kwargs))
        else:
            results.append(SourceResult(source_id, "not_run", mode="deferred",
                                        error="Source is deferred until a variant-safe adapter and source audit are available"))
    return results
