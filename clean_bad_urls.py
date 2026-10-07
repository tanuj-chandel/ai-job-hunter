"""
Clean job_search_tracker.csv — remove rows where the URL is a search/listing page
instead of a direct job page. These cannot be applied to by the browser agent.
"""
import csv, os, shutil, re
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TRACKER  = os.path.join(BASE_DIR, "job_search_tracker.csv")
BACKUP   = os.path.join(BASE_DIR, f"job_search_tracker_backup_clean_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")

shutil.copy2(TRACKER, BACKUP)
print(f"Backup: {BACKUP}")

def is_search_page_url(url):
    u = url.lower()
    # Naukri search pages (not direct job listing)
    if "naukri.com" in u and "-jobs-in-" in u and "/job-listings-" not in u:
        return True
    # Indeed search pages
    if "indeed.com" in u and ("jobs?q=" in u or "/jobs?q=" in u or "jobs?q=" in u):
        return True
    # Glassdoor search pages
    if "glassdoor.com" in u and "SRCH_KO" in url and "/job-listing/" not in u:
        return True
    # Bayt search pages (category pages, not individual jobs)
    if "bayt.com" in u and "-jobs-in-" in u and len(u.split("/")) < 8:
        return True
    return False

rows, fieldnames = [], []
removed, kept = 0, 0

with open(TRACKER, encoding="utf-8") as f:
    reader = csv.DictReader(f)
    fieldnames = list(reader.fieldnames or [])
    for row in reader:
        url = row.get("URL", "").strip()
        if is_search_page_url(url):
            print(f"  [REMOVE - search URL] {row.get('Company','')} | {url[:70]}")
            removed += 1
        else:
            rows.append(row)
            kept += 1

with open(TRACKER, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"\nDone! Removed {removed} bad search-page URLs. Kept {kept} direct job URLs.")
