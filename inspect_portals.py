import re, urllib.request

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

def fetch(url):
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=12) as resp:
        return resp.read().decode('utf-8', errors='ignore')

# 1. Turing
try:
    html = fetch('https://www.turing.com/jobs')
    print("Turing HTML length:", len(html))
    matches = re.findall(r'href=["\'](/jobs/[^"\']+)["\']', html)
    print(f"Turing job paths: {len(set(matches))}")
    for p in list(set(matches))[:8]:
        print("  - https://www.turing.com" + p)
except Exception as e:
    print("Turing error:", e)

# 2. Micro1
try:
    html = fetch('https://www.micro1.ai/jobs')
    print("\nMicro1 HTML length:", len(html))
    matches = re.findall(r'href=["\']([^"\']*(?:jobs|apply|careers)[^"\']*)["\']', html, re.I)
    print(f"Micro1 links: {len(set(matches))}")
    for p in list(set(matches))[:8]:
        print("  -", p)
except Exception as e:
    print("Micro1 error:", e)
