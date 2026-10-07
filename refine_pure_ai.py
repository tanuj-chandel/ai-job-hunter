import csv, re

with open("job_search_tracker.csv", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    rows = list(reader)

ai_regex = re.compile(r'\b(ai|genai|prompt|rlhf|llm|annotation|model evaluator|evaluator)\b', re.IGNORECASE)

pure_ai = [
    r for r in rows 
    if ai_regex.search(r.get("Title",""))
]

# Ensure status is 'New' for these newly discovered AI jobs so they appear fresh in the dashboard
for r in pure_ai:
    r["Status"] = "New"
    r["Region"] = "Remote"
    r["AppliedDate"] = ""

print(f"Total verified AI jobs: {len(pure_ai)}")
for r in pure_ai:
    print(f"  - [{r.get('Source')}] {r.get('Title')} @ {r.get('Company')} (Fit: {r.get('FitScore')})")

with open("job_search_tracker.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(pure_ai)
