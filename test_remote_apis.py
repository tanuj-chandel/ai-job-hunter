import urllib.request
import json

def fetch_json(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
    with urllib.request.urlopen(req, timeout=12) as resp:
        return json.loads(resp.read().decode('utf-8'))

print("Testing Remote APIs for AI Trainer / Evaluator / Prompt jobs...")

# 1. Remotive API
try:
    data = fetch_json('https://remotive.com/api/remote-jobs?search=ai&limit=25')
    jobs = data.get('jobs', [])
    print(f"Remotive API: Found {len(jobs)} jobs")
    for j in jobs[:5]:
        print(f"  - {j.get('title')} @ {j.get('company_name')} ({j.get('candidate_required_location')}) -> {j.get('url')[:60]}")
except Exception as e:
    print(f"Remotive error: {e}")

# 2. Jobicy API
try:
    data = fetch_json('https://jobicy.com/api/v2/remote-jobs?count=25&tag=ai')
    jobs = data.get('jobs', [])
    print(f"\nJobicy API: Found {len(jobs)} jobs")
    for j in jobs[:5]:
        print(f"  - {j.get('jobTitle')} @ {j.get('companyName')} ({j.get('jobGeo')}) -> {j.get('url')[:60]}")
except Exception as e:
    print(f"Jobicy error: {e}")

# 3. Test Turing & Micro1 jobs URLs
for portal, url in [
    ("Turing Jobs", "https://turing.com/jobs"),
    ("Micro1 Jobs", "https://www.micro1.ai/jobs"),
    ("Outlier.ai Careers", "https://outlier.ai/"),
]:
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            print(f"\n{portal}: HTTP {resp.status} reachable!")
    except Exception as e:
        print(f"\n{portal} status check: {e}")
