import json

path = r"C:\Users\jhoff\.gemini\antigravity-ide\brain\8df0cad1-e401-4b8f-b4c7-0f7ea621fb99\.system_generated\steps\258\content.md"
content = open(path, encoding="utf-8").read()
idx = content.find('{"products":')
data = json.loads(content[idx:])

EXCLUDE_SKU_PREFIXES = ("MB-", "MNT-", "DC-", "KB-", "FG-", "PBM-", "ACC-")
EXCLUDE_KEYWORDS = ("motherboard", "keyboard", "monitor", "desktop", "mousepad", "customized gaming pc", "headset", "bag", "backpack", "pin badge", "luggage", "wifi")

laptops = []

for p in data["products"]:
    title = p.get("title", "").strip()
    p_type = (p.get("product_type") or "").upper()
    tags = [t.lower() for t in p.get("tags", [])]
    variants = p.get("variants", [])
    sku = (variants[0].get("sku") or "") if variants else ""

    if any(sku.startswith(prefix) for prefix in EXCLUDE_SKU_PREFIXES):
        continue
    if any(k in title.lower() for k in EXCLUDE_KEYWORDS):
        continue

    is_laptop = (
        p_type in ("NB", "HANDHELD PCS", "LAPTOPS") or
        "laptop" in title.lower() or
        "handheld" in title.lower() or
        any("laptop" in tag or "notebook" in tag for tag in tags) or
        sku.startswith("NB-") or sku.startswith("GC-")
    )

    if is_laptop:
        laptops.append((sku, title))

print(f"Total strictly filtered laptops: {len(laptops)}")
print("=== STRICT LAPTOPS LIST ===")
for sku, title in laptops:
    print(f"  [{sku}] {title}")
