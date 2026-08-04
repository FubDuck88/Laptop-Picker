import requests
import json

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
}

# 1. Lenovo Image Field
print("=== LENOVO IMAGE FIELDS ===")
url_lenovo = "https://openapi.lenovo.com/my/en/ofp/search/dlp/product/query/get/_tsc"
params_lenovo = {
    "pageFilterId": "47af9ba7-cab2-4e61-9b10-2283ac14c87c",
    "params": json.dumps({"page": "1", "pageSize": 5})
}
try:
    r = requests.get(url_lenovo, params=params_lenovo, headers=headers, timeout=8)
    data = r.json().get("data", {})
    prods = data.get("data", [])[0].get("products", [])
    if prods:
        p0 = prods[0]
        for k, v in p0.items():
            if any(x in k.lower() for x in ["image", "photo", "media", "asset", "src", "pic", "thumb", "img", "url"]):
                print(f"  {k}: {repr(v)[:120]}")
except Exception as e:
    print(f"Lenovo error: {e}")

# 2. MSI Image Field
print("\n=== MSI IMAGE FIELDS ===")
try:
    r = requests.get("https://my-store.msi.com/products.json?limit=3", headers=headers, timeout=8)
    p0 = r.json().get("products", [])[0]
    print(f"  images: {repr(p0.get('images'))[:150]}")
    print(f"  image: {repr(p0.get('image'))[:150]}")
except Exception as e:
    print(f"MSI error: {e}")

# 3. ASUS Image Field
print("\n=== ASUS IMAGE FIELDS ===")
url_asus = "https://odinapi.asus.com/recent-data/apiv2/SeriesFilterResult?CategoryName=&PageIndex=1&PageSize=5&ProductLevel1Code=laptops&SystemCode=asus&WebsiteCode=my&siteID=www"
try:
    r = requests.get(url_asus, headers=headers, timeout=8)
    p0 = r.json().get("Result", {}).get("ProductList", [])[0]
    for k, v in p0.items():
        if any(x in k.lower() for x in ["image", "photo", "media", "asset", "src", "pic", "thumb", "img", "logo"]):
            print(f"  {k}: {repr(v)[:120]}")
except Exception as e:
    print(f"ASUS error: {e}")
