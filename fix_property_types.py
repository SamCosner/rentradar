"""
fix_property_types.py

One-time script to correct property_type for all existing Supabase listings
using the authoritative city address database.

Run: python fix_property_types.py
"""

import csv, re, os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

supabase = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])

CITY_FILE = "data/city_addresses.csv"

STREET_ABBREVS = [
    (r"\bstreet\b",    "st"),
    (r"\bavenue\b",    "ave"),
    (r"\bdrive\b",     "dr"),
    (r"\blane\b",      "ln"),
    (r"\bland\b",      "ln"),
    (r"\bcourt\b",     "ct"),
    (r"\bplace\b",     "pl"),
    (r"\bboulevard\b", "blvd"),
    (r"\broad\b",      "rd"),
    (r"\bcircle\b",    "cir"),
    (r"\bway\b",       "way"),
    (r"\bnorth\b",     "n"),
    (r"\bsouth\b",     "s"),
    (r"\beast\b",      "e"),
    (r"\bwest\b",      "w"),
    (r"\bgr\b",        "grove"),
    (r"\bgrov\b",      "grove"),
]

UNIT_PATTERN = re.compile(
    r"[-–#]?\s*"
    r"(unit|unt|apt|apartment|suite|ste|ph|penthouse|"
    r"rm|room|whole\s+house|bldg|building|fl|floor|"
    r"lot|space|sp|#)"
    r"\s*[\w\d]*.*$",
    re.I
)
TRAILING_UNIT = re.compile(r"\s*[-–]\s*[a-z0-9]{1,3}\s*$", re.I)
DUPLICATE_ADDR = re.compile(r"^(.+?)\s*[-–]\s*\1.*$", re.I)


def fix_half_address(s):
    return re.sub(r"(\d+)\.5\b", r"\1 1/2", s)


def apply_abbrevs(s):
    for pattern, replacement in STREET_ABBREVS:
        s = re.sub(pattern, replacement, s)
    return s


def normalize_address(address):
    if not address:
        return ""
    street = address.split(",")[0].lower().strip()
    street = fix_half_address(street)
    street = street.replace(".", "")
    dup_match = DUPLICATE_ADDR.match(street)
    if dup_match:
        street = dup_match.group(1).strip()
    street = UNIT_PATTERN.sub("", street).strip()
    street = TRAILING_UNIT.sub("", street).strip()
    street = street.strip("-–").strip()
    street = apply_abbrevs(street)
    street = re.sub(r"\s+", " ", street).strip()
    return street


def use_type_to_property_type(use_type):
    if not use_type:
        return ""
    u = use_type.lower()
    if "single family" in u or "single-family" in u:
        return "House"
    if "multi" in u or "apartment" in u or "condo" in u:
        return "Apartment"
    if "duplex" in u or "two family" in u or "2 family" in u:
        return "Duplex/Triplex"
    if "triplex" in u or "three family" in u or "3 family" in u:
        return "Duplex/Triplex"
    if "townhouse" in u or "townhome" in u:
        return "Apartment"
    if "mobile" in u:
        return "House"
    return ""


def load_city_lookup():
    print(f"Loading city dataset from {CITY_FILE}...")
    if not os.path.isfile(CITY_FILE):
        print(f"ERROR: {CITY_FILE} not found.")
        return {}
    lookup = {}
    with open(CITY_FILE, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            raw = (row.get("Full Street Address") or "").strip()
            if not raw:
                continue
            use_type = (row.get("Location Use Type") or "").strip()
            prop_type = use_type_to_property_type(use_type)
            if not prop_type:
                continue
            key = normalize_address(raw)
            if key:
                lookup[key] = prop_type
    print(f"City lookup built: {len(lookup):,} entries with a property type\n")
    return lookup


def fetch_all_listings():
    """Fetch every row from Supabase, return list of dicts."""
    print("Fetching all listings from Supabase...")
    rows = []
    page_size = 1000
    offset = 0
    while True:
        result = supabase.table("listings").select("url,address,company,property_type").range(offset, offset + page_size - 1).execute()
        rows.extend(result.data)
        if len(result.data) < page_size:
            break
        offset += page_size
    print(f"Fetched {len(rows):,} rows\n")
    return rows


def main():
    city_lookup = load_city_lookup()
    if not city_lookup:
        return

    listings = fetch_all_listings()

    # Build correction map: url → correct property_type
    # For listings without a url, fall back to company+address key
    url_corrections = {}    # url → new_property_type
    addr_corrections = {}   # "company|address" → new_property_type

    no_match = 0
    for row in listings:
        key = normalize_address(row.get("address", ""))
        new_type = city_lookup.get(key)
        if not new_type:
            no_match += 1
            continue

        url = (row.get("url") or "").strip()
        if url:
            url_corrections[url] = new_type
        else:
            fallback_key = f'{row.get("company","").strip()}|{row.get("address","").strip()}'
            addr_corrections[fallback_key] = new_type

    print(f"Addresses matched in city DB: {len(url_corrections) + len(addr_corrections):,}")
    print(f"Addresses not matched:        {no_match:,}\n")

    # Apply corrections via targeted Supabase UPDATEs
    updated = 0

    print(f"Updating {len(url_corrections):,} unique URLs in Supabase...")
    for url, new_type in url_corrections.items():
        supabase.table("listings").update({"property_type": new_type}).eq("url", url).execute()
        updated += 1
        if updated % 100 == 0:
            print(f"  {updated} URLs updated...")

    print(f"Updating {len(addr_corrections):,} company+address rows...")
    for combo, new_type in addr_corrections.items():
        company, address = combo.split("|", 1)
        supabase.table("listings").update({"property_type": new_type}).eq("company", company).eq("address", address).execute()
        updated += 1

    print(f"\nDone. {updated:,} unique keys updated in Supabase.")
    print(f"{no_match:,} listings had no city DB match and were left unchanged.")


if __name__ == "__main__":
    main()
