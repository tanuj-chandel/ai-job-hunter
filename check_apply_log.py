import json, os
from collections import Counter

log_path = os.path.join(os.path.dirname(__file__), 'apply_screenshots', 'apply_log.json')
with open(log_path, encoding='utf-8') as f:
    log = json.load(f)

print(f'Total jobs processed: {len(log)}')
statuses = Counter(r.get('Status', '') for r in log)
print('\nStatus breakdown:')
for s, c in statuses.most_common():
    print(f'  {repr(s)}: {c}')

by_portal = Counter(r.get('Portal', '') for r in log)
print('\nBy portal:')
for p, c in by_portal.most_common():
    print(f'  {p}: {c}')

applied = [r for r in log if r.get('Status') == 'applied']
attempted = [r for r in log if r.get('Status') == 'attempted']
skipped = [r for r in log if 'skipped' in str(r.get('Status', ''))]
errors = [r for r in log if 'error' in str(r.get('Status', ''))]

print(f'\n✅ Confirmed Applied : {len(applied)}')
for r in applied:
    print(f'   - {r.get("Company","")} | {r.get("Title","")} | {r.get("Portal","")}')

print(f'\n⚡ Attempted         : {len(attempted)}')
for r in attempted:
    print(f'   - {r.get("Company","")} | {r.get("Title","")} | {r.get("Portal","")}')

print(f'\n⏭  Skipped           : {len(skipped)}')
skip_reasons = Counter(r.get('Status','') for r in skipped)
for reason, count in skip_reasons.most_common():
    print(f'   {reason}: {count}')

print(f'\n❌ Errors            : {len(errors)}')
