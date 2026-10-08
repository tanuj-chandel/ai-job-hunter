"""
Migration script: One-time migration from job_search_tracker.csv to tracker.db (SQLite).
"""
import os
import csv
import sys
from tracker_db import init_db, insert_jobs, get_all_jobs, export_to_csv, DB_FILE, CSV_FILE

def run_migration():
    if not os.path.exists(CSV_FILE):
        print(f"Error: {CSV_FILE} not found.")
        sys.exit(1)

    print(f"[*] Reading jobs from {CSV_FILE}...")
    jobs = []
    with open(CSV_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("ID"):
                jobs.append(dict(row))

    print(f"[*] Read {len(jobs)} rows from CSV.")
    init_db()

    print(f"[*] Inserting rows into SQLite database ({DB_FILE})...")
    insert_jobs(jobs)

    db_jobs = get_all_jobs()
    print(f"[*] Total rows in tracker.db: {len(db_jobs)}")

    if len(db_jobs) != len(jobs):
        print(f"[!] Warning: Row count mismatch (CSV: {len(jobs)}, DB: {len(db_jobs)})")
    else:
        print(f"[+] Success! Exactly {len(db_jobs)} rows migrated successfully.")

    # Export back to verify round-trip
    exported = export_to_csv()
    print(f"[+] Verified CSV export: {exported} rows exported to {CSV_FILE}.")

if __name__ == "__main__":
    run_migration()
