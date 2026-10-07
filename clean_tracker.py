import csv

fixed_rows = []
fieldnames = ['ID','Company','Title','Location','Region','FitScore','Status','CVFile','CoverFile','URL','AppliedDate','Source']

with open('job_search_tracker.csv', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for r in reader:
        # Clean extra keys if any
        clean_r = {k: v for k, v in r.items() if k in fieldnames and k is not None}
        for k in fieldnames:
            if k not in clean_r or clean_r[k] is None:
                clean_r[k] = ''

        if not clean_r['Company']:
            url = clean_r.get('URL', '')
            if 'naukri.com/job-listings-' in url:
                slug_part = url.split('naukri.com/job-listings-')[1].split('?')[0]
                tokens = slug_part.split('-')
                # pick middle token
                if len(tokens) >= 4:
                    clean_r['Company'] = tokens[2].title()
                else:
                    clean_r['Company'] = 'Direct Employer'
            else:
                clean_r['Company'] = 'Direct Employer'

        fixed_rows.append(clean_r)

with open('job_search_tracker.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(fixed_rows)

print(f"Successfully cleaned and standardized tracker. Total jobs: {len(fixed_rows)}")
