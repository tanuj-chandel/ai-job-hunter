import csv

rows = list(csv.DictReader(open('job_search_tracker.csv', encoding='utf-8')))
applied = [r for r in rows if r.get('Status','') == 'Real Applied']
statuses = {}
for r in rows:
    s = r.get('Status','')
    statuses[s] = statuses.get(s, 0) + 1

print(f'Total jobs: {len(rows)}')
print('Status breakdown:')
for k,v in sorted(statuses.items(), key=lambda x: -x[1]):
    print(f'  {repr(k)}: {v}')

print(f'\nReal Applied jobs ({len(applied)}):')
for r in applied[:10]:
    print(f'  - {r.get("Company","")} | {r.get("Title","")} | Date: {r.get("AppliedDate","")}')
