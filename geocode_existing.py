"""
geocode_existing.py

One-time script to geocode all addresses in your master CSV
that don't already have lat/lng coordinates.

Run this once:  python geocode_existing.py

Uses Nominatim (OpenStreetMap) — free, no API key needed.
Rate limited to 1 request/second to respect their terms of service.

After this runs, bloomington_rents_master.csv will have
lat and lng columns on every row that could be geocoded.
"""

import csv
import re
import time
import os
import requests
from datetime import datetime

MASTER_FILE = "data/bloomington_rents_master.csv"
CACHE_FILE  = "data/geocode_cache.csv"  # address → lat/lng cache

HEADERS = {
    "User-Agent": "BedData-Bloomington/1.0 (rental market research)"
}

# ── Geocode cache ─────────────────────────────────────────────────────────────
# Saves every geocoded address so we never hit the API twice for the same one.

def load_cache():
    cache = {}
    if not os.path.isfile(CACHE_FILE):
        return cache
    with open(CACHE_FILE, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cache[row["address"]] = (row["lat"], row["lng"])
    return cache


def save_to_cache(address, lat, lng):
    file_exists = os.path.isfile(CACHE_FILE) and os.path.getsize(CACHE_FILE) > 0
    with open(CACHE_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["address", "lat", "lng"])
        if not file_exists:
            writer.writeheader()
        writer.writerow({"address": address, "lat": lat, "lng": lng})


# ── Geocoder ──────────────────────────────────────────────────────────────────

def clean_address(address):
    """
    Strip unit/apt designators from the street portion so
    Nominatim can find the base building address.
    Preserves city, state, ZIP from the rest of the address.

    e.g. "317 W. 13th Street - Unit 2, Bloomington, IN 47404"
      -> "317 W 13th Street, Bloomington, IN 47404"
    """
    parts = [p.strip() for p in address.split(",")]
    street = parts[0]

    # Remove unit/apt/suite designators from the street part
    street = re.sub(
        r"[-]?\s*(unit|apt\.?|apartment|suite|ste\.?|#)\s*[\w\d]+",
        "", street, flags=re.I
    ).strip().strip("-").strip()

    # Remove trailing "- N" style unit numbers
    street = re.sub(r"\s*[-]\s*\d+[A-Za-z]?\s*$", "", street).strip()

    # Rebuild with city/state/zip
    city_state_zip = ", ".join(parts[1:]) if len(parts) > 1 else "Bloomington, IN"

    return f"{street}, {city_state_zip}"


def geocode(address, cache):
    """
    Returns (lat, lng) string tuple or ("", "") if not found.
    Checks cache first, then calls Nominatim API.
    Tries the full cleaned address first, then falls back to
    just street + city if that fails.
    """
    if address in cache:
        return cache[address]

    cleaned = clean_address(address)

    # Build fallback: just street number + street name + Bloomington IN
    parts = cleaned.split(",")
    street_only = f"{parts[0].strip()}, Bloomington, IN, USA"

    for query in [cleaned, street_only]:
        try:
            resp = requests.get(
                "https://nominatim.openstreetmap.org/search",
                params={
                    "q":            query,
                    "format":       "json",
                    "limit":        1,
                    "countrycodes": "us",
                    "addressdetails": 1
                },
                headers=HEADERS,
                timeout=10
            )
            results = resp.json()
            if results:
                lat = results[0]["lat"]
                lng = results[0]["lon"]
                save_to_cache(address, lat, lng)
                cache[address] = (lat, lng)
                return lat, lng
            time.sleep(1.0)  # wait between fallback attempts
        except Exception as e:
            print(f"    Geocode error for '{address}': {e}")

    # Cache the failure so we don't retry every time
    save_to_cache(address, "", "")
    cache[address] = ("", "")
    return "", ""


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    if not os.path.isfile(MASTER_FILE):
        print(f"Master file not found: {MASTER_FILE}")
        return

    print(f"Loading {MASTER_FILE}...")
    with open(MASTER_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        existing_fields = reader.fieldnames or []

    # Add lat/lng to fieldnames if not already there
    fieldnames = list(existing_fields)
    if "lat" not in fieldnames:
        fieldnames.append("lat")
    if "lng" not in fieldnames:
        fieldnames.append("lng")

    print(f"Loaded {len(rows)} rows")

    cache = load_cache()
    print(f"Geocode cache: {len(cache)} addresses already cached\n")

    # Find rows that need geocoding
    needs_geocoding = [r for r in rows if not r.get("lat") or not r.get("lng")]
    already_done    = len(rows) - len(needs_geocoding)

    print(f"Already geocoded: {already_done}")
    print(f"Need geocoding:   {len(needs_geocoding)}")

    if not needs_geocoding:
        print("\nAll rows already have coordinates. Nothing to do.")
        return

    # Estimate time
    estimated_mins = len(needs_geocoding) / 60
    print(f"Estimated time:   ~{estimated_mins:.0f} minutes at 1 req/sec\n")
    print("Starting geocoding...\n")

    geocoded   = 0
    failed     = 0
    from_cache = 0

    for i, row in enumerate(rows):
        if row.get("lat") and row.get("lng"):
            continue  # already has coords

        address = row.get("address", "").strip()
        if not address:
            row["lat"] = ""
            row["lng"] = ""
            failed += 1
            continue

        # Check cache first (no API call needed)
        if address in cache:
            row["lat"], row["lng"] = cache[address]
            from_cache += 1
            continue

        # Call the API
        lat, lng = geocode(address, cache)
        row["lat"] = lat
        row["lng"] = lng

        if lat and lng:
            geocoded += 1
            status = f"✓ {float(lat):.4f}, {float(lng):.4f}"
        else:
            failed += 1
            status = "✗ not found"

        # Progress update every 50 rows
        if (i + 1) % 50 == 0:
            print(f"  Progress: {i+1}/{len(rows)} rows "
                  f"({geocoded} geocoded, {from_cache} from cache, {failed} failed)")

        time.sleep(1.0)  # Nominatim rate limit — do not reduce this

    # Write updated file
    print(f"\nWriting updated file...")
    with open(MASTER_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n── Complete ─────────────────────────────")
    print(f"  Geocoded via API:   {geocoded}")
    print(f"  Loaded from cache:  {from_cache}")
    print(f"  Failed / no result: {failed}")
    print(f"  Total rows:         {len(rows)}")
    print(f"\nCoordinates saved to {MASTER_FILE}")
    print(f"Cache saved to {CACHE_FILE}")


if __name__ == "__main__":
    main()