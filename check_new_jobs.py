import csv

with open('job_search_tracker.csv', encoding='utf-8') as f:
    rows = list(csv.DictReader(f))

new_naukri = [r for r in rows if r.get('Source') == 'Naukri' or r.get('Status') == 'New']
print(f"Total New Applyable jobs: {len(new_naukri)}")
for i, r in enumerate(new_naukri[:10], 1):
    print(f"{i}. [{r['ID']}] {r['Title']} @ {r['Company']} ({r['Location']})")
    print(f"   URL: {r['URL']}")
