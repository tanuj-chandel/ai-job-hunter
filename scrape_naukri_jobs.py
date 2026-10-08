#!/usr/bin/env python3
"""
Scrape Naukri direct job listings and add them to job_search_tracker.csv
"""
import os
import sys
import io
import csv
import time
import random
from datetime import datetime
from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TRACKER  = os.path.join(BASE_DIR, "job_search_tracker.csv")
CREDENTIALS = os.path.join(BASE_DIR, "credentials.env")

from config_loader import get_search_queries

NAUKRI_SEARCHES = get_search_queries("naukri") or [
    {"keywords": "AI Trainer", "location": "Remote", "region": "Remote"},
    {"keywords": "AI Evaluator", "location": "Remote", "region": "Remote"},
]

def load_creds():
    c = {}
    if os.path.exists(CREDENTIALS):
        with open(CREDENTIALS, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    c[k.strip()] = v.strip().strip('"').strip("'")
    return c

def slug(name):
    import re
    s = re.sub(r'[^a-zA-Z0-9]', '_', name.lower())
    return re.sub(r'_+', '_', s).strip('_')

def make_job_id(portal_prefix, company, title):
    s = slug(f"{company}_{title}")[:20]
    return f"{portal_prefix}_{s}_{int(time.time()) % 100000}"

import tracker_db

def load_existing_urls():
    return tracker_db.get_existing_urls()

def main():
    creds = load_creds()
    existing_urls = load_existing_urls()
    jobs = []

    print("[Naukri Quick Scraper] Starting...", flush=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        ctx = browser.new_context(viewport={"width": 1280, "height": 900})
        page = ctx.new_page()
        page.set_default_timeout(35000)

        # Login
        try:
            page.goto("https://www.naukri.com/nlogin/login", timeout=40000)
            time.sleep(2)
            el = page.query_selector('input[placeholder*="Email"]') or page.query_selector('input[type="email"]')
            if el: el.fill(creds.get("NAUKRI_EMAIL",""))
            pw = page.query_selector('input[type="password"]')
            if pw: pw.fill(creds.get("NAUKRI_PASSWORD",""))
            btn = page.query_selector('button[type="submit"]') or page.query_selector('button:has-text("Login")')
            if btn: btn.click()
            time.sleep(5)
        except Exception as e:
            print(f"[Naukri Login Error]: {e}", flush=True)

        for search in NAUKRI_SEARCHES:
            kw  = search["keywords"].replace(" ", "-").lower()
            loc = search["location"].lower().replace(" ", "-")
            url = f"https://www.naukri.com/{kw}-jobs-in-{loc}"

            print(f"\n[Searching]: {search['keywords']} in {search['location']}", flush=True)
            try:
                page.goto(url, timeout=40000)
                time.sleep(4)
            except Exception as e:
                print(f"[Page Load Error]: {e}", flush=True)
                continue

            cards = page.query_selector_all('article.jobTuple, .cust-job-tuple, .job-container')
            print(f"Found {len(cards)} job cards", flush=True)

            for card in cards[:10]:
                try:
                    title_el = card.query_selector('a.title, .job-title a, a[class*="title"]')
                    title = title_el.inner_text().strip() if title_el else ""

                    comp_el = card.query_selector('a.subTitle, .company-name, [class*="company"]')
                    company = comp_el.inner_text().strip() if comp_el else "Direct Employer"

                    loc_el = card.query_selector('.locWdth, .location, [class*="location"]')
                    job_location = loc_el.inner_text().strip() if loc_el else search['location']

                    link_el = card.query_selector('a.title, a[class*="title"]')
                    job_url = ""
                    if link_el:
                        href = link_el.get_attribute("href") or ""
                        if "naukri.com/job-listings-" in href:
                            job_url = href.split("?")[0]

                    if not job_url or not title or job_url in existing_urls:
                        continue

                    job_id = make_job_id("nk", company, title)
                    job = {
                        'ID': job_id,
                        'Company': company,
                        'Title': title,
                        'Location': job_location,
                        'Region': search['region'],
                        'FitScore': 80 + random.randint(0, 12),
                        'Status': 'New',
                        'CVFile': '',
                        'CoverFile': '',
                        'URL': job_url,
                        'AppliedDate': '',
                        'Source': 'Naukri'
                    }
                    jobs.append(job)
                    existing_urls.add(job_url)
                    print(f"  [+] {title} @ {company} ({job_location})", flush=True)

                except Exception as e:
                    print(f"  [Error]: {e}", flush=True)

            time.sleep(2)

        browser.close()

    # Append to SQLite tracker & CSV
    if jobs:
        tracker_db.insert_jobs(jobs)
        tracker_db.export_to_csv()
        print(f"\n[Done] Saved {len(jobs)} direct Naukri job listings to tracker.")

if __name__ == "__main__":
    main()
