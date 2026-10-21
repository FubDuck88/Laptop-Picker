"""Conservative, shared extraction from explicit specification fields and titles."""

from decimal import Decimal
import hashlib
import json
import re


FAMILY = re.compile(r"\b(?:up to|starting (?:at|from)|varies|configurable)\b", re.I)
NON_LAPTOP = re.compile(r"\b(?:desktop|motherboard|monitor|backpack|charger|headset|handheld|mouse|keyboard cover|docking station)\b", re.I)
FIELDS = ("processor", "graphics", "memory", "storage", "display", "wifi", "battery", "others")


def clean(text):
    return re.sub(r"\s+", " ", str(text or "").replace("®", "").replace("™", "")).strip()


def is_family_level(row):
    # CPU boost-clock phrasing is not a product-family maximum.
    for name in ("title", "graphics", "memory", "storage", "display"):
        if FAMILY.search(str(row.get(name) or "")):
            return True
    return bool(re.match(r"^up to\b", clean(row.get("processor")), re.I))


def is_laptop_listing(title, product_type=""):
    text = clean(title)
    if NON_LAPTOP.search(text) or text.lower() in {"2-in-1 laptops", "gaming laptops", "laptops", "notebooks", "all laptops"}:
        return False
    return bool(text and (product_type.upper() in {"NOTEB", "NB", "LAPTOP", "LAPTOPS", "NOTEBOOK", "NOTEBOOKS"}
                         or re.search(r"\b(?:laptop|notebook|legion|ideapad|thinkpad|vivobook|zenbook|victus|omen|aspire|nitro|expertbook|katana|probook)\b", text, re.I)))


def manufacturer_part_number(title, source_id=""):
    text = clean(title).upper()
    if re.search(r"/\s*[A-Z]{2}\d{4,5}[A-Z]{1,2}\b", text):
        return None
    sku = clean(source_id).upper()
    if "CTO" in sku:
        return None
    # HP supply part numbers are more precise than family/model aliases.
    hp_parts = set(re.findall(r"\b[A-Z0-9]{5}PA(?:#[A-Z0-9]+)?\b", text))
    if hp_parts:
        return next(iter(hp_parts)) if len(hp_parts) == 1 else None
    patterns = [
        r"\b(?:83|82|21|22)[A-Z0-9]{8}\b",
        r"\b\d{2}-[A-Z]{2}\d{4,5}[A-Z]{1,2}\b",
        r"\b(?:A[LNGIV]?\d{2,3}|PHN?\d{2}|PT\d{3}|SFG\d{2})-[A-Z0-9]{2,5}-[A-Z0-9]{3,6}\b",
        r"\b[A-Z][A-Z0-9]{2,7}-\d{3,4}MY\b",
        r"\b(?:FA|FX|GA|GU|G|UX|UM|X|M|B|P|S|E|D)\d{3,4}[A-Z0-9]{0,4}-[A-Z0-9]{4,12}\b",
    ]
    for pattern in patterns:
        matches = set(re.findall(pattern, text))
        if matches:
            return next(iter(matches)) if len(matches) == 1 else None
    for pattern in patterns:
        if re.fullmatch(pattern, sku):
            return sku
    return None


def cpu_model(text):
    text = clean(text)
    if re.match(r"^up to\b", text, re.I):
        return ""
    patterns = [
        (r"\b(i[3579])[-\s]?(\d{4,5}[A-Z]{0,3})\b", lambda m: f"Intel Core {m[1].lower()}-{m[2].upper()}"),
        (r"\b(?:Core\s*Ultra|CU)\s*([3579])[-\s]+(\d{3}[A-Z]{0,3})\b", lambda m: f"Intel Core Ultra {m[1]} {m[2].upper()}"),
        (r"\b(?:Core\s*|C)([3579])[-\s]+(?:processor\s*)?(\d{3}[A-Z]{0,3})\b", lambda m: f"Intel Core {m[1]} {m[2].upper()}"),
        (r"\b(?:Ryzen\s*|R)([3579])[-\s]+(\d{2,4}[A-Z]{0,3})\b", lambda m: f"AMD Ryzen {m[1]} {m[2].upper()}"),
        (r"\bRyzen\s*AI\s*([3579])[-\s]+(\d{3}[A-Z]{0,3})\b", lambda m: f"AMD Ryzen AI {m[1]} {m[2].upper()}"),
        (r"\bAthlon[-\s]*(\d{4}[A-Z]{0,2})\b", lambda m: f"AMD Athlon {m[1].upper()}"),
        (r"\b(N\d{4})\b", lambda m: f"Intel {m[1].upper()}"),
    ]
    values = {render(match) for pattern, render in patterns for match in re.finditer(pattern, text, re.I)}
    return next(iter(values)) if len(values) == 1 else ""


def gpu_model(text):
    text = clean(text)
    if FAMILY.search(text):
        return ""
    values = {f"NVIDIA GeForce {m[1].upper()} {m[2]}{(' ' + m[3].upper()) if m[3] else ''}"
              for m in re.finditer(r"\b(RTX|GTX)\s*(\d{4})(?:\s*(Ti))?\b", text, re.I)}
    if values:
        return next(iter(values)) if len(values) == 1 else ""
    patterns = [r"\bIntel\s+(?:Iris\s*Xe|UHD(?:\s*\d{3})?|Arc(?:\s*\d{3}[A-Z]?)?|Graphics)(?:\s*Graphics)?\b",
                r"\b(?:AMD\s*)?Radeon\s*(?:RX\s*\d{4}[A-Z]*|\d{3}M|Graphics)\b",
                r"\b(?:Qualcomm\s*)?Adreno(?:\s*\d{3})?(?:\s*Graphics)?\b"]
    for pattern in patterns:
        values = {clean(m[0]) for m in re.finditer(pattern, text, re.I)}
        if values:
            return next(iter(values)) if len(values) == 1 else ""
    return ""


def gpu_details(text, *, bounded=False):
    """Extract explicit type/memory evidence, never infer from a GPU model prefix."""
    text = clean(text)
    unknown = {"gpu_kind": "unknown", "vram_gb": None}
    if FAMILY.search(text):
        return unknown
    integrated = bool(re.search(r"\b(?:integrated|iGPU)\b", text, re.I))
    dedicated = bool(re.search(r"\b(?:dedicated|discrete|GDDR\d[A-Z]?)\b", text, re.I))
    if integrated and dedicated:
        return unknown
    kind = "integrated" if integrated else "discrete" if dedicated else "unknown"
    if integrated or re.search(r"\b(?:shared|system memory|RAM|LPDDR\w*|DDR\w*)\b", text, re.I):
        return {"gpu_kind": kind, "vram_gb": None}
    values = {int(m[1]) for m in re.finditer(r"\b(\d+)\s*GB\s*(?:GDDR\d\w*|VRAM)\b", text, re.I)}
    values.update(int(m[1]) for m in re.finditer(r"\bVRAM\s*:?\s*(\d+)\s*GB\b", text, re.I))
    # An isolated graphics field can explicitly state GPU memory without GDDR.
    if bounded and gpu_model(text):
        values.update(int(m[1]) for m in re.finditer(r"\b(\d+)\s*GB\b", text, re.I))
    capacity_gb = next(iter(values)) if len(values) == 1 else None
    if capacity_gb is not None and not 1 <= capacity_gb <= 128:
        capacity_gb = None
    return {"gpu_kind": kind, "vram_gb": capacity_gb}


def capacity(text, kind):
    text = clean(text)
    if FAMILY.search(text):
        return None
    candidates = []
    for match in re.finditer(r"\b(\d+(?:\.\d+)?)\s*(GB|TB)\b", text, re.I):
        amount = Decimal(match[1]) * (1000 if match[2].upper() == "TB" else 1)
        after = text[match.end():]
        trailing_modules = re.match(r"\s*[*x×]\s*(\d+)\b", after, re.I) if kind == 'memory' else None
        if trailing_modules:
            after = after[trailing_modules.end():]
        segment = re.split(r"[/;,|]", text[:match.start()])[-1]
        graphics = bool(re.match(r"\s*(?:GDDR\w*|VRAM)\b", after, re.I) or re.search(r"\b(?:RTX|GTX|GeForce|VRAM)\s*\d*\s*$", segment, re.I))
        ram_type = re.match(r"\s*(LPDDR[45]X?|DDR[345]X?|D[45]|RAM)\b", after, re.I)
        disk_type = re.match(r"\s*(SSD|NVMe|PCIe|HDD|G[345])\b", after, re.I)
        if graphics or (kind == "memory" and (amount > 128 or match[2].upper() == "TB" or disk_type)):
            continue
        if kind == "storage" and (ram_type or (match[2].upper() == "GB" and amount < 128)):
            continue
        # A preceding multiplier denotes installed modules, not separate choices.
        multiplier = re.search(r"\b(\d+)\s*[x×]\s*$", segment, re.I)
        multiplier = multiplier or trailing_modules
        if multiplier:
            amount *= int(multiplier[1])
        label = match[0].replace(" ", "").upper()
        if multiplier:
            label = f"{multiplier[1]}x{label}"
        suffix = ram_type if kind == "memory" else disk_type
        if suffix:
            suffix_value = suffix[1].upper()
            suffix_value = {"D5": "DDR5", "D4": "DDR4"}.get(suffix_value, suffix_value)
            label += " " + suffix_value
        if amount == int(amount):
            candidates.append({"capacity_gb": int(amount), "label": label})
    amounts = {item["capacity_gb"] for item in candidates}
    technologies = {match[0].upper() for item in candidates
                    for match in re.finditer(r"(?:LP)?DDR[345]X?", item["label"], re.I)}
    if len(amounts) != 1 or len(technologies) > 1:
        return None
    # Repeated total/module labels may describe the same installed capacity.
    preferred = sorted(candidates, key=lambda item: (not bool(re.search(r"DDR|SSD|HDD|NVME", item["label"], re.I)), item["label"]))
    return preferred[0] if preferred else None


def display_spec(text):
    text = clean(text)
    text = re.sub(r"\bFull\s+HD\b", "FHD", text, flags=re.I)
    # A stated maximum refresh is not proof of a fixed refresh mode; retain other panel facts.
    text = re.sub(r"up to\s*\d+(?:\.\d+)?\s*Hz", "", text, flags=re.I)
    result = {"diagonal_inches": None, "resolution_width": None, "resolution_height": None, "refresh_hz": None, "label": None}
    if not text or FAMILY.search(text):
        return result
    sizes = set(re.findall(r'\b(1[0-9](?:\.\d)?)\s*(?:["”]|inch(?:es)?\b|(?=FHD|WUXGA|QHD|WQXGA|OLED))', text, re.I))
    resolutions = set(re.findall(r"\b(\d{3,5})\s*[x×]\s*(\d{3,5})\b", text, re.I))
    refresh = set(re.findall(r"\b(\d{2,3})\s*Hz\b", text, re.I))
    alias = re.search(r"\b(WUXGA|WQXGA|FHD|QHD)\b(?!\+)", text, re.I)
    if not resolutions and alias:
        resolutions.add({"FHD": ("1920", "1080"), "WUXGA": ("1920", "1200"), "QHD": ("2560", "1440"), "WQXGA": ("2560", "1600")}[alias[1].upper()])
    if len(sizes) > 1 or len(resolutions) > 1 or len(refresh) > 1:
        return result
    if sizes:
        result["diagonal_inches"] = float(next(iter(sizes)))
    if resolutions:
        width, height = next(iter(resolutions))
        result["resolution_width"], result["resolution_height"] = int(width), int(height)
    if refresh:
        result["refresh_hz"] = int(next(iter(refresh)))
    if any(value is not None for name, value in result.items() if name != "label"):
        parts = []
        if sizes: parts.append(f'{next(iter(sizes))} inch')
        if resolutions: parts.append(f'{width}x{height}')
        if refresh: parts.append(f'{next(iter(refresh))}Hz')
        panel = re.search(r"\b(OLED|IPS(?:-Level)?|TN|VA)\b", text, re.I)
        if panel: parts.append(panel[0].upper())
        result["label"] = " ".join(parts)
    return result


def title_specs(title):
    memory, storage, display = capacity(title, "memory"), capacity(title, "storage"), display_spec(title)
    return {"processor": cpu_model(title), "graphics": gpu_model(title),
            "memory": memory["label"] if memory else "", "storage": storage["label"] if storage else "",
            "display": display["label"] or "", "wifi": "", "battery": "", "others": ""}


def hardware_signature(row):
    cpu, gpu = cpu_model(row.get("processor")), gpu_model(row.get("graphics"))
    memory, storage = capacity(row.get("memory"), "memory"), capacity(row.get("storage"), "storage")
    display = display_spec(row.get("display"))
    if not (cpu and gpu and memory and storage and display["diagonal_inches"] and display["resolution_width"]):
        return None
    # Retain exact known RAM/storage technology and display refresh; do not collapse unknowns into known facts.
    return (cpu.casefold(), gpu.casefold(), clean(row.get("graphics")).casefold(), memory["capacity_gb"], memory["label"].casefold(),
            storage["capacity_gb"], storage["label"].casefold(), display["diagonal_inches"],
            display["resolution_width"], display["resolution_height"], display["refresh_hz"], display["label"].casefold())


def comparison_key(row):
    part = manufacturer_part_number(row.get("title"), row.get("id"))
    signature = hardware_signature(row)
    if part and signature:
        payload = [part, signature]
    else:
        payload = [row.get("source_file"), row.get("id"), row.get("url"), row.get("title")]
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:20]
    return f"{part or 'listing'}_{digest}"
