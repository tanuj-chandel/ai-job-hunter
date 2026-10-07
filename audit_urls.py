import csv

with open('job_search_tracker.csv', encoding='utf-8') as f:
    rows = list(csv.DictReader(f))

portals = {'linkedin': [], 'naukri': [], 'bayt': [], 'indeed': [], 'glassdoor': [], 'other': []}
for r in rows:
    url = r.get('URL','').lower()
    matched = False
    for k in portals:
        if k in url:
            portals[k].append(r)
            matched = True
            break
    if not matched:
        portals['other'].append(r)

for portal, rows_p in portals.items():
    print(f"\n{portal.upper()}: {len(rows_p)} jobs")
    for r in rows_p[:3]:
        jid = r.get('ID','?')
        url = r.get('URL','')
        print(f"  [{jid}] {url[:100]}")
