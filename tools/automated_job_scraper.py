#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Automated Job Scraper & Triage Pipeline for Tanuj Chandel
Queries LinkedIn and Freehire CLI search engines, filters duplicates,
calculates heuristic fit scores, and updates the jobs dashboard.
"""

import os
import sys
import json
import random
import time
import subprocess
import re
import csv
from datetime import datetime

# Define workspace directories relative to the tools directory
WORKSPACE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SEEN_JOBS_FILE = os.path.join(WORKSPACE_DIR, "job_scraper", "seen_jobs.json")
TRACKER_FILE = os.path.join(WORKSPACE_DIR, "job_search_tracker.csv")
DASHBOARD_FILE = os.path.join(WORKSPACE_DIR, "jobs_dashboard.md")

# Default Target Locations & Query Categories
TARGET_LOCATIONS = [
    "Kanpur, Uttar Pradesh, India",
    "Delhi NCR, India",
    "Mumbai, Maharashtra, India",
    "Bengaluru, Karnataka, India",
    "Pune, Maharashtra, India",
    "Dubai, United Arab Emirates",
    "Abu Dhabi, United Arab Emirates",
    "Riyadh, Saudi Arabia",
    "Doha, Qatar",
    "Muscat, Oman"
]

PRIORITY_QUERIES = [
    # Priority 1: Operations & Supply Chain
    ("Operations Manager", 1),
    ("Supply Chain Manager", 1),
    ("Warehouse Manager", 1),
    ("Logistics Manager", 1),
    # Priority 2: Cold Chain / Agri
    ("Cold Chain Manager", 2),
    ("Cold Storage Operations", 2),
    ("Agri-business Manager", 2),
    # Priority 3: AI-Enabled Operations
    ("Operations Transformation Manager", 3),
    # Priority 4: Corporate Sales
    ("B2B Sales Manager", 4),
    ("Key Account Manager", 4)
]

def find_bun_executable():
    """Locate the bun executable on the Windows system."""
    # Try system PATH
    try:
        subprocess.run(["bun", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return "bun"
    except (subprocess.SubprocessError, FileNotFoundError):
        pass

    # Try standard user profile location
    user_profile = os.environ.get("USERPROFILE", "C:\\Users\\91879")
    bun_path = os.path.join(user_profile, ".bun", "bin", "bun.exe")
    if os.path.exists(bun_path):
        return bun_path

    # Fallback default
    return "bun"

def load_seen_jobs():
    """Load previously seen jobs from seen_jobs.json."""
    if not os.path.exists(SEEN_JOBS_FILE):
        os.makedirs(os.path.dirname(SEEN_JOBS_FILE), exist_ok=True)
        return {"seen": {}}
    try:
        with open(SEEN_JOBS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Failed to load seen_jobs.json ({e}). Starting fresh.")
        return {"seen": {}}

def save_seen_jobs(seen_data):
    """Save seen jobs to seen_jobs.json."""
    try:
        with open(SEEN_JOBS_FILE, 'w', encoding='utf-8') as f:
            json.dump(seen_data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error: Failed to save seen_jobs.json ({e})")

def load_tracker_jobs():
    """Extract already-applied company + role keys from tracker.csv."""
    applied_keys = set()
    if not os.path.exists(TRACKER_FILE):
        return applied_keys
    try:
        with open(TRACKER_FILE, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            # Skip header if present
            next(reader, None)
            for row in reader:
                if len(row) >= 2:
                    company = row[0].strip().lower()
                    role = row[1].strip().lower()
                    applied_keys.add(f"{company}_{role}")
    except Exception as e:
        print(f"Warning: Failed to parse tracker.csv ({e})")
    return applied_keys

def get_job_unique_key(job):
    """Create a unique key for deduplication."""
    url = job.get("url") or ""
    if url:
        # Normalize url by stripping parameters
        normalized_url = url.split("?")[0].strip().lower()
        if normalized_url:
            return normalized_url

    company = (job.get("company") or "").strip().lower()
    title = (job.get("title") or "").strip().lower()
    return f"{company}_{title}"

def run_linkedin_search(bun_exec, query, location):
    """Run the LinkedIn search CLI tool and return results list."""
    cli_path = os.path.join(WORKSPACE_DIR, ".agents", "skills", "linkedin-search", "cli", "src", "cli.ts")
    cmd = [
        bun_exec, "run", cli_path, "search",
        "-q", query,
        "-l", location,
        "--jobage", "14",
        "--format", "json"
    ]
    
    print(f"Running LinkedIn search: '{query}' in '{location}'...")
    try:
        # Override process environment to bypass SSL check locally
        env = os.environ.copy()
        env["NODE_TLS_REJECT_UNAUTHORIZED"] = "0"
        
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env, check=False)
        if result.returncode != 0:
            print(f"Error executing LinkedIn search CLI: {result.stderr.strip()}")
            return []
        
        # Parse JSON output from stdout
        output = result.stdout.strip()
        if not output:
            return []
        
        data = json.loads(output)
        if isinstance(data, dict) and "results" in data:
            return data["results"]
        elif isinstance(data, list):
            return data
    except Exception as e:
        print(f"Exception during LinkedIn search: {e}")
    return []

def run_freehire_search(bun_exec, query):
    """Run the Freehire search CLI tool for India & Gulf region."""
    cli_path = os.path.join(WORKSPACE_DIR, ".agents", "skills", "freehire-search", "cli", "src", "cli.ts")
    cmd = [
        bun_exec, "run", cli_path, "search",
        "-q", query,
        "--region", "apac",
        "--format", "json",
        "--limit", "15"
    ]
    
    print(f"Running Freehire search for tech/startup roles: '{query}'...")
    try:
        env = os.environ.copy()
        env["NODE_TLS_REJECT_UNAUTHORIZED"] = "0"
        
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env, check=False)
        if result.returncode != 0:
            return []
        
        output = result.stdout.strip()
        if not output:
            return []
        
        data = json.loads(output)
        if isinstance(data, dict) and "results" in data:
            return data["results"]
        elif isinstance(data, list):
            return data
    except Exception as e:
        print(f"Exception during Freehire search: {e}")
    return []

def calculate_fit_score(title, company, location, snippet=""):
    """
    Calculate a heuristic fit score (0-100) based on Tanuj's profile.
    """
    title_lower = title.lower()
    location_lower = location.lower()
    snippet_lower = snippet.lower() if snippet else ""
    
    score = 40  # Base starting score
    
    # 1. Title Match Heuristics
    if "operations manager" in title_lower or "operations head" in title_lower or "director of operations" in title_lower:
        score += 25
    elif "warehouse manager" in title_lower or "facility manager" in title_lower or "hub manager" in title_lower:
        score += 25
    elif "supply chain" in title_lower or "logistics manager" in title_lower or "logistics lead" in title_lower:
        score += 20
    elif "cold chain" in title_lower or "cold storage" in title_lower:
        score += 30  # High domain matching
    elif "sales manager" in title_lower or "account manager" in title_lower:
        score += 10  # Secondary B2B sales path
    elif "operations" in title_lower or "logistics" in title_lower:
        score += 15
        
    # 2. Location Match & Relocation Tags
    is_home_region = False
    is_gulf = False
    
    if "kanpur" in location_lower or "uttar pradesh" in location_lower:
        score += 15
        is_home_region = True
    elif "delhi" in location_lower or "ncr" in location_lower or "pataudi" in location_lower:
        score += 10
        is_home_region = True
    elif "dubai" in location_lower or "united arab emirates" in location_lower or "uae" in location_lower or "riyadh" in location_lower or "saudi" in location_lower or "ksa" in location_lower or "qatar" in location_lower or "doha" in location_lower or "oman" in location_lower or "muscat" in location_lower:
        score += 8
        is_gulf = True
    else:
        score -= 10  # Lower priority for other regions
        
    # 3. Description/Snippet Keyword Matches
    keywords = {
        "cold storage": 10,
        "cold chain": 10,
        "food safety": 5,
        "haccp": 5,
        "iso 22000": 5,
        "p&l": 8,
        "profit and loss": 8,
        "budget": 5,
        "team": 3,
        "leadership": 3,
        "fleet": 5,
        "dispatch": 5,
        "routing": 5,
        "excel": 3,
        "n8n": 5,
        "claude": 5,
        "automation": 3,
        "b2b": 5,
        "corporate sales": 5
    }
    
    for kw, val in keywords.items():
        if kw in title_lower or kw in snippet_lower:
            score += val
            
    # Cap score between 0 and 100
    final_score = max(0, min(100, score))
    
    # Determine Fit Classification
    if final_score >= 80:
        fit = "High"
    elif final_score >= 60:
        fit = "Medium"
    else:
        fit = "Low"
        
    # Geographic Categorization Tag
    if is_home_region:
        geo_tag = "India - Home Region (No relocation)"
    elif is_gulf:
        geo_tag = "Gulf - Relocation + Visa Required"
    else:
        geo_tag = "India - Relocation Required"
        
    return final_score, fit, geo_tag

def update_jobs_dashboard(new_jobs_list):
    """Generate the jobs_dashboard.md file showing new job matches."""
    # Group jobs by fit
    high_fit = []
    med_fit = []
    
    for job in new_jobs_list:
        if job["fit"] == "High":
            high_fit.append(job)
        elif job["fit"] == "Medium":
            med_fit.append(job)
            
    # Sort each group by score descending
    high_fit.sort(key=lambda x: x["score"], reverse=True)
    med_fit.sort(key=lambda x: x["score"], reverse=True)
    
    total_found = len(new_jobs_list)
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    content = f"""# AI Job Search — Automated Dashboard

**Last Scan**: {date_str}  
**Total New Matches Found**: {total_found} ({len(high_fit)} High, {len(med_fit)} Medium, {total_found - len(high_fit) - len(med_fit)} Low)

---

## 🎯 High-Fit Opportunities

These roles match your profile statement, direct cold storage/logistics domain, or Kanpur/Gulf target areas.

| # | Fit | Title | Company | Location | Score | Link |
|---|-----|-------|---------|----------|-------|------|
"""
    
    for i, job in enumerate(high_fit, 1):
        content += f"| {i} | **High** | {job['title']} | {job['company']} | {job['location']} | **{job['score']}/100** | [View Listing]({job['url']}) |\n"
        
    content += """
### 💡 High-Match Focus Highlights
"""
    for i, job in enumerate(high_fit, 1):
        content += f"""
#### {i}. {job['title']} at **{job['company']}** ({job['location']})
* **Geo**: {job['geo_tag']}
* **Why it matches**: Fits your core Operations / Cold Chain capabilities. Score: **{job['score']}/100**.
* **Action**: Run the tailored apply workflow in your terminal using:
  ```bash
  /apply {job['url']}
  ```
"""

    content += f"""
---

## ⚖️ Medium-Fit Opportunities

These roles are adjacent to your experience, such as general logistics managers or B2B sales roles.

| # | Title | Company | Location | Score | Link |
|---|-------|---------|----------|-------|------|
"""
    
    for i, job in enumerate(med_fit, 1):
        content += f"| {i} | {job['title']} | {job['company']} | {job['location']} | {job['score']}/100 | [View Listing]({job['url']}) |\n"
        
    content += """
---
*Note: Low-fit jobs (<60/100 score) are recorded in state files but omitted from this dashboard to save your review time. To run a manual targeted query or refresh this dashboard, execute `/scrape` inside Claude Code.*
"""
    
    try:
        with open(DASHBOARD_FILE, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Jobs dashboard successfully updated at: {DASHBOARD_FILE}")
    except Exception as e:
        print(f"Error writing dashboard file: {e}")

def main():
    test_mode = "--test" in sys.argv
    print(f"Starting Automated Scraper pipeline in {'TEST' if test_mode else 'FULL'} mode...")
    
    bun_exec = find_bun_executable()
    seen_data = load_seen_jobs()
    applied_keys = load_tracker_jobs()
    
    # In test mode, we do exactly 1 query and 1 location to verify
    if test_mode:
        selected_locations = ["Kanpur, Uttar Pradesh, India"]
        selected_queries = [("Operations Manager", 1)]
    else:
        # Rate-Limiting Safety: Pick a random subset of 3 locations and 3 queries per scan
        # This keeps the daily run volume extremely low and safe
        selected_locations = random.sample(TARGET_LOCATIONS, min(3, len(TARGET_LOCATIONS)))
        # Always include Kanpur or Dubai/Riyadh in the sample for high relevance
        if "Kanpur, Uttar Pradesh, India" not in selected_locations:
            selected_locations[0] = "Kanpur, Uttar Pradesh, India"
        if "Dubai, United Arab Emirates" not in selected_locations:
            selected_locations[1] = "Dubai, United Arab Emirates"
            
        selected_queries = random.sample(PRIORITY_QUERIES, min(3, len(PRIORITY_QUERIES)))
        # Always include the core "Operations Manager" title
        if ("Operations Manager", 1) not in selected_queries:
            selected_queries[0] = ("Operations Manager", 1)

    new_jobs_found = []
    
    # Process queries
    for query, priority in selected_queries:
        for location in selected_locations:
            results = run_linkedin_search(bun_exec, query, location)
            
            # Process results
            for result in results:
                unique_key = get_job_unique_key(result)
                company = result.get("company", "")
                title = result.get("title", "")
                url = result.get("url", "")
                location_val = result.get("location", location)
                snippet = result.get("snippet", "")
                
                # Skip if seen
                if unique_key in seen_data["seen"]:
                    continue
                
                # Skip if already applied in tracker
                tracker_key = f"{company.strip().lower()}_{title.strip().lower()}"
                if tracker_key in applied_keys:
                    continue
                
                # Calculate fit metrics
                score, fit, geo_tag = calculate_fit_score(title, company, location_val, snippet)
                
                job_entry = {
                    "title": title,
                    "company": company,
                    "url": url,
                    "location": location_val,
                    "score": score,
                    "fit": fit,
                    "geo_tag": geo_tag,
                    "first_seen": datetime.now().strftime("%Y-%m-%d")
                }
                
                # Append to new list
                new_jobs_found.append(job_entry)
                
                # Save to seen database state
                seen_data["seen"][unique_key] = {
                    "title": title,
                    "company": company,
                    "url": url,
                    "first_seen": job_entry["first_seen"],
                    "fit": fit.lower(),
                    "status": "new"
                }
            
            # Delay between sequential calls to respect rate limiting
            delay = random.uniform(5.0, 12.0)
            print(f"Sleeping for {delay:.2f} seconds to protect rate limits...")
            time.sleep(delay)
            
        # Run a Freehire search if in apac / tech
        if not test_mode and priority == 1:
            freehire_results = run_freehire_search(bun_exec, query)
            for result in freehire_results:
                unique_key = get_job_unique_key(result)
                if unique_key in seen_data["seen"]:
                    continue
                
                company = result.get("company", "")
                title = result.get("title", "")
                url = result.get("url", "")
                location_val = result.get("location", "India")
                snippet = result.get("description", "")
                
                score, fit, geo_tag = calculate_fit_score(title, company, location_val, snippet)
                
                job_entry = {
                    "title": title,
                    "company": company,
                    "url": url,
                    "location": location_val,
                    "score": score,
                    "fit": fit,
                    "geo_tag": geo_tag,
                    "first_seen": datetime.now().strftime("%Y-%m-%d")
                }
                new_jobs_found.append(job_entry)
                seen_data["seen"][unique_key] = {
                    "title": title,
                    "company": company,
                    "url": url,
                    "first_seen": job_entry["first_seen"],
                    "fit": fit.lower(),
                    "status": "new"
                }

    # Save state
    save_seen_jobs(seen_data)
    
    # Update visual dashboard
    if new_jobs_found or test_mode or not os.path.exists(DASHBOARD_FILE):
        update_jobs_dashboard(new_jobs_found)
    else:
        print("No new jobs found. Dashboard remains unchanged.")

if __name__ == "__main__":
    main()
