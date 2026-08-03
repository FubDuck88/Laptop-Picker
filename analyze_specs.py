import csv

rows = list(csv.DictReader(open('lenovo_laptops.csv', encoding='utf-8')))

print('=== SAMPLE URLS ===')
for r in rows[:5]:
    print(' ', repr(r.get('url', '')[:120]))

print()
print('=== SAMPLE DISPLAY STRINGS ===')
for r in rows[:8]:
    d = r.get('display', '')
    print(' ', repr(d[:80]))
    print('   bytes:', [hex(ord(c)) for c in d[:6]])

print()
print('=== SAMPLE STORAGE STRINGS ===')
for r in rows[:5]:
    print(' ', repr(r.get('storage', '')[:80]))

print()
print('=== SAMPLE PROCESSOR STRINGS ===')
for r in rows[:8]:
    print(' ', repr(r.get('processor', '')[:100]))
