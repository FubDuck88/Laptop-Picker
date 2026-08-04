import csv
import re

rows = list(csv.DictReader(open("master_laptops.csv", encoding="utf-8")))
print(f"Total rows in master_laptops.csv: {len(rows)}")

cpus = set()
gpus = set()
mems = set()
stos = set()
disps = set()
stores = set()

for r in rows:
    if r.get("series"):
        stores.add(r["series"])
    
    cpu_str = r.get("processor", "").replace("®","").replace("™","").replace("©","")
    gpu_str = r.get("graphics", "").replace("®","").replace("™","").replace("©","")
    mem_str = r.get("memory", "")
    sto_str = r.get("storage", "")
    disp_str = r.get("display", "").replace("“",'"').replace("”",'"').replace("″",'"')

    # CPU series checks
    for c in [
        "Core Ultra 9", "Core Ultra 7", "Core Ultra 5",
        "Core i9", "Core i7", "Core i5", "Core i3",
        "Core 9", "Core 7", "Core 5", "Core 3",
        "Ryzen AI 9", "Ryzen AI 7", "Ryzen AI 5",
        "Ryzen 9", "Ryzen 7", "Ryzen 5", "Ryzen 3",
        "Snapdragon"
    ]:
        if c.lower() in cpu_str.lower():
            cpus.add(c)

    # GPU checks
    for g in [
        "RTX 5090", "RTX 5080", "RTX 5070 Ti", "RTX 5070", "RTX 5060", "RTX 5050",
        "RTX 4090", "RTX 4080", "RTX 4070", "RTX 4060", "RTX 4050",
        "RTX 3070", "RTX 3060", "RTX 3050", "MX330",
        "Radeon", "Arc", "Iris Xe", "Adreno", "UHD", "Integrated"
    ]:
        if g.lower() in gpu_str.lower():
            gpus.add(g)

    # Memory checks
    for m in ["8GB", "16GB", "24GB", "32GB", "48GB", "64GB", "96GB", "128GB"]:
        if m.lower() in mem_str.lower() or m.replace("GB"," GB").lower() in mem_str.lower():
            mems.add(m)

    # Storage checks
    for s in ["256GB", "512GB", "1TB", "2TB", "4TB"]:
        if s.lower() in sto_str.lower() or s.replace("TB"," TB").replace("GB"," GB").lower() in sto_str.lower():
            stos.add(s)

    # Display checks
    disp_m = re.search(r'(\d{2}(?:\.\d)?)["\s]', disp_str)
    if disp_m:
        inch = disp_m.group(1).split('.')[0]
        disps.add(inch)

print("\nStores:", sorted(stores))
print("\nCPUs found in data:", sorted(cpus))
print("\nGPUs found in data:", sorted(gpus))
print("\nMemory sizes found:", sorted(mems, key=lambda x: int(re.sub(r'\D','',x))))
print("\nStorage sizes found:", sorted(stos))
print("\nDisplay sizes found:", sorted(disps, key=lambda x: float(x)))
