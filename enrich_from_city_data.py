"""
enrich_from_city_data.py

One-time script to enrich bloomington_rents_master.csv with data
from the City of Bloomington address dataset.

Adds / improves:
  - lat / lng         (official GIS coords, more accurate than Nominatim)
  - property_type     (from Location Use Type field)
  - address_matched   (True/False — whether a city match was found)

Run once:  python enrich_from_city_data.py

Then re-run whenever you get an updated city dataset.
"""

import csv
import re
import os

MASTER_FILE  = "data/bloomington_rents_master.csv"
CITY_FILE    = "data/city_addresses.csv"   # rename your city CSV to this
OUTPUT_FILE  = "data/bloomington_rents_master.csv"  # overwrites in place

# ── Address normalization ─────────────────────────────────────────────────────
# Both datasets need to be normalized the same way before matching.
# Strategy: extract just the street number + normalized street name,
# ignore unit/apt/suite designators entirely.

STREET_ABBREVS = [
    # Street types
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
    # Directions
    (r"\bnorth\b",     "n"),
    (r"\bsouth\b",     "s"),
    (r"\beast\b",      "e"),
    (r"\bwest\b",      "w"),
    # Common scraper abbreviations not in city data
    (r"\bave\b",       "ave"),
    (r"\bblvd\b",      "blvd"),
    (r"\bcr\b",        "cir"),
    (r"\bct\b",        "ct"),
    (r"\bdr\b",        "dr"),
    (r"\bln\b",        "ln"),
    (r"\bpl\b",        "pl"),
    (r"\brd\b",        "rd"),
    (r"\bst\b",        "st"),
    # Street name shortening fixes
    (r"\bgr\b",        "grove"),    # "cottage gr" → "cottage grove"
    (r"\bgrov\b",      "grove"),
]

# Unit designators to strip — expanded list
UNIT_PATTERN = re.compile(
    r"[-–#]?\s*"
    r"(unit|unt|apt|apartment|suite|ste|ph|penthouse|"
    r"rm|room|whole\s+house|bldg|building|fl|floor|"
    r"lot|space|sp|#)"
    r"\s*[\w\d]*.*$",
    re.I
)

# Trailing single letter/number unit like "- A", "- 2B", "- 1"
TRAILING_UNIT = re.compile(r"\s*[-–]\s*[a-z0-9]{1,3}\s*$", re.I)

# Duplicate address pattern: "719 N Washington - 719 N Washington"
# Detect when the string before the dash repeats after it
DUPLICATE_ADDR = re.compile(r"^(.+?)\s*[-–]\s*\1.*$", re.I)

def fix_half_address(s):
    """Convert "408.5" → "408 1/2" and "221.5" → "221 1/2" to match city data."""
    return re.sub(r"(\d+)\.5\b", r"\1 1/2", s)

def apply_abbrevs(s):
    for pattern, replacement in STREET_ABBREVS:
        s = re.sub(pattern, replacement, s)
    return s

def normalize_address(address):
    """
    Reduce a scraper address to a comparable key.
    Handles all known edge cases from the data.
    """
    if not address:
        return ""

    # Take only the street portion (before the first comma)
    street = address.split(",")[0].lower().strip()

    # Fix .5 addresses before stripping periods
    street = fix_half_address(street)

    # Remove periods
    street = street.replace(".", "")

    # Remove duplicate address pattern e.g. "719 N Washington - 719 N Washington"
    dup_match = DUPLICATE_ADDR.match(street)
    if dup_match:
        street = dup_match.group(1).strip()

    # Remove unit/apt/suite/ph/rm designators
    street = UNIT_PATTERN.sub("", street).strip()

    # Remove trailing single letter/number unit like "- A" or "- 1"
    street = TRAILING_UNIT.sub("", street).strip()

    # Strip trailing dashes and spaces
    street = street.strip("-–").strip()

    # Standardize abbreviations
    street = apply_abbrevs(street)

    # Collapse whitespace
    street = re.sub(r"\s+", " ", street).strip()

    return street


def normalize_city_address(address):
    """Normalize a city dataset address the same way."""
    if not address:
        return ""
    addr = address.lower().strip()
    addr = fix_half_address(addr)
    addr = addr.replace(".", "")
    # Strip unit designators
    addr = re.sub(r"\s+(apt|unit|ste|suite|#|ph)\s*[\w\d]*.*$", "", addr, flags=re.I).strip()
    addr = apply_abbrevs(addr)
    addr = re.sub(r"\s+", " ", addr).strip()
    return addr


def use_type_to_property_type(use_type):
    """
    Map city Location Use Type to our property_type values.
    """
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


# ── Load city dataset into a lookup dict ──────────────────────────────────────

def load_city_lookup():
    """
    Returns a dict: normalized_address → {lat, lng, property_type}
    Loads the full 40k-row city file once, builds the lookup, done.
    """
    print(f"Loading city dataset from {CITY_FILE}...")

    if not os.path.isfile(CITY_FILE):
        print(f"ERROR: {CITY_FILE} not found.")
        print("Rename your city CSV to 'data/city_addresses.csv' and try again.")
        return {}

    lookup = {}
    total = 0
    skipped = 0

    with open(CITY_FILE, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        
        # Print actual column names so we can debug if needed
        print(f"City file columns: {reader.fieldnames}")

        for row in reader:
            total += 1

            # Handle the column names from the sample you showed
            # Try multiple possible column name formats
            raw_address = (
                row.get("Full Street Address") or
                row.get("full_street_address") or
                row.get("ADDRESS") or
                row.get("address") or ""
            ).strip()

            lat = (
                row.get("Latitude") or
                row.get("latitude") or
                row.get("LAT") or ""
            ).strip()

            lng = (
                row.get("Longitude") or
                row.get("longitude") or
                row.get("LON") or
                row.get("LNG") or ""
            ).strip()

            use_type = (
                row.get("Location Use Type") or
                row.get("location_use_type") or
                row.get("USE_TYPE") or ""
            ).strip()

            if not raw_address:
                skipped += 1
                continue

            key = normalize_city_address(raw_address)
            if not key:
                skipped += 1
                continue

            lookup[key] = {
                "lat":           lat,
                "lng":           lng,
                "property_type": use_type_to_property_type(use_type),
                "raw_address":   raw_address,
            }

    print(f"City lookup built: {len(lookup):,} unique normalized addresses "
          f"({total:,} rows, {skipped} skipped)\n")
    return lookup


# ── Enrich master CSV ──────────────────────────────────────────────────────────

def main():
    if not os.path.isfile(MASTER_FILE):
        print(f"Master file not found: {MASTER_FILE}")
        return

    city_lookup = load_city_lookup()
    if not city_lookup:
        return

    print(f"Loading master CSV from {MASTER_FILE}...")
    with open(MASTER_FILE, newline="", encoding="utf-8") as f:
        reader   = csv.DictReader(f)
        rows     = list(reader)
        fieldnames = list(reader.fieldnames or [])

    print(f"Loaded {len(rows):,} rows\n")

    # Add new columns if not already present
    for col in ["lat", "lng", "property_type", "address_matched"]:
        if col not in fieldnames:
            fieldnames.append(col)

    matched   = 0
    improved_coords  = 0
    improved_type    = 0
    unmatched = 0

    for row in rows:
        key = normalize_address(row.get("address", ""))
        city_row = city_lookup.get(key)

        if city_row:
            matched += 1
            row["address_matched"] = "True"

            # Always use city coords — they're official GIS data
            if city_row["lat"] and city_row["lng"]:
                if row.get("lat") != city_row["lat"]:
                    improved_coords += 1
                row["lat"] = city_row["lat"]
                row["lng"] = city_row["lng"]

            # Use city property type if we have one
            if city_row["property_type"]:
                if row.get("property_type") != city_row["property_type"]:
                    improved_type += 1
                row["property_type"] = city_row["property_type"]

        else:
            row["address_matched"] = row.get("address_matched", "False")
            if not row.get("address_matched"):
                row["address_matched"] = "False"
            unmatched += 1

    # Results
    print(f"── Match Results ─────────────────────────────")
    print(f"  Matched to city data:    {matched:,} ({matched/len(rows)*100:.1f}%)")
    print(f"  Unmatched:               {unmatched:,} ({unmatched/len(rows)*100:.1f}%)")
    print(f"  Coordinates improved:    {improved_coords:,}")
    print(f"  Property types updated:  {improved_type:,}")

    # Write enriched file
    print(f"\nWriting enriched master file...")
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Done. Enriched data saved to {OUTPUT_FILE}")
    print(f"\nNOTE: {unmatched:,} unmatched rows still have their original")
    print(f"Nominatim coordinates and inferred property types.")


if __name__ == "__main__":
    main()