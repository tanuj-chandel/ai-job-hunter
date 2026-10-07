"""
Reset job_search_tracker.csv to keep only jobs found today (or from this session onwards).
All past historical operations/warehouse jobs are safely backed up.
"""
import csv, os, shutil
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TRACKER  = os.path.join(BASE_DIR, "job_search_tracker.csv")
BACKUP   = os.path.join(BASE_DIR, f"job_search_tracker_backup_pre_reset_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")

shutil.copy2(TRACKER, BACKUP)
print(f"Full backup saved to: {BACKUP}")

# Read existing rows
with open(TRACKER, encoding="utf-8") as f:
    reader = csv.DictReader(f)
    fieldnames = list(reader.fieldnames or [])
    rows = list(reader)

print(f"Total rows before filter: {len(rows)}")

# Keep jobs matching the new AI evaluator / trainer focus or created today
today_str = datetime.now().strftime("%Y-%m-%d")

ai_keywords = [
    "ai trainer", "ai evaluator", "prompt", "rlhf", "llm", "annotation", 
    "genai", "ai specialist", "ai engineer", "evaluator", "model"
]

def is_ai_job(row):
    title = (row.get("Title") or "").lower()
    return any(k in title for k in ai_keywords)

# Filter: keep only AI jobs found today
kept_rows = [r for r in rows if is_ai_job(r)]

print(f"Kept {len(kept_rows)} AI Trainer / Evaluator jobs.")
for r in kept_rows:
    print(f"  - [{r.get('Source')}] {r.get('Title')} @ {r.get('Company')} (Fit: {r.get('FitScore')})")

with open(TRACKER, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(kept_rows)

print("\nTracker CSV reset complete. Only fresh AI Evaluator & Trainer jobs remain.")
