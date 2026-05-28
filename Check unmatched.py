"""
check_unmatched.py
Run this to see WHY the 253 addresses didn't match,
so we can tune the normalizer to catch more of them.
"""
import csv, re, os

MASTER_FILE = "data/bloomington_rents_master.csv"
CITY_FILE   = "data/city_addresses.csv"

STREET_ABBREVS = {
    "street": "st", "avenue": "ave", "drive": "dr",
    "lane": "ln", "land": "ln", "court": "ct",
    "place": "pl", "boulevard": "blvd", "road": "rd",
    "circle": "cir", "north": "n", "south": "s",
    "east": "e", "west": "w",
}

def normalize(address):
    street = address.split(",")[0].lower().replace(".", "")
    street = re.sub(r"[-]?\s*(unit|apt|apartment|suite|ste|#)\s*[\w\d]*.*$", "", street).strip()
    street = re.sub(r"\s*[-]\s*\d+[a-z]?\s*$", "", street).strip()
    for word, abbrev in STREET_ABBREVS.items():
        street = re.sub(r"\b" + word + r"\b", abbrev, street)
    return re.sub(r"\s+", " ", street).strip()

# Load city lookup
city_lookup = set()
with open(CITY_FILE, newline="", encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        raw = (row.get("Full Street Address") or "").strip()
        if raw:
            city_lookup.add(normalize(raw))

# Find unmatched master rows
unmatched = []
with open(MASTER_FILE, newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        if row.get("address_matched") != "True":
            key = normalize(row.get("address", ""))
            unmatched.append((row.get("address", ""), key))

print(f"Total unmatched: {len(unmatched)}\n")
print("Sample of unmatched normalized keys:")
seen = set()
for raw, key in unmatched:
    if key not in seen:
        seen.add(key)
        print(f"  Raw:        {raw[:80]}")
        print(f"  Normalized: {key}")
        print()
    if len(seen) >= 30:
        break

# Look for near-misses in city data
print("\n── Potential near-misses ─────────────────────")
print("(city keys that start with the same street number)\n")
for raw, key in list(unmatched)[:15]:
    # Get the street number
    num_match = re.match(r"(\d+)", key)
    if not num_match:
        continue
    num = num_match.group(1)
    # Find city keys with same number
    candidates = [c for c in city_lookup if c.startswith(num + " ")][:3]
    if candidates:
        print(f"  Unmatched: {key}")
        print(f"  City candidates: {candidates}")
        print()