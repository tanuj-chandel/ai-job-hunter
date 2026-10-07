import csv

with open('job_search_tracker.csv', encoding='utf-8') as f:
    applied = [r for r in csv.DictReader(f) if r.get('Status') == 'Real Applied']

print(f"Total Confirmed Applied: {len(applied)}\n")
for i, r in enumerate(applied, 1):
    print(f"{i:2d}. {r.get('Title')} @ {r.get('Company')} | Source: {r.get('Source')} | Date: {r.get('AppliedDate')}")
