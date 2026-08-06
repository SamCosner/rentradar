"""Backfill Supabase with scrape days that exist in the local master CSV but not in the DB.

The scraper writes to data/bloomington_rents_master.csv first, then inserts to Supabase.
While the Supabase project was paused those inserts failed, so the local CSV is complete
and the DB has a hole. This copies the missing days back in.

Insert-only and idempotent: a date is skipped if the DB already has any row for it.

    python backfill_supabase.py            # dry run — report what would be inserted
    python backfill_supabase.py --apply    # actually insert
"""
import csv, os, sys, collections
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

MASTER_FILE = "data/bloomington_rents_master.csv"
APPLY = "--apply" in sys.argv

supabase = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])


def db_dates():
    """Every scraped_date already present in the listings table."""
    dates, offset = set(), 0
    while True:
        result = supabase.table("listings").select("scraped_date").range(offset, offset + 999).execute()
        if not result.data:
            break
        dates.update(r["scraped_date"] for r in result.data)
        if len(result.data) < 1000:
            break
        offset += 1000
    return dates


def to_db_row(row):
    """Same field mapping the scraper uses in append_to_master()."""
    return {
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
    }


existing = db_dates()

by_date = collections.defaultdict(list)
with open(MASTER_FILE, newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        d = row.get("scraped_date")
        if d and d not in existing:
            by_date[d].append(row)

if not by_date:
    print("Nothing to backfill — Supabase already has every date in the master CSV.")
    sys.exit()

print(f"Missing dates: {len(by_date)}   rows to insert: {sum(len(v) for v in by_date.values())}")
for d in sorted(by_date):
    events = collections.Counter(r.get("event") for r in by_date[d])
    print(f"  {d}  {len(by_date[d]):>5} rows   {dict(events)}")

if not APPLY:
    print("\nDry run. Re-run with --apply to insert.")
    sys.exit()

inserted = 0
for d in sorted(by_date):
    rows = [to_db_row(r) for r in by_date[d]]
    for i in range(0, len(rows), 500):
        batch = rows[i:i + 500]
        supabase.table("listings").insert(batch).execute()
        inserted += len(batch)
    print(f"  inserted {d} ({len(rows)} rows)")

print(f"\nDone. Inserted {inserted} rows.")
