#!/bin/bash
# startup.sh — runs on Render before gunicorn starts.
# Downloads processed data files from Google Drive using
# file IDs set as environment variables in the Render dashboard.

set -e  # exit immediately if any command fails

mkdir -p data

echo "Checking for data files..."

if [ ! -f data/listings_clean.csv ]; then
    echo "Downloading data from Google Drive..."

    gdown --fuzzy "$GDRIVE_LISTINGS"          -O data/listings_clean.csv
    gdown --fuzzy "$GDRIVE_CALENDAR"          -O data/calendar_monthly.csv
    gdown --fuzzy "$GDRIVE_REVIEWS_MONTHLY"   -O data/reviews_monthly.csv
    gdown --fuzzy "$GDRIVE_REVIEWS_PER_LST"   -O data/reviews_per_listing.csv

    echo "Download complete."
else
    echo "Data files already present — skipping download."
fi

exec gunicorn dashboard:server --bind 0.0.0.0:$PORT
