"""
Fix 1: Reset phantom 'Real Applied' entries in job_search_tracker.csv back to 'Tailored & Ready'.
Run this once to clean up the fake applied data.
"""
import csv, os, shutil
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TRACKER  = os.path.join(BASE_DIR, "job_search_tracker.csv")
BACKUP   = os.path.join(BASE_DIR, f"job_search_tracker_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")

# Backup first
shutil.copy2(TRACKER, BACKUP)
print(f"Backup saved to: {BACKUP}")

rows, fieldnames = [], []
reset_count = 0

with open(TRACKER, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    fieldnames = list(reader.fieldnames or [])
    for row in reader:
        if row.get("Status", "") == "Real Applied":
            row["Status"] = "Tailored & Ready"
            reset_count += 1
        rows.append(row)

with open(TRACKER, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"Done! Reset {reset_count} phantom 'Real Applied' rows to 'Tailored & Ready'.")
print(f"Total rows processed: {len(rows)}")
