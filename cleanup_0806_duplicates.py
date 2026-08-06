"""Remove redundant new/removed events from the 2026-08-06 scrape.

That scrape diffed against the last state visible in Supabase (2026-07-10), because the
2026-07-13..2026-08-05 rows had not been backfilled yet. So it re-announced listings that
had already gone new or removed during the outage.

A 2026-08-06 row is redundant when it restates the listing's state as of 2026-08-05:
  - event "new"     and the listing was already active on 08-05
  - event "removed" and the listing was already removed on 08-05
A genuine relisting (removed on 08-05, new on 08-06) is kept, as is a genuine removal.

    python cleanup_0806_duplicates.py            # dry run
    python cleanup_0806_duplicates.py --apply    # actually delete
"""
import os, sys
import pandas as pd
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

TARGET = "2026-08-06"
APPLY = "--apply" in sys.argv

supabase = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])


def fetch(select, **filters):
    rows, offset = [], 0
    while True:
        q = supabase.table("listings").select(select)
        for op, args in filters.items():
            q = getattr(q, op)(*args)
        result = q.range(offset, offset + 999).execute()
        if not result.data:
            break
        rows.extend(result.data)
        if len(result.data) < 1000:
            break
        offset += 1000
    return rows


# State of every listing as of the day before the target scrape
prior = pd.DataFrame(fetch("url,event,scraped_date", lt=("scraped_date", TARGET)))
prior = prior.sort_values("scraped_date", kind="mergesort")
state = prior.groupby("url")["event"].last()

target = pd.DataFrame(fetch("id,url,event", eq=("scraped_date", TARGET)))
target["prior_state"] = target["url"].map(state)

redundant = target[
    ((target["event"] == "new")     & target["prior_state"].notna() & (target["prior_state"] != "removed"))
    | ((target["event"] == "removed") & (target["prior_state"] == "removed"))
]

print(f"{TARGET} rows: {len(target)}")
for ev in ("new", "removed"):
    tot = int((target["event"] == ev).sum())
    red = int((redundant["event"] == ev).sum())
    print(f"  {ev:<8} {tot:>4} total -> {red:>4} redundant, {tot - red:>4} genuine")
print(f"  changed  {int((target['event'] == 'changed').sum()):>4} total ->    0 redundant (left untouched)")
print(f"\nRows to delete: {len(redundant)}")

if not APPLY:
    print("Dry run. Re-run with --apply to delete.")
    sys.exit()

ids = redundant["id"].tolist()
for i in range(0, len(ids), 200):
    batch = ids[i:i + 200]
    supabase.table("listings").delete().in_("id", batch).execute()
    print(f"  deleted {i + len(batch)}/{len(ids)}")

print(f"\nDone. Deleted {len(ids)} rows.")
