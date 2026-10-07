import json, time, re, urllib.request

def get_remotive_ai_jobs():
    jobs = []
    try:
        url = 'https://remotive.com/api/remote-jobs?search=ai&limit=30'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            for item in data.get('jobs', []):
                title = item.get('title', '')
                company = item.get('company_name', 'Tech Client')
                job_url = item.get('url', '')
                loc = item.get('candidate_required_location', 'Worldwide')
                
                # Check for AI / Evaluation / Annotation / Tech relevance
                t_lower = title.lower()
                if any(k in t_lower for k in ['ai', 'evaluator', 'trainer', 'prompt', 'annotation', 'review', 'analyst', 'data', 'quality', 'model', 'ml']):
                    jobs.append({
                        'title': title,
                        'company': company,
                        'url': job_url,
                        'location': loc,
                        'source': 'Remotive Remote'
                    })
    except Exception as e:
        print("Remotive error:", e)
    return jobs

print("Remotive matching AI jobs:", len(get_remotive_ai_jobs()))
for j in get_remotive_ai_jobs()[:5]:
    print(" ", j)
