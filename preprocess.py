"""
preprocess.py — Run this ONCE locally before deploying.
Reads the large raw files and writes small aggregated CSVs into data/
that are safe to commit to GitHub (each < 50 KB).
"""

import pandas as pd
import numpy as np
import os

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR  = os.path.join(DATA_DIR, "data")
os.makedirs(OUT_DIR, exist_ok=True)

print("Loading raw data…")

# ── 1. Listings (725 KB — keep cleaned version) ──────────────────────────────
listings = pd.read_csv(os.path.join(DATA_DIR, "listings.csv"))
listings = listings[listings["price"].notna() & (listings["price"] <= 2000)]
listings["price"] = listings["price"].astype(float)
listings.to_csv(os.path.join(OUT_DIR, "listings_clean.csv"), index=False)
print(f"  listings_clean.csv  → {len(listings):,} rows")

# ── 2. Calendar → monthly availability aggregate (12 rows) ───────────────────
calendar = pd.read_csv(os.path.join(DATA_DIR, "calendar.csv.gz"), compression="gzip")
calendar["date"]         = pd.to_datetime(calendar["date"])
calendar["month"]        = calendar["date"].dt.month
calendar["month_name"]   = calendar["date"].dt.strftime("%b")
calendar["is_available"] = (calendar["available"] == "t").astype(int)

cal_monthly = (
    calendar.groupby(["month", "month_name"])["is_available"]
    .mean()
    .reset_index()
    .rename(columns={"is_available": "pct_available"})
    .sort_values("month")
)
cal_monthly["pct_available"] = (cal_monthly["pct_available"] * 100).round(2)
cal_monthly.to_csv(os.path.join(OUT_DIR, "calendar_monthly.csv"), index=False)
print(f"  calendar_monthly.csv → {len(cal_monthly)} rows")

# Also save per-listing availability for scatter (join with listings later)
# Not needed separately — listings_clean already has availability_365

# ── 3. Reviews → monthly counts (one row per month) ─────────────────────────
reviews = pd.read_csv(os.path.join(DATA_DIR, "reviews.csv.gz"), compression="gzip",
                      usecols=["listing_id", "date"])
reviews["date"]       = pd.to_datetime(reviews["date"])
reviews["year_month"] = reviews["date"].dt.to_period("M").dt.to_timestamp()

reviews_monthly = (
    reviews.groupby("year_month")
    .size()
    .reset_index(name="reviews")
    .sort_values("year_month")
)
# Keep only 2020-present for clarity
reviews_monthly = reviews_monthly[reviews_monthly["year_month"] >= "2020-01-01"]
reviews_monthly["year_month"] = reviews_monthly["year_month"].astype(str)
reviews_monthly.to_csv(os.path.join(OUT_DIR, "reviews_monthly.csv"), index=False)
print(f"  reviews_monthly.csv  → {len(reviews_monthly)} rows")

# ── 4. Reviews per listing (for filtered trend chart) ────────────────────────
reviews_per_listing = (
    reviews.groupby(["listing_id", "year_month"])
    .size()
    .reset_index(name="reviews")
)
reviews_per_listing["year_month"] = reviews_per_listing["year_month"].astype(str)
reviews_per_listing.to_csv(os.path.join(OUT_DIR, "reviews_per_listing.csv"), index=False)
print(f"  reviews_per_listing.csv → {len(reviews_per_listing):,} rows")

print("\nDone! Files written to ./data/")
for f in os.listdir(OUT_DIR):
    size_kb = os.path.getsize(os.path.join(OUT_DIR, f)) / 1024
    print(f"  {f:40s} {size_kb:6.1f} KB")
