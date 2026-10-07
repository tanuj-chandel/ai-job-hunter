import csv
from collections import Counter

with open('job_search_tracker.csv', encoding='utf-8') as f:
    rows = list(csv.DictReader(f))

new_jobs = [r for r in rows if r.get('Status') == 'New']
print(f'Total New jobs: {len(new_jobs)}')
print('By source:')
for p, c in Counter(r.get('Source','') for r in new_jobs).items():
    print(f'  {p}: {c}')

print('\nFirst 10 New jobs:')
for r in new_jobs[:10]:
    print(f"  [{r.get('ID')}] {r.get('Company')} - {r.get('Title')} ({r.get('URL')[:65]})")
