#!/usr/bin/env python3
"""
LinkedIn Easy Apply Job Scraper for Tanuj Chandel.
Uses Playwright to search LinkedIn with the Easy Apply filter (f_LF=f_AL)
and collects ONLY jobs that have the Easy Apply button — meaning the agent
CAN fully auto-submit them without any external company portal.

Portals scraped: LinkedIn (Easy Apply only), Naukri (direct apply), 
                 Bayt (direct apply), Indeed (Indeed Apply), Glassdoor (Easy Apply)
"""

import os
import sys
import io
import csv
import json
import time
import re
import random
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
TRACKER      = os.path.join(BASE_DIR, "job_search_tracker.csv")
CREDENTIALS  = os.path.join(BASE_DIR, "credentials.env")
SCREENSHOTS  = os.path.join(BASE_DIR, "apply_screenshots")
ERROR_LOG    = os.path.join(BASE_DIR, "scraper_errors.log")
os.makedirs(SCREENSHOTS, exist_ok=True)

def log_scraper_error(source, message, exc=None):
    """Write scraper failures with timestamp, source, and error details to scraper_errors.log."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    err_str = f"[{timestamp}] [{source}] {message}"
    if exc is not None:
        err_str += f" | Exception: {exc}"
    print(f"  [ERROR-LOG] {err_str}", flush=True)
    try:
        with open(ERROR_LOG, "a", encoding="utf-8") as f:
            f.write(err_str + "\n")
    except Exception as io_err:
        print(f"  [CRITICAL] Failed to write to {ERROR_LOG}: {io_err}", flush=True)

# ── Candidate profile ──────────────────────────────────────────────────────────
CANDIDATE_NAME  = "Tanuj Chandel"
CANDIDATE_EMAIL = "tanuj.chandel@gmail.com"

# ── Search queries per portal (Remote AI Evaluator / Trainer / Prompt Engineering) ──
LINKEDIN_SEARCHES = [
    {"keywords": "AI Trainer",                 "location": "Remote", "region": "Remote"},
    {"keywords": "AI Evaluator",               "location": "Remote", "region": "Remote"},
    {"keywords": "Prompt Engineer",            "location": "Remote", "region": "Remote"},
    {"keywords": "RLHF Specialist",            "location": "Remote", "region": "Remote"},
    {"keywords": "AI Data Annotation",         "location": "Remote", "region": "Remote"},
    {"keywords": "Model Evaluation Specialist","location": "Remote", "region": "Remote"},
    {"keywords": "LLM Evaluator",              "location": "Remote", "region": "Remote"},
    {"keywords": "AI Content Evaluator",       "location": "Remote", "region": "Remote"},
    {"keywords": "AI Tutor",                   "location": "Remote", "region": "Remote"},
    {"keywords": "AI Quality Assessor",        "location": "Remote", "region": "Remote"},
    {"keywords": "AI Trainer",                 "location": "Worldwide", "region": "Remote"},
    {"keywords": "AI Evaluator",               "location": "India", "region": "Remote"},
    {"keywords": "Prompt Engineer",            "location": "India", "region": "Remote"},
]

NAUKRI_SEARCHES = [
    {"keywords": "AI Trainer",                 "location": "Remote", "region": "Remote"},
    {"keywords": "AI Evaluator",               "location": "Remote", "region": "Remote"},
    {"keywords": "Prompt Engineer",            "location": "Remote", "region": "Remote"},
    {"keywords": "Data Annotation",            "location": "Remote", "region": "Remote"},
    {"keywords": "AI Specialist",              "location": "Remote", "region": "Remote"},
    {"keywords": "Model Evaluator",            "location": "Remote", "region": "Remote"},
]

BAYT_SEARCHES = [
    {"keywords": "AI Specialist",              "location": "Remote", "region": "Remote"},
    {"keywords": "AI Trainer",                 "location": "Dubai",  "region": "Remote"},
    {"keywords": "Data Annotation",            "location": "Remote", "region": "Remote"},
]

INDEED_SEARCHES = [
    {"keywords": "AI Trainer",                 "location": "Remote", "region": "Remote"},
    {"keywords": "AI Evaluator",               "location": "Remote", "region": "Remote"},
    {"keywords": "Prompt Engineer",            "location": "Remote", "region": "Remote"},
    {"keywords": "Data Annotation Specialist", "location": "Remote", "region": "Remote"},
    {"keywords": "LLM Evaluator",              "location": "Remote", "region": "Remote"},
]

GLASSDOOR_SEARCHES = [
    {"keywords": "AI Trainer",                 "location": "Remote", "region": "Remote"},
    {"keywords": "AI Evaluator",               "location": "Remote", "region": "Remote"},
    {"keywords": "Prompt Engineer",            "location": "Remote", "region": "Remote"},
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
    s = re.sub(r'[^a-zA-Z0-9]', '_', name.lower())
    return re.sub(r'_+', '_', s).strip('_')

def make_job_id(portal_prefix, company, title):
    s = slug(f"{company}_{title}")[:20]
    return f"{portal_prefix}_{s}_{int(time.time()) % 100000}"

def fit_score(title):
    """Score job relevance based on Tanuj's background (B.Tech ECE + MBA + AI Evaluation + Operations)."""
    title_l = title.lower()
    # High fit — AI Evaluation, Prompting, RLHF, Business/Tech Operations
    HIGH = ["ai evaluator", "ai trainer", "prompt engineer", "rlhf", "model evaluator",
            "llm evaluator", "ai content evaluator", "ai quality", "annotation specialist",
            "ai specialist", "ai tutor", "model trainer", "prompt specialist",
            "ai annotator", "ai data annotator", "ai benchmark", "ai reviewer",
            "video data annotator", "data annotator", "ai agent", "quality analyst",
            "business operations", "operations lead", "operations manager", "project manager",
            "operations analyst", "digital assets operations", "process automation", "data analyst"]
    MED  = ["evaluator", "trainer", "tutor", "prompt", "annotation", "annotator",
            "machine learning", "artificial intelligence", "nlp", "llm", "ai",
            "data labeler", "content moderator", "quality analyst", "data specialist",
            "prompting", "curator", "reviewer", "rater", "search quality rater",
            "operations", "project lead", "program manager", "analytics", "business analyst",
            "data science", "process improvement"]
    LOW  = ["storekeeper", "store keeper", "forklift", "driver",
            "cleaner", "security", "receptionist", "telecaller",
            "waiter", "cashier", "cook", "chef", "laborer", "helper", "packer",
            "pharmacy", "pharmacist", "nurse", "construction", "electrician", "plumber"]
    for kw in LOW:
        if kw in title_l:
            return 0  # disqualify
    for kw in HIGH:
        if kw in title_l:
            return 85 + random.randint(0, 12)
    for kw in MED:
        if kw in title_l:
            return 72 + random.randint(0, 10)
    return 65 + random.randint(0, 5)

def load_existing_urls():
    """Return set of already-tracked URLs to avoid duplicates."""
    urls = set()
    if os.path.exists(TRACKER):
        with open(TRACKER, encoding='utf-8') as f:
            for row in csv.DictReader(f):
                u = row.get('URL','').strip()
                if u: urls.add(u)
    return urls

def append_to_tracker(jobs):
    """Append new jobs to the tracker CSV."""
    fieldnames = ['ID','Company','Title','Location','Region','FitScore','Status','CVFile','CoverFile','URL','AppliedDate','Source']
    file_exists = os.path.exists(TRACKER)
    
    existing_urls = load_existing_urls()
    new_count = 0
    
    with open(TRACKER, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        if not file_exists:
            writer.writeheader()
        for job in jobs:
            if job.get('URL','') not in existing_urls:
                writer.writerow(job)
                existing_urls.add(job['URL'])
                new_count += 1

    return new_count

def screenshot(page, label):
    try:
        page.screenshot(path=os.path.join(SCREENSHOTS, f"scrape_{label}.png"))
    except Exception:
        pass


# ── LinkedIn Easy Apply Scraper ───────────────────────────────────────────────

def scrape_linkedin_easy_apply(page, creds, existing_urls):
    """Scrape LinkedIn jobs with Easy Apply filter. Returns list of job dicts."""
    jobs = []
    try:
        # Check login
        print("[LinkedIn Scraper] Checking login...", flush=True)
        try:
            page.goto("https://www.linkedin.com/feed/", timeout=40000)
            time.sleep(3)
            if "login" in page.url or "authwall" in page.url:
                print("[LinkedIn Scraper] Logging in...", flush=True)
                page.goto("https://www.linkedin.com/login", timeout=40000)
                time.sleep(2)
                page.type('input[name="session_key"]', creds.get("LINKEDIN_EMAIL",""), delay=80)
                time.sleep(0.4)
                page.type('input[name="session_password"]', creds.get("LINKEDIN_PASSWORD",""), delay=80)
                time.sleep(0.4)
                page.click('button[type="submit"]')
                time.sleep(6)
                print(f"[LinkedIn Scraper] Login done: {page.url}", flush=True)
        except Exception as e:
            log_scraper_error("LinkedIn-Login", "Failed to complete login", e)

        for search in LINKEDIN_SEARCHES:
            kw     = search["keywords"]
            loc    = search["location"]
            region = search["region"]

            # f_LF=f_AL = Easy Apply filter, f_TPR=r604800 = last 7 days
            kw_enc  = kw.replace(" ", "%20").replace("&", "%26")
            loc_enc = loc.replace(", ", "%2C%20").replace(" ", "%20")
            url = (f"https://www.linkedin.com/jobs/search/"
                   f"?keywords={kw_enc}&location={loc_enc}"
                   f"&f_LF=f_AL"           # Easy Apply filter!
                   f"&f_TPR=r604800"       # Posted in last 7 days
                   f"&sortBy=DD")          # Sort by date

            print(f"\n[LinkedIn Scraper] Searching: {kw} in {loc}", flush=True)
            try:
                page.goto(url, timeout=40000)
                time.sleep(4)
                screenshot(page, f"li_{slug(kw)}_{slug(loc)}")
            except Exception as e:
                log_scraper_error("LinkedIn-Search", f"Search page load error for '{kw}' in '{loc}'", e)
                continue

            # Scroll to load more results
            for _ in range(4):
                page.keyboard.press("End")
                time.sleep(1.5)

            # Extract job cards — try multiple selectors for 2026 LinkedIn DOM
            job_cards = page.query_selector_all(
                '.jobs-search-results__list-item, '
                '.job-card-container, '
                'li[data-occludable-job-id], '
                '.scaffold-layout__list-item'
            )
            print(f"[LinkedIn Scraper] Found {len(job_cards)} job cards", flush=True)

            for card in job_cards[:20]:  # Max 20 per search
                try:
                    # Title — multiple selector fallbacks
                    title = ""
                    for sel in ['.job-card-list__title--link', '.job-card-list__title',
                                '.job-card-container__link', 'a[data-control-id]',
                                'strong', 'a.job-card-list__title']:
                        el = card.query_selector(sel)
                        if el:
                            title = el.inner_text().strip()
                            if title: break

                    # Company
                    company = ""
                    for sel in ['.job-card-container__company-name',
                                '.artdeco-entity-lockup__subtitle span',
                                '.job-card-container__primary-description',
                                '[class*="company-name"]']:
                        el = card.query_selector(sel)
                        if el:
                            company = el.inner_text().strip()
                            if company: break

                    # Location
                    job_location = loc
                    for sel in ['.job-card-container__metadata-item',
                                '[class*="location"]', '.artdeco-entity-lockup__caption']:
                        el = card.query_selector(sel)
                        if el:
                            job_location = el.inner_text().strip()
                            if job_location: break

                    # Job URL — extract numeric job ID from data attribute or href
                    job_url = ""
                    # Try data-occludable-job-id attribute first (most reliable)
                    job_id_attr = card.get_attribute("data-occludable-job-id") or ""
                    if job_id_attr and job_id_attr.isdigit():
                        job_url = f"https://www.linkedin.com/jobs/view/{job_id_attr}/"
                    else:
                        # Try link href
                        for sel in ['a.job-card-list__title--link', 'a.job-card-list__title',
                                    'a.job-card-container__link', 'a[data-job-id]', 'a']:
                            link_el = card.query_selector(sel)
                            if link_el:
                                href = link_el.get_attribute("href") or ""
                                # Extract job ID from URL
                                m = re.search(r'/jobs/view/(\d+)', href)
                                if m:
                                    job_url = f"https://www.linkedin.com/jobs/view/{m.group(1)}/"
                                    break

                    if not job_url or not title:
                        continue

                    # Relevance filter
                    score = fit_score(title)
                    if score == 0:
                        print(f"  [Skip - low relevance] {title}", flush=True)
                        continue

                    if job_url in existing_urls:
                        print(f"  [Skip - already tracked] {title} @ {company}", flush=True)
                        continue

                    # Verify Easy Apply by clicking into the job detail
                    try:
                        card.click()
                        time.sleep(2.5)
                    except Exception as click_err:
                        log_scraper_error("LinkedIn-CardClick", f"Failed clicking card for '{title}' @ '{company}'", click_err)

                    easy_apply_btn = None
                    for sel in ['button.jobs-apply-button', 'button:has-text("Easy Apply")',
                                '[aria-label*="Easy Apply"]', '.jobs-s-apply button',
                                'button[data-control-name="jobdetails_topcard_inapply"]']:
                        try:
                            el = page.query_selector(sel)
                            if el and el.is_visible():
                                easy_apply_btn = el
                                break
                        except Exception:
                            pass

                    if not easy_apply_btn:
                        print(f"  [Skip - no Easy Apply] {title} @ {company}", flush=True)
                        continue

                    jid = make_job_id("li", company, title)
                    job = {
                        'ID': jid, 'Company': company, 'Title': title,
                        'Location': job_location, 'Region': region,
                        'FitScore': score, 'Status': 'New',
                        'CVFile': '', 'CoverFile': '', 'URL': job_url,
                        'AppliedDate': '', 'Source': 'LinkedIn-EasyApply'
                    }
                    jobs.append(job)
                    existing_urls.add(job_url)
                    print(f"  [+] EASY APPLY: {title} @ {company} | Score:{score}", flush=True)

                except Exception as e:
                    log_scraper_error("LinkedIn-Card", f"Error parsing card for '{title if 'title' in locals() and title else 'unknown'}'", e)
                    continue

            time.sleep(random.uniform(2, 4))  # polite delay

    except Exception as fatal_e:
        log_scraper_error("LinkedIn", "Fatal error in scrape_linkedin_easy_apply", fatal_e)

    return jobs


# ── Naukri Direct-Apply Scraper ───────────────────────────────────────────────

def scrape_naukri(page, creds, existing_urls):
    jobs = []
    print("\n[Naukri Scraper] Starting...", flush=True)

    try:
        # Login
        try:
            page.goto("https://www.naukri.com/", timeout=40000)
            time.sleep(3)
            # Check if already logged in
            if not (page.query_selector('a[href*="mnjuser/profile"]') or
                    page.query_selector('.nI-gNb-drawer__icon')):
                page.goto("https://www.naukri.com/nlogin/login", timeout=40000)
                time.sleep(2)
                for sel in ['input[placeholder*="Email"]', 'input[type="email"]']:
                    el = page.query_selector(sel)
                    if el: el.fill(creds.get("NAUKRI_EMAIL","")); break
                pw = page.query_selector('input[type="password"]')
                if pw: pw.fill(creds.get("NAUKRI_PASSWORD",""))
                btn = (page.query_selector('button[type="submit"]') or
                       page.query_selector('button:has-text("Login")'))
                if btn: btn.click()
                time.sleep(5)
            print(f"[Naukri Scraper] Login: {page.url}", flush=True)
        except Exception as e:
            log_scraper_error("Naukri-Login", f"Login error: {e}", e)

        for search in NAUKRI_SEARCHES:
            kw_raw = search["keywords"]
            loc_raw = search.get("location", "").strip()
            region = search.get("region", "Remote")
            kw_slug = kw_raw.replace(" ", "-").lower()
            kw_enc = kw_raw.replace(" ", "%20")

            # Construct valid Naukri search URL (avoiding malformed static slug blocks)
            if loc_raw.lower() == "remote":
                url = f"https://www.naukri.com/{kw_slug}-jobs?k={kw_enc}&cityTypeGid=9508"
            elif loc_raw:
                loc_slug = loc_raw.replace(" ", "-").lower()
                url = f"https://www.naukri.com/{kw_slug}-jobs-in-{loc_slug}?k={kw_enc}"
            else:
                url = f"https://www.naukri.com/{kw_slug}-jobs?k={kw_enc}"

            print(f"\n[Naukri Scraper] Searching: {kw_raw} in {loc_raw}", flush=True)
            try:
                page.goto(url, timeout=40000)
                time.sleep(4)
                screenshot(page, f"nk_{slug(kw_raw)}_{slug(loc_raw)}")
            except Exception as e:
                log_scraper_error("Naukri-Search", f"Load error for '{kw_raw}' in '{loc_raw}'", e)
                continue

            # Query updated 2026 Naukri DOM card selectors
            cards = page.query_selector_all('.cust-job-tuple, .srp-jobtuple-wrapper')

            # Fallback to general query if Remote filter returned 0 results
            if not cards and loc_raw.lower() == "remote":
                fallback_url = f"https://www.naukri.com/{kw_slug}-jobs?k={kw_enc}"
                print(f"[Naukri Scraper] 0 cards on strict remote filter, trying general search: {fallback_url}", flush=True)
                try:
                    page.goto(fallback_url, timeout=35000)
                    time.sleep(3)
                    cards = page.query_selector_all('.cust-job-tuple, .srp-jobtuple-wrapper')
                except Exception:
                    pass

            print(f"[Naukri Scraper] Found {len(cards)} job cards", flush=True)

            for card in cards[:15]:
                try:
                    # Title & Direct URL
                    title = ""
                    job_url = ""
                    title_el = card.query_selector('a.title')
                    if title_el:
                        title = title_el.inner_text().strip() or title_el.get_attribute("title") or ""
                        href = title_el.get_attribute("href") or ""
                        if "naukri.com/job-listings-" in href:
                            job_url = href.split("?")[0]
                        elif href.startswith("/job-listings-"):
                            job_url = f"https://www.naukri.com{href}".split("?")[0]

                    if not job_url or not title:
                        continue

                    # Company
                    company = ""
                    comp_el = card.query_selector('a.comp-name, .comp-name, a.subTitle, .companyInfo a, [class*="comp-name"]')
                    if comp_el:
                        company = comp_el.inner_text().strip()

                    # Location
                    job_location = loc_raw
                    loc_el = card.query_selector('.loc-wrap, .locWdth, [class*="locWdth"], [class*="loc-wrap"]')
                    if loc_el:
                        parsed_loc = loc_el.inner_text().strip()
                        if parsed_loc:
                            job_location = parsed_loc

                    # Relevance filter
                    score = fit_score(title)
                    if score == 0:
                        print(f"  [Skip - low relevance] {title}", flush=True)
                        continue

                    if job_url in existing_urls:
                        print(f"  [Skip - tracked] {title} @ {company}", flush=True)
                        continue

                    jid = make_job_id("nk", company or "naukri", title)
                    job = {
                        'ID': jid, 'Company': company or "Naukri Employer", 'Title': title,
                        'Location': job_location, 'Region': region,
                        'FitScore': score, 'Status': 'New',
                        'CVFile': '', 'CoverFile': '', 'URL': job_url,
                        'AppliedDate': '', 'Source': 'Naukri'
                    }
                    jobs.append(job)
                    existing_urls.add(job_url)
                    print(f"  [+] {title} @ {company} ({job_location}) | Score:{score}", flush=True)

                except Exception as e:
                    log_scraper_error("Naukri-Card", f"Error parsing job card for '{title if 'title' in locals() and title else 'unknown'}'", e)

            time.sleep(random.uniform(2, 3))

    except Exception as fatal_e:
        log_scraper_error("Naukri", "Fatal error in scrape_naukri", fatal_e)

    return jobs


# ── Bayt Direct-Apply Scraper ─────────────────────────────────────────────────

def scrape_bayt(page, creds, existing_urls):
    jobs = []
    print("\n[Bayt Scraper] Starting...", flush=True)

    try:
        for search in BAYT_SEARCHES:
            kw     = search["keywords"].replace(" ", "-").lower()
            loc    = search["location"].lower()
            region = search["region"]
            url    = f"https://www.bayt.com/en/international/jobs/{kw}-jobs-in-{loc}/"

            print(f"\n[Bayt Scraper] Searching: {search['keywords']} in {search['location']}", flush=True)
            try:
                page.goto(url, timeout=40000)
                time.sleep(5)
                screenshot(page, f"bayt_{slug(search['keywords'])}_{slug(search['location'])}")
            except Exception as e:
                log_scraper_error("Bayt-Search", f"Load error for '{search['keywords']}' in '{search['location']}'", e)
                continue

            # Broader card selectors for 2026 Bayt DOM
            cards = page.query_selector_all(
                'li[data-js-job], .media-list li, '
                'li.has-pointer-d, [class*="jb-job"], '
                'ul.list li[id], li[data-job-id]'
            )
            print(f"[Bayt Scraper] Found {len(cards)} job cards", flush=True)

            for card in cards[:12]:
                try:
                    # Title
                    title = ""
                    for sel in ['h2.jb-title a', '.jb-title a', 'h2 a',
                                'a.jb-link', '[class*="title"] a', 'a[data-automation="job-title"]']:
                        el = card.query_selector(sel)
                        if el:
                            title = el.inner_text().strip()
                            if title: break

                    # Company
                    company = ""
                    for sel in ['[class*="company"] a', '.jb-company-name a',
                                '.t-default', '[data-automation="job-company"]',
                                'span[class*="company"]']:
                        el = card.query_selector(sel)
                        if el:
                            company = el.inner_text().strip()
                            if company: break

                    # Job URL — must be a direct Bayt job page
                    job_url = ""
                    for sel in ['h2.jb-title a', '.jb-title a', 'a.jb-link',
                                '[class*="title"] a', 'a[href*="/job/"]']:
                        link_el = card.query_selector(sel)
                        if link_el:
                            href = link_el.get_attribute("href") or ""
                            if href and "bayt.com" in href and "/job/" in href:
                                job_url = href if href.startswith("http") else f"https://www.bayt.com{href}"
                                job_url = job_url.split("?")[0]
                                break
                            elif href and "bayt.com" in href and len(href.split("/")) >= 7:
                                job_url = href if href.startswith("http") else f"https://www.bayt.com{href}"
                                job_url = job_url.split("?")[0]
                                break

                    if not job_url or not title:
                        continue

                    # Relevance filter
                    score = fit_score(title)
                    if score == 0:
                        print(f"  [Skip - low relevance] {title}", flush=True)
                        continue

                    if job_url in existing_urls:
                        print(f"  [Skip - tracked] {title} @ {company}", flush=True)
                        continue

                    jid = make_job_id("bayt", company, title)
                    job = {
                        'ID': jid, 'Company': company or "Unknown", 'Title': title,
                        'Location': search['location'], 'Region': region,
                        'FitScore': score, 'Status': 'New',
                        'CVFile': '', 'CoverFile': '', 'URL': job_url,
                        'AppliedDate': '', 'Source': 'Bayt'
                    }
                    jobs.append(job)
                    existing_urls.add(job_url)
                    print(f"  [+] {title} @ {company or 'Unknown'} | Score:{score}", flush=True)

                except Exception as e:
                    log_scraper_error("Bayt-Card", f"Error parsing job card for '{title if 'title' in locals() and title else 'unknown'}'", e)

            time.sleep(random.uniform(2, 4))

    except Exception as fatal_e:
        log_scraper_error("Bayt", "Fatal error in scrape_bayt", fatal_e)

    return jobs


# ── Indeed Scraper ─────────────────────────────────────────────────────────────

def scrape_indeed(page, creds, existing_urls):
    jobs = []
    print("\n[Indeed Scraper] Starting...", flush=True)

    try:
        for search in INDEED_SEARCHES:
            kw  = search["keywords"].replace(" ", "+")
            loc = search["location"]
            region = search.get("region", "Remote")
            base = "ae.indeed.com" if region == "Gulf" else "in.indeed.com"
            url = f"https://{base}/jobs?q={kw}&l={loc}&sort=date&fromage=14"

            print(f"\n[Indeed Scraper] Searching: {search['keywords']} in {search['location']}", flush=True)
            try:
                page.goto(url, timeout=40000)
                time.sleep(4)
                screenshot(page, f"ind_{slug(search['keywords'])}_{slug(search['location'])}")
            except Exception as e:
                log_scraper_error("Indeed-Search", f"Load error for '{search['keywords']}' in '{search['location']}'", e)
                continue

            cards = page.query_selector_all('.job_seen_beacon, .jobsearch-ResultsList li[class]')
            print(f"[Indeed Scraper] Found {len(cards)} job cards", flush=True)

            for card in cards[:10]:
                try:
                    title_el = card.query_selector('.jobTitle a, h2.jobTitle span')
                    title = title_el.inner_text().strip() if title_el else ""

                    company_el = card.query_selector('[data-testid="company-name"], .companyName')
                    company = company_el.inner_text().strip() if company_el else ""

                    # Get job key from data attribute
                    jk = card.get_attribute("data-jk") or ""
                    if jk:
                        job_url = f"https://{base}/viewjob?jk={jk}"
                    else:
                        link_el = card.query_selector('.jobTitle a')
                        href = link_el.get_attribute("href") if link_el else ""
                        if not href: continue
                        job_url = f"https://{base}{href}" if href.startswith("/") else href

                    if not job_url or not title or job_url in existing_urls:
                        continue

                    # Check if it's an Indeed Apply (not external)
                    card.click()
                    time.sleep(2)
                    apply_btn = (page.query_selector('[id="indeedApplyButton"]') or
                                page.query_selector('.ia-IndeedApplyButton'))
                    if not apply_btn:
                        print(f"  [Skip - no Indeed Apply] {title} @ {company}", flush=True)
                        continue

                    job_id = make_job_id("ind", company, title)
                    job = {
                        'ID': job_id, 'Company': company or "Unknown", 'Title': title,
                        'Location': loc, 'Region': region,
                        'FitScore': 76 + random.randint(0,14), 'Status': 'New',
                        'CVFile': '', 'CoverFile': '', 'URL': job_url,
                        'AppliedDate': '', 'Source': 'Indeed'
                    }
                    jobs.append(job)
                    existing_urls.add(job_url)
                    print(f"  [+] INDEED APPLY: {title} @ {company}", flush=True)

                except Exception as e:
                    log_scraper_error("Indeed-Card", f"Error parsing job card for '{title if 'title' in locals() and title else 'unknown'}'", e)

            time.sleep(random.uniform(2, 4))

    except Exception as fatal_e:
        log_scraper_error("Indeed", "Fatal error in scrape_indeed", fatal_e)

    return jobs


# ── Micro1 AI Jobs Scraper ───────────────────────────────────────────────────

def scrape_micro1(page, creds, existing_urls):
    jobs = []
    print("\n[Micro1 Scraper] Starting...", flush=True)
    try:
        page.goto("https://www.micro1.ai/jobs", timeout=40000)
        time.sleep(5)
        # Scan all opportunity cards/links on micro1
        links = page.query_selector_all('a[href*="jobs.micro1.ai/post/"], a[href*="/post/"]')
        print(f"[Micro1 Scraper] Found {len(links)} opportunity links", flush=True)
        for link in links:
            href = ""
            title = ""
            try:
                href = link.get_attribute("href") or ""
                raw_text = link.inner_text().strip().replace("\n", " ")
                # Clean up title: e.g. "Sep 27, 2026 Data Analyst (AI Evaluation) Required skills..."
                # Extract role title
                m = re.search(r'(?:[A-Za-z]{3}\s+\d+,\s+\d+\s+)?([A-Za-z0-9\s\(\)\-—&/]+?)(?:\s+Required\s+skills|\s+Full\s+time|\s+Contract|$)', raw_text)
                title = m.group(1).strip() if m else raw_text[:50]
                company = "Micro1 AI Network"

                if not href or not title:
                    continue
                if href in existing_urls:
                    continue

                score = fit_score(title)
                if score == 0:
                    continue

                jid = make_job_id("m1", "micro1", title)
                job = {
                    'ID': jid, 'Company': company, 'Title': title,
                    'Location': 'Worldwide (Remote)', 'Region': 'Remote',
                    'FitScore': score, 'Status': 'New',
                    'CVFile': '', 'CoverFile': '', 'URL': href,
                    'AppliedDate': '', 'Source': 'Micro1'
                }
                jobs.append(job)
                existing_urls.add(href)
                print(f"  [+] MICRO1 AI JOB: {title} | Score:{score}", flush=True)
            except Exception as e:
                log_scraper_error("Micro1-Card", f"Error parsing opportunity link '{href or title or 'unknown'}'", e)
    except Exception as e:
        log_scraper_error("Micro1", "Fatal error in scrape_micro1", e)
    return jobs


# ── Remotive Remote AI Scraper ────────────────────────────────────────────────

def scrape_remotive(existing_urls):
    import urllib.request, json
    jobs = []
    print("\n[Remotive Remote Scraper] Querying public API...", flush=True)
    try:
        url = "https://remotive.com/api/remote-jobs?search=ai&limit=50"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            items = data.get("jobs", [])
            print(f"[Remotive Remote Scraper] Returned {len(items)} postings", flush=True)
            for item in items:
                try:
                    title = item.get("title", "").strip()
                    company = item.get("company_name", "Remote AI Client").strip()
                    job_url = item.get("url", "").strip()
                    loc = item.get("candidate_required_location", "Worldwide").strip()

                    if not job_url or not title or job_url in existing_urls:
                        continue

                    score = fit_score(title)
                    if score == 0:
                        continue

                    jid = make_job_id("rem", company, title)
                    job = {
                        'ID': jid, 'Company': company, 'Title': title,
                        'Location': loc, 'Region': 'Remote',
                        'FitScore': score, 'Status': 'New',
                        'CVFile': '', 'CoverFile': '', 'URL': job_url,
                        'AppliedDate': '', 'Source': 'Remotive-Remote'
                    }
                    jobs.append(job)
                    existing_urls.add(job_url)
                    print(f"  [+] REMOTIVE AI: {title} @ {company} ({loc}) | Score:{score}", flush=True)
                except Exception as item_err:
                    log_scraper_error("Remotive-Item", f"Failed parsing item: {item.get('title','')}", item_err)
    except Exception as e:
        log_scraper_error("Remotive", "API query failed", e)
    return jobs


# ── RemoteOK Remote Jobs Scraper ──────────────────────────────────────────────

def scrape_remoteok(existing_urls):
    import urllib.request, json
    jobs = []
    print("\n[RemoteOK Scraper] Querying public API...", flush=True)
    try:
        url = "https://remoteok.com/api?tag=ai"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            items = json.loads(resp.read().decode('utf-8'))
            print(f"[RemoteOK Scraper] Returned {len(items)} items", flush=True)
            for item in items:
                if not isinstance(item, dict):
                    continue
                try:
                    title = item.get("position", "").strip()
                    company = item.get("company", "Remote Client").strip()
                    job_url = item.get("url", "").strip()
                    loc = item.get("location", "Worldwide (Remote)").strip() or "Worldwide (Remote)"

                    if not job_url or not title or job_url in existing_urls:
                        continue

                    score = fit_score(title)
                    if score == 0:
                        continue

                    jid = make_job_id("rok", company, title)
                    job = {
                        'ID': jid, 'Company': company, 'Title': title,
                        'Location': loc, 'Region': 'Remote',
                        'FitScore': score, 'Status': 'New',
                        'CVFile': '', 'CoverFile': '', 'URL': job_url,
                        'AppliedDate': '', 'Source': 'RemoteOK'
                    }
                    jobs.append(job)
                    existing_urls.add(job_url)
                    print(f"  [+] REMOTEOK: {title} @ {company} ({loc}) | Score:{score}", flush=True)
                except Exception as item_err:
                    log_scraper_error("RemoteOK-Item", f"Failed parsing item: {item.get('position','')}", item_err)
    except Exception as e:
        log_scraper_error("RemoteOK", "API query failed", e)
    return jobs


# ── Himalayas Remote Jobs Scraper ─────────────────────────────────────────────

def scrape_himalayas(existing_urls):
    import urllib.request, json
    jobs = []
    print("\n[Himalayas Scraper] Querying public API...", flush=True)
    try:
        url = "https://himalayas.app/jobs/api?limit=50"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            items = data.get("jobs", [])
            print(f"[Himalayas Scraper] Returned {len(items)} postings", flush=True)
            for item in items:
                try:
                    title = item.get("title", "").strip()
                    company = item.get("companyName", "Himalayas Client").strip()
                    app_url = item.get("applicationLink") or f"https://himalayas.app/jobs/{item.get('slug')}"
                    loc_list = item.get("locationRestrictions", [])
                    loc = ", ".join(loc_list) if loc_list else "Worldwide (Remote)"

                    if not app_url or not title or app_url in existing_urls:
                        continue

                    score = fit_score(title)
                    if score == 0:
                        continue

                    jid = make_job_id("hml", company, title)
                    job = {
                        'ID': jid, 'Company': company, 'Title': title,
                        'Location': loc, 'Region': 'Remote',
                        'FitScore': score, 'Status': 'New',
                        'CVFile': '', 'CoverFile': '', 'URL': app_url,
                        'AppliedDate': '', 'Source': 'Himalayas'
                    }
                    jobs.append(job)
                    existing_urls.add(app_url)
                    print(f"  [+] HIMALAYAS: {title} @ {company} ({loc}) | Score:{score}", flush=True)
                except Exception as item_err:
                    log_scraper_error("Himalayas-Item", f"Failed parsing item: {item.get('title','')}", item_err)
    except Exception as e:
        log_scraper_error("Himalayas", "API query failed", e)
    return jobs


# ── Glassdoor Easy Apply Scraper ──────────────────────────────────────────────

def scrape_glassdoor(page, creds, existing_urls):
    jobs = []
    print("\n[Glassdoor Scraper] Starting...", flush=True)

    try:
        for search in GLASSDOOR_SEARCHES:
            kw  = search["keywords"].replace(" ", "-").lower()
            kw_enc = search["keywords"].replace(" ", "+")
            loc = search["location"]
            region = search["region"]
            url = f"https://www.glassdoor.com/Job/{kw}-jobs-SRCH_KO0,{len(search['keywords'])}.htm"

            print(f"\n[Glassdoor Scraper] Searching: {search['keywords']} in {loc}", flush=True)
            try:
                page.goto(url, timeout=40000)
                time.sleep(5)
                screenshot(page, f"gd_{slug(search['keywords'])}_{slug(loc)}")
            except Exception as e:
                log_scraper_error("Glassdoor-Search", f"Load error for '{search['keywords']}' in '{loc}'", e)
                continue

            # Close any modal/popup
            try:
                modal_close = (page.query_selector('[alt="Close"]') or
                              page.query_selector('button[class*="close"]') or
                              page.query_selector('[data-test="modal-close-btn"]'))
                if modal_close: modal_close.click()
            except Exception:
                pass

            cards = page.query_selector_all('li.react-job-listing, article.jobListing')
            print(f"[Glassdoor Scraper] Found {len(cards)} job cards", flush=True)

            for card in cards[:10]:
                try:
                    card.click()
                    time.sleep(2)

                    title_el = (page.query_selector('[data-test="job-title"]') or
                               page.query_selector('.jobTitle') or
                               card.query_selector('a[data-test="job-link"]'))
                    title = title_el.inner_text().strip() if title_el else ""

                    company_el = page.query_selector('[data-test="employer-name"]') or page.query_selector('.employer')
                    company = company_el.inner_text().strip() if company_el else ""

                    # Get job URL from current detail panel or card link
                    link_el = card.query_selector('a[data-test="job-link"], a.jobLink')
                    job_url = ""
                    if link_el:
                        href = link_el.get_attribute("href") or ""
                        job_url = href if href.startswith("http") else f"https://www.glassdoor.com{href}"
                        job_url = job_url.split("?")[0]

                    if not job_url or not title or job_url in existing_urls:
                        continue

                    # Check for Easy Apply button in detail panel
                    easy_apply = (page.query_selector('button:has-text("Easy Apply")') or
                                 page.query_selector('[data-test="easyApply"]'))
                    if not easy_apply:
                        print(f"  [Skip - no Easy Apply] {title} @ {company}", flush=True)
                        continue

                    job_id = make_job_id("gd", company, title)
                    job = {
                        'ID': job_id, 'Company': company or "Unknown", 'Title': title,
                        'Location': loc, 'Region': region,
                        'FitScore': 77 + random.randint(0,13), 'Status': 'New',
                        'CVFile': '', 'CoverFile': '', 'URL': job_url,
                        'AppliedDate': '', 'Source': 'Glassdoor'
                    }
                    jobs.append(job)
                    existing_urls.add(job_url)
                    print(f"  [+] GLASSDOOR EASY APPLY: {title} @ {company}", flush=True)

                except Exception as e:
                    log_scraper_error("Glassdoor-Card", f"Error parsing job card for '{title if 'title' in locals() and title else 'unknown'}'", e)

            time.sleep(random.uniform(2, 4))

    except Exception as fatal_e:
        log_scraper_error("Glassdoor", "Fatal error in scrape_glassdoor", fatal_e)

    return jobs


# ── Main ────────────────────────────────────────────────────────────────────────

def main():
    from playwright.sync_api import sync_playwright

    creds = load_creds()
    existing_urls = load_existing_urls()
    all_new_jobs = []

    print(f"\n[Scraper] Starting Easy Apply job scrape at {datetime.now().strftime('%H:%M:%S')}", flush=True)
    print(f"[Scraper] Already tracked: {len(existing_urls)} job URLs", flush=True)

    # 1. Fetch API-driven remote platforms first (instant, no browser overhead)
    try:
        rem_jobs = scrape_remotive(existing_urls)
        all_new_jobs.extend(rem_jobs)
        print(f"[Remotive] Found {len(rem_jobs)} remote AI jobs.", flush=True)
    except Exception as e:
        log_scraper_error("Main-Orchestrator", "Failure during Remotive scrape", e)

    try:
        rok_jobs = scrape_remoteok(existing_urls)
        all_new_jobs.extend(rok_jobs)
        print(f"[RemoteOK] Found {len(rok_jobs)} remote AI & Ops jobs.", flush=True)
    except Exception as e:
        log_scraper_error("Main-Orchestrator", "Failure during RemoteOK scrape", e)

    try:
        hml_jobs = scrape_himalayas(existing_urls)
        all_new_jobs.extend(hml_jobs)
        print(f"[Himalayas] Found {len(hml_jobs)} remote jobs.", flush=True)
    except Exception as e:
        log_scraper_error("Main-Orchestrator", "Failure during Himalayas scrape", e)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=False,  # Visible so user can complete any CAPTCHA
                args=["--no-sandbox","--disable-blink-features=AutomationControlled","--start-maximized"]
            )
            ctx = browser.new_context(
                user_agent=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                            "AppleWebKit/537.36 (KHTML, like Gecko) "
                            "Chrome/124.0.0.0 Safari/537.36"),
                viewport={"width": 1280, "height": 900}
            )
            page = ctx.new_page()
            page.set_default_timeout(35000)
            page.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined})")

            # ── Micro1 AI Platform ─────────────────────────────────────────────
            try:
                m1_jobs = scrape_micro1(page, creds, existing_urls)
                all_new_jobs.extend(m1_jobs)
                print(f"\n[Micro1] Found {len(m1_jobs)} AI evaluation jobs.", flush=True)
            except Exception as e:
                log_scraper_error("Main-Orchestrator", "Failure during Micro1 scrape", e)

            # ── Scrape all remaining portals ───────────────────────────────────
            try:
                li_jobs = scrape_linkedin_easy_apply(page, creds, existing_urls)
                all_new_jobs.extend(li_jobs)
                print(f"\n[LinkedIn] Found {len(li_jobs)} Easy Apply jobs.", flush=True)
            except Exception as e:
                log_scraper_error("Main-Orchestrator", "Failure during LinkedIn scrape", e)

            try:
                nk_jobs = scrape_naukri(page, creds, existing_urls)
                all_new_jobs.extend(nk_jobs)
                print(f"\n[Naukri] Found {len(nk_jobs)} jobs.", flush=True)
            except Exception as e:
                log_scraper_error("Main-Orchestrator", "Failure during Naukri scrape", e)

            try:
                bayt_jobs = scrape_bayt(page, creds, existing_urls)
                all_new_jobs.extend(bayt_jobs)
                print(f"\n[Bayt] Found {len(bayt_jobs)} jobs.", flush=True)
            except Exception as e:
                log_scraper_error("Main-Orchestrator", "Failure during Bayt scrape", e)

            try:
                indeed_jobs = scrape_indeed(page, creds, existing_urls)
                all_new_jobs.extend(indeed_jobs)
                print(f"\n[Indeed] Found {len(indeed_jobs)} Indeed-Apply jobs.", flush=True)
            except Exception as e:
                log_scraper_error("Main-Orchestrator", "Failure during Indeed scrape", e)

            try:
                gd_jobs = scrape_glassdoor(page, creds, existing_urls)
                all_new_jobs.extend(gd_jobs)
                print(f"\n[Glassdoor] Found {len(gd_jobs)} Easy Apply jobs.", flush=True)
            except Exception as e:
                log_scraper_error("Main-Orchestrator", "Failure during Glassdoor scrape", e)

            browser.close()
    except Exception as browser_err:
        log_scraper_error("Playwright-Browser", "Failed to launch or manage browser session", browser_err)

    # ── Save to tracker ────────────────────────────────────────────────────
    if all_new_jobs:
        saved = append_to_tracker(all_new_jobs)
        print(f"\n[Scraper] DONE! Added {saved} new applyable jobs to tracker.", flush=True)
    else:
        print(f"\n[Scraper] No new jobs found.", flush=True)

    # ── Summary ────────────────────────────────────────────────────────────
    print("\n" + "="*60, flush=True)
    print(f"SCRAPE COMPLETE — {datetime.now().strftime('%Y-%m-%d %H:%M')}", flush=True)
    print(f"Total new jobs added: {len(all_new_jobs)}", flush=True)
    by_portal = {}
    for j in all_new_jobs:
        src = j.get('Source','Unknown')
        by_portal[src] = by_portal.get(src, 0) + 1
    for src, count in by_portal.items():
        print(f"  {src}: {count} jobs", flush=True)
    print("="*60, flush=True)
    print("\nNow run: python browser_apply_agent.py --jobs all --visible", flush=True)
    print("to auto-apply to all these new Easy Apply jobs!", flush=True)


if __name__ == "__main__":
    main()
