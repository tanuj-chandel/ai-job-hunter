import urllib.request, json

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

print("Testing RemoteOK & Himalayas Extraction...")

# 1. RemoteOK
try:
    req = urllib.request.Request("https://remoteok.com/api?tag=ai", headers=headers)
    with urllib.request.urlopen(req, timeout=12) as r:
        items = json.loads(r.read().decode('utf-8'))
        valid = [i for i in items if isinstance(i, dict) and i.get('position')]
        print(f"RemoteOK: {len(valid)} valid job items")
        for j in valid[:3]:
            print(f"  - {j.get('position')} @ {j.get('company')} -> {j.get('url')}")
except Exception as e:
    print("RemoteOK error:", e)

# 2. Himalayas
try:
    req = urllib.request.Request("https://himalayas.app/jobs/api?limit=30", headers=headers)
    with urllib.request.urlopen(req, timeout=12) as r:
        data = json.loads(r.read().decode('utf-8'))
        h_jobs = data.get('jobs', [])
        print(f"\nHimalayas: {len(h_jobs)} job items")
        for j in h_jobs[:3]:
            app_url = j.get('applicationLink') or f"https://himalayas.app/jobs/{j.get('slug')}"
            print(f"  - {j.get('title')} @ {j.get('companyName')} -> {app_url}")
except Exception as e:
    print("Himalayas error:", e)
