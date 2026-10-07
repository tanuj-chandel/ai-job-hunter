#!/usr/bin/env python3
"""
Migration script: Add outcome & response tracking columns to job_search_tracker.csv

New columns added:
- ResponseReceived: 'Yes', 'No', 'Pending', or '' (unapplied)
- ResponseDate: YYYY-MM-DD or ''
- InterviewScheduled: 'Yes', 'No', or ''
- Outcome: 'Rejected', 'Interview', 'Offer', 'NoResponse', or ''

Preserves all existing data and creates an automatic timestamped backup.
"""

import os
import sys
import csv
import shutil
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TRACKER_FILE = os.path.join(BASE_DIR, "job_search_tracker.csv")

NEW_COLUMNS = [
    "ResponseReceived",
    "ResponseDate",
    "InterviewScheduled",
    "Outcome"
]

def migrate_tracker():
    if not os.path.exists(TRACKER_FILE):
        print(f"[Error] Tracker file not found: {TRACKER_FILE}", file=sys.stderr)
        return False

    # 1. Create a safe backup
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(BASE_DIR, f"job_search_tracker_backup_pre_outcomes_{timestamp}.csv")
    shutil.copy2(TRACKER_FILE, backup_file)
    print(f"[Backup] Created backup: {os.path.basename(backup_file)}")

    # 2. Read existing data
    rows = []
    with open(TRACKER_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        old_fieldnames = list(reader.fieldnames or [])
        for row in reader:
            rows.append(row)

    print(f"[Migration] Read {len(rows)} existing rows with {len(old_fieldnames)} columns.")

    # 3. Formulate new fieldnames list (preserving existing order, appending new columns)
    updated_fieldnames = list(old_fieldnames)
    for col in NEW_COLUMNS:
        if col not in updated_fieldnames:
            updated_fieldnames.append(col)

    # 4. Migrate rows
    applied_count = 0
    unapplied_count = 0

    for row in rows:
        status = row.get("Status", "").strip()
        is_applied = status in ["Real Applied", "Attempted", "Applied"]

        # ResponseReceived
        if not row.get("ResponseReceived"):
            row["ResponseReceived"] = "Pending" if is_applied else ""

        # ResponseDate
        if not row.get("ResponseDate"):
            row["ResponseDate"] = ""

        # InterviewScheduled
        if not row.get("InterviewScheduled"):
            row["InterviewScheduled"] = "No" if is_applied else ""

        # Outcome
        if not row.get("Outcome"):
            row["Outcome"] = "NoResponse" if is_applied else ""

        if is_applied:
            applied_count += 1
        else:
            unapplied_count += 1

    # 5. Write back updated CSV
    with open(TRACKER_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=updated_fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"[Migration] Successfully migrated {len(rows)} records.")
    print(f"  - Applied records set to 'Pending' / 'NoResponse': {applied_count}")
    print(f"  - Unapplied records initialized: {unapplied_count}")
    print(f"  - New columns: {', '.join(NEW_COLUMNS)}")
    print(f"  - Final column count: {len(updated_fieldnames)}")
    return True

if __name__ == "__main__":
    success = migrate_tracker()
    sys.exit(0 if success else 1)
