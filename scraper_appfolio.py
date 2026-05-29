import requests
from bs4 import BeautifulSoup
import csv, re, time, os
from datetime import datetime
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ── Geocoding ─────────────────────────────────────────────────────────────────

GEOCODE_CACHE_FILE = "data/geocode_cache.csv"
GEOCODE_HEADERS = {
    "User-Agent": "BedData-Bloomington/1.0 (rental market research)"
}

def load_geocode_cache():
    cache = {}
    if not os.path.isfile(GEOCODE_CACHE_FILE):
        return cache
    with open(GEOCODE_CACHE_FILE, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cache[row["address"]] = (row["lat"], row["lng"])
    return cache


def save_geocode_cache_entry(address, lat, lng):
    file_exists = os.path.isfile(GEOCODE_CACHE_FILE) and os.path.getsize(GEOCODE_CACHE_FILE) > 0
    with open(GEOCODE_CACHE_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["address", "lat", "lng"])
        if not file_exists:
            writer.writeheader()
        writer.writerow({"address": address, "lat": lat, "lng": lng})


def geocode_address(address, cache):
    """Returns (lat, lng) strings. Checks cache first, then Nominatim API."""
    if address in cache:
        return cache[address]

    # Use just the street part for better geocoding accuracy
    clean = address.split(",")[0]
    query = f"{clean}, Bloomington, IN, USA" if "bloomington" not in address.lower() else address

    try:
        resp = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": query, "format": "json", "limit": 1, "countrycodes": "us"},
            headers=GEOCODE_HEADERS,
            timeout=10
        )
        results = resp.json()
        if results:
            lat = results[0]["lat"]
            lng = results[0]["lon"]
            save_geocode_cache_entry(address, lat, lng)
            cache[address] = (lat, lng)
            time.sleep(1.0)  # Nominatim rate limit
            return lat, lng
    except Exception as e:
        print(f"    Geocode error for '{address}': {e}")

    save_geocode_cache_entry(address, "", "")
    cache[address] = ("", "")
    return "", ""

# ── City address lookup ───────────────────────────────────────────────────────

CITY_FILE = "data/city_addresses.csv"

STREET_ABBREVS = {
    "street": "st", "avenue": "ave", "drive": "dr",
    "lane": "ln", "land": "ln", "court": "ct",
    "place": "pl", "boulevard": "blvd", "road": "rd",
    "circle": "cir", "north": "n", "south": "s",
    "east": "e", "west": "w",
}

def normalize_for_lookup(address):
    street = address.split(",")[0].lower().replace(".", "")
    street = re.sub(r"[-]?\s*(unit|apt|apartment|suite|ste|#)\s*[\w\d]*.*$", "", street).strip()
    street = re.sub(r"\s*[-]\s*\d+[a-z]?\s*$", "", street).strip()
    for word, abbrev in STREET_ABBREVS.items():
        street = re.sub(r"\b" + word + r"\b", abbrev, street)
    return re.sub(r"\s+", " ", street).strip()


def load_city_lookup():
    lookup = {}
    if not os.path.isfile(CITY_FILE):
        return lookup
    with open(CITY_FILE, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            raw = (row.get("Full Street Address") or "").strip()
            if not raw:
                continue
            key = normalize_for_lookup(raw)
            use_type = row.get("Location Use Type", "").lower()
            if "single family" in use_type:
                prop_type = "House"
            elif "multi" in use_type or "apartment" in use_type:
                prop_type = "Apartment"
            elif "duplex" in use_type or "two family" in use_type:
                prop_type = "Duplex/Triplex"
            else:
                prop_type = ""
            lookup[key] = {
                "lat": row.get("Latitude", ""),
                "lng": row.get("Longitude", ""),
                "property_type": prop_type,
            }
    return lookup

# ─────────────────────────────────────────────────────────────────────────────

SITES = [
    ("https://brawley.appfolio.com/listings/listings", "Brawley Property Management"),
    ("https://bloomingtonservices.appfolio.com/listings/listings", "Bloomington Services"),
    ("https://sargeproperties.appfolio.com/listings/listings", "Sarge Properties"),
    ("https://granitesl.appfolio.com/listings/listings", "Granite Solutions"),
    ("https://cedarview.appfolio.com/listings/listings", "Cedar View Properties"),
    ("https://creamandcrimson.appfolio.com/listings/listings", "Cream and Crimson Properties"),
    ("https://pavilion.appfolio.com/listings/listings", "Pavilion Properties"),
    ("https://cpw.appfolio.com/listings/listings", "Mackie Properties"),
    ("https://olympus.appfolio.com/listings/listings", "Olympus Properties"),
    ("https://parkerrealestate.appfolio.com/listings/listings", "Parker Real Estate"),
    ("https://omegaproperties.appfolio.com/listings/listings", "Omega Properties"),
    ("https://regencymultifamily.appfolio.com/listings/listings", "Regency Multifamily"),
    ("https://phoenixpropertymanagement.appfolio.com/listings/listings", "Phoenix Property Management"),
    ("https://rubicondevelopment.appfolio.com/listings/listings", "Rubicon Development"),
    ("https://station11.appfolio.com/listings/listings", "Station 11 Properties"),
    ("https://hoosierchoice.appfolio.com/listings/listings", "Hoosier Choice Properties"),
    ("https://costleyco.appfolio.com/listings/listings", "Costley Company"),
]

MASTER_FILE = "data/bloomington_rents_master.csv"
SNAPSHOT_DIR = "data/snapshots"

# Create folders automatically if they do not exist yet
os.makedirs(SNAPSHOT_DIR, exist_ok=True)

FIELDNAMES = [
    "scraped_date", "scraped_time", "event",
    "company", "address", "property_type",
    "rent", "bedrooms", "bathrooms", "sqft",
    "pets", "parking", "laundry", "utilities_included",
    "available", "url", "lat", "lng"
]

# Fields that are compared to detect a meaningful change
# (scraped_date, scraped_time, and event are excluded on purpose)
CHANGE_FIELDS = ["rent", "bedrooms", "bathrooms", "sqft", "available"]


def infer_property_type(address):
    a = address.upper()
    if re.search(r'\bAPT\.?\b|#\s*\d|\bSUITE\b|\bSTE\b', a):
        return "Apartment"
    unit_match = re.search(r'(?:UNIT|UNT|-)\s*(\d+)', a)
    if unit_match:
        return "Duplex/Triplex" if int(unit_match.group(1)) <= 4 else "Apartment"
    if re.search(r',\s*\d{3,}$', a.strip()):
        return "Apartment"
    return "House"


def extract_amenities(text):
    t = text.lower()
    if re.search(r'no pets|pets not allowed|pet free', t):
        pets = "No"
    elif re.search(r'pets? (ok|allowed|welcome|friendly)|dogs? ok|cats? ok', t):
        pets = "Yes"
    else:
        pets = "Unknown"

    if re.search(r'no parking|street parking only', t):
        parking = "No"
    elif re.search(r'parking|garage|carport|driveway', t):
        parking = "Yes"
    else:
        parking = "Unknown"

    if re.search(r'in.unit laundry|washer.?dryer included|w/d included|in unit w/d', t):
        laundry = "In-unit"
    elif re.search(r'laundry on.?site|shared laundry|laundry room|coin.?op', t):
        laundry = "Shared"
    elif re.search(r'no laundry|laundry not', t):
        laundry = "None"
    else:
        laundry = "Unknown"

    if re.search(r'utilities included|all utilities|water included|heat included', t):
        utilities = "Yes"
    elif re.search(r'utilities not included|tenant pays|renter pays utilities', t):
        utilities = "No"
    else:
        utilities = "Unknown"

    return pets, parking, laundry, utilities


def parse_listing(item, company):
    try:
        link_el = item.find("a", href=re.compile(r"/listings/detail/"))
        link = link_el["href"] if link_el else ""

        addr_el = (item.find(class_=re.compile(r"address|street|location", re.I))
                   or item.find("h2") or item.find("h3"))
        address = addr_el.get_text(" ", strip=True) if addr_el else ""

        full_text = item.get_text(" ")

        rent_match = re.search(r'\$\s*([\d,]+)', full_text)
        rent = rent_match.group(1).replace(",", "") if rent_match else ""

        bed_bath_match = re.search(
            r'(studio|\d+)\s*bd[^/]*/\s*([\d.]+)\s*ba', full_text, re.I)
        if bed_bath_match:
            raw_beds = bed_bath_match.group(1).strip().lower()
            beds = "0" if raw_beds == "studio" else raw_beds
            baths = bed_bath_match.group(2).strip()
        else:
            room_match = re.search(
                r'private\s+room\s+in\s+(\d+)\s*bd[^/]*/\s*([\d.]+)\s*ba',
                full_text, re.I)
            beds = room_match.group(1) if room_match else ""
            baths = room_match.group(2) if room_match else ""

        sqft_match = re.search(r'([\d,]+)\s*sq\.?\s*ft', full_text, re.I)
        sqft = sqft_match.group(1).replace(",", "") if sqft_match else ""

        # Normalize available date
        avail_match = re.search(r'Available\s+([\w/]+)', full_text, re.I)
        available_raw = avail_match.group(1).strip() if avail_match else ""
        if not available_raw or available_raw.upper() == "NOW":
            available = datetime.now().strftime("%Y-%m-%d")
        else:
            try:
                available = datetime.strptime(available_raw, "%m/%d/%y").strftime("%Y-%m-%d")
            except ValueError:
                try:
                    available = datetime.strptime(available_raw, "%m/%d/%Y").strftime("%Y-%m-%d")
                except ValueError:
                    available = available_raw

        property_type = infer_property_type(address) if address else ""
        pets, parking, laundry, utilities = extract_amenities(full_text)

        if not address:
            return None

        return {
            "company":            company,
            "address":            address,
            "property_type":      property_type,
            "rent":               rent,
            "bedrooms":           beds,
            "bathrooms":          baths,
            "sqft":               sqft,
            "pets":               pets,
            "parking":            parking,
            "laundry":            laundry,
            "utilities_included": utilities,
            "available":          available,
            "url":                link,
        }
    except Exception:
        return None


def scrape_site(base_url, company):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    all_results = []
    page = 1
    while True:
        url = base_url if page == 1 else f"{base_url}?page={page}"
        print(f"  Fetching page {page}...")
        try:
            resp = requests.get(url, headers=headers, timeout=15)
        except Exception as e:
            print(f"  Error: {e}")
            break
        if resp.status_code != 200:
            print(f"  HTTP {resp.status_code} — stopping")
            break
        soup = BeautifulSoup(resp.text, "html.parser")
        containers = (soup.select("div.listing-item")
                      or soup.select("article.listing-item")
                      or soup.find_all("div", class_=re.compile(r"listing", re.I)))
        if not containers:
            print(f"  No listings found — stopping")
            break
        page_results = [r for item in containers
                        if (r := parse_listing(item, company)) and r["address"]]
        if not page_results:
            break
        all_results.extend(page_results)
        print(f"  Got {len(page_results)} listings (running total: {len(all_results)})")
        page += 1
        time.sleep(1.5)
    return all_results


def make_key(row):
    """
    Unique key for a listing. Prefer URL since it is most stable.
    Fall back to company + address for rows where URL is blank.
    """
    url = (row.get("url") or "").strip()
    if url:
        return url
    return f'{row.get("company","").strip()}|{row.get("address","").strip()}'


def load_last_seen():
    """Load most recent row per URL from Supabase, falling back to local CSV."""
    last_seen = {}
    try:
        result = supabase.table("listings")\
            .select("*")\
            .neq("event", "removed")\
            .order("scraped_date", desc=True)\
            .execute()
        for row in result.data:
            key = make_key(row)
            if key and key not in last_seen:
                last_seen[key] = row
    except Exception as e:
        print(f"Supabase load error: {e}")
        print("Falling back to local CSV...")
        if os.path.isfile(MASTER_FILE):
            with open(MASTER_FILE, newline="", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    key = make_key(row)
                    if key:
                        last_seen[key] = row
            # Exclude listings whose last event was "removed"
            last_seen = {k: v for k, v in last_seen.items() if v.get("event") != "removed"}
    return last_seen


def has_changed(new_row, old_row):
    """Return True if any tracked field differs between the new and stored row."""
    for field in CHANGE_FIELDS:
        if str(new_row.get(field, "")).strip() != str(old_row.get(field, "")).strip():
            return True
    return False


def append_to_master(rows):
    """Write rows to local CSV backup and Supabase."""
    # Local CSV backup
    file_exists = os.path.isfile(MASTER_FILE) and os.path.getsize(MASTER_FILE) > 0
    with open(MASTER_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if not file_exists:
            writer.writeheader()
            print(f"Created new master file: {MASTER_FILE}")
        writer.writerows(rows)

    # Supabase insert
    supabase_rows = []
    for row in rows:
        supabase_rows.append({
            "scraped_date":       row.get("scraped_date") or None,
            "scraped_time":       row.get("scraped_time") or None,
            "event":              row.get("event") or None,
            "company":            row.get("company") or None,
            "address":            row.get("address") or None,
            "property_type":      row.get("property_type") or None,
            "rent":               float(row["rent"]) if row.get("rent") else None,
            "bedrooms":           float(row["bedrooms"]) if row.get("bedrooms") else None,
            "bathrooms":          float(row["bathrooms"]) if row.get("bathrooms") else None,
            "sqft":               row.get("sqft") or None,
            "pets":               row.get("pets") or None,
            "parking":            row.get("parking") or None,
            "laundry":            row.get("laundry") or None,
            "utilities_included": row.get("utilities_included") or None,
            "available":          row.get("available") or None,
            "url":                row.get("url") or None,
            "lat":                float(row["lat"]) if row.get("lat") else None,
            "lng":                float(row["lng"]) if row.get("lng") else None,
            "address_matched":    row.get("address_matched") or None,
        })

    batch_size = 500
    for i in range(0, len(supabase_rows), batch_size):
        batch = supabase_rows[i:i + batch_size]
        supabase.table("listings").insert(batch).execute()
        print(f"  Inserted batch {i//batch_size + 1} ({len(batch)} rows) to Supabase")


# ── Run ──────────────────────────────────────────────────────────────────────

run_dt = datetime.now()
scraped_date = run_dt.strftime("%Y-%m-%d")
scraped_time = run_dt.strftime("%H:%M:%S")

print(f"Scrape started: {scraped_date} at {scraped_time}\n")

# Load city lookup, geocode cache, and last seen listings
city_lookup = load_city_lookup()
if city_lookup:
    print(f"City lookup loaded: {len(city_lookup):,} addresses")
else:
    print("City lookup not found — will use Nominatim only")
geocode_cache = load_geocode_cache()
last_seen = load_last_seen()

all_listings = []
for url, name in SITES:
    print(f"Scraping {name}...")
    results = scrape_site(url, name)
    all_listings.extend(results)
    print(f"Done: {len(results)} listings\n")

# Filter Bloomington only
bloom_only = [r for r in all_listings if "bloomington" in r["address"].lower()]

# ── Change detection ─────────────────────────────────────────────────────────

rows_to_save = []
current_urls = set()

for r in bloom_only:
    key = make_key(r)
    current_urls.add(key)

    if key not in last_seen:
        # Brand new listing
        rows_to_save.append({
            "scraped_date": scraped_date,
            "scraped_time": scraped_time,
            "event":        "new",
            **r
        })

    elif has_changed(r, last_seen[key]):
        # Something changed — preserve original available date
        r["available"] = last_seen[key]["available"]
        rows_to_save.append({
            "scraped_date": scraped_date,
            "scraped_time": scraped_time,
            "event":        "changed",
            **r
        })

    # else: identical to last run — skip

# ── Detect removed listings ───────────────────────────────────────────────────

for key, old_row in last_seen.items():
    if key not in current_urls:
        # Was there last run, gone now — mark as removed
        rows_to_save.append({
            "scraped_date": scraped_date,
            "scraped_time": scraped_time,
            "event":        "removed",
            **{f: old_row.get(f, "") for f in FIELDNAMES
               if f not in ("scraped_date", "scraped_time", "event")}
        })

# ── Save ──────────────────────────────────────────────────────────────────────

new_count     = sum(1 for r in rows_to_save if r["event"] == "new")
changed_count = sum(1 for r in rows_to_save if r["event"] == "changed")
removed_count = sum(1 for r in rows_to_save if r["event"] == "removed")
skipped_count = len(bloom_only) - new_count - changed_count

print(f"── Summary ──────────────────────────")
print(f"  Total Bloomington listings scraped: {len(bloom_only)}")
print(f"  New listings:     {new_count}")
print(f"  Changed listings: {changed_count}")
print(f"  Removed listings: {removed_count}")
print(f"  Unchanged (skipped): {skipped_count}")
print(f"  Rows saved to master: {len(rows_to_save)}")

# Geocode only new listings — city lookup first, Nominatim as fallback
print("\nGeocoding new listings...")
geo_count = 0
city_count = 0
for row in rows_to_save:
    if row.get("event") == "new" and not row.get("lat"):
        address = row.get("address", "")
        key = normalize_for_lookup(address)
        city_hit = city_lookup.get(key) if city_lookup else None
        if city_hit and city_hit.get("lat"):
            row["lat"] = city_hit["lat"]
            row["lng"] = city_hit["lng"]
            if city_hit.get("property_type"):
                row["property_type"] = city_hit["property_type"]
            city_count += 1
            geo_count += 1
        else:
            lat, lng = geocode_address(address, geocode_cache)
            row["lat"] = lat
            row["lng"] = lng
            if lat:
                geo_count += 1
    elif not row.get("lat"):
        row["lat"] = ""
        row["lng"] = ""

print(f"Geocoded {geo_count} new listings ({city_count} from city data, {geo_count-city_count} from Nominatim)")

if rows_to_save:
    append_to_master(rows_to_save)
    print(f"\nAppended {len(rows_to_save)} rows to {MASTER_FILE}")

    snapshot_file = f"{SNAPSHOT_DIR}/snapshot_{scraped_date}.csv"
    with open(snapshot_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows_to_save)
    print(f"Saved snapshot to {snapshot_file}")
else:
    print("\nNo changes detected — nothing saved.")