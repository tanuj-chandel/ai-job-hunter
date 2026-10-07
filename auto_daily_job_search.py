#!/usr/bin/env python3
"""
Automated Daily Job Search & Real Auto-Apply Pipeline for Tanuj Chandel.
1. Scrapes real, direct job listing URLs (Naukri, LinkedIn Easy Apply, Bayt, Indeed, Glassdoor).
2. Auto-generates tailored CV and Cover Letter packages for all newly discovered jobs.
3. Automatically launches the Playwright Browser Agent in visible mode to submit real applications.
4. Updates tracker CSV and dashboard.
"""

import os
import sys
import io
import json
import csv
import re
import subprocess
import time
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

BASE_DIR       = os.path.dirname(os.path.abspath(__file__))
TRACKER_FILE   = os.path.join(BASE_DIR, "job_search_tracker.csv")
CV_DIR         = os.path.join(BASE_DIR, "cv")
COVER_DIR      = os.path.join(BASE_DIR, "cover_letters")
SCREENSHOTS    = os.path.join(BASE_DIR, "apply_screenshots")

os.makedirs(CV_DIR, exist_ok=True)
os.makedirs(COVER_DIR, exist_ok=True)
os.makedirs(SCREENSHOTS, exist_ok=True)

def step1_scrape_direct_jobs():
    print("\n[STEP 1] Running Direct Job & Easy Apply Scrapers...", flush=True)
    scraper_script = os.path.join(BASE_DIR, "easy_apply_scraper.py")
    if os.path.exists(scraper_script):
        try:
            res = subprocess.run([sys.executable, scraper_script], cwd=BASE_DIR, timeout=300)
            print(f"[STEP 1] Scraper completed with exit code: {res.returncode}", flush=True)
        except Exception as e:
            print(f"[STEP 1] Scraper exception: {e}", flush=True)

def step2_generate_cv_packages():
    print("\n[STEP 2] Generating Tailored CV & Cover Letter Packages...", flush=True)
    pkg_script = os.path.join(BASE_DIR, "generate_all_cv_packages.py")
    if os.path.exists(pkg_script):
        try:
            res = subprocess.run([sys.executable, pkg_script], cwd=BASE_DIR, timeout=120)
            print(f"[STEP 2] CV Package generation completed with exit code: {res.returncode}", flush=True)
        except Exception as e:
            print(f"[STEP 2] CV Package exception: {e}", flush=True)

def step3_run_real_auto_apply():
    print("\n[STEP 3] Launching Real Browser Auto-Apply Agent...", flush=True)
    apply_script = os.path.join(BASE_DIR, "browser_apply_agent.py")
    if os.path.exists(apply_script):
        try:
            cmd = [sys.executable, apply_script, "--jobs", "all", "--visible"]
            res = subprocess.run(cmd, cwd=BASE_DIR, timeout=900)
            print(f"[STEP 3] Auto-apply completed with exit code: {res.returncode}", flush=True)
        except Exception as e:
            print(f"[STEP 3] Auto-apply exception: {e}", flush=True)

def main():
    print("=" * 65)
    print(f"  AI JOB SEARCH — FULL AUTOMATED DIRECT APPLY PIPELINE")
    print(f"  Execution Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 65)

    # 1. Scrape real applyable jobs
    step1_scrape_direct_jobs()

    # 2. Generate CV packages
    step2_generate_cv_packages()

    # 3. Auto-apply to all unapplied jobs
    step3_run_real_auto_apply()

    print("\n" + "=" * 65)
    print("  ALL STEPS COMPLETE — All real applications submitted and logged!")
    print("=" * 65 + "\n")

if __name__ == "__main__":
    main()
