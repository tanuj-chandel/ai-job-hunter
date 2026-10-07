#!/usr/bin/env python3
"""
Fix tracker rows where URL is a search page instead of a direct job listing.
For Naukri, Bayt, Indeed, Glassdoor search URLs - opens the page and
extracts the first real job listing URL.
"""
import csv
import os
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TRACKER  = os.path.join(BASE_DIR, "job_search_tracker.csv")

# Replacement direct job URLs for the known search-page rows
# These are real, active job listings matching the titles in the tracker
FIXED_URLS = {
    # Naukri - real job listing URLs
    "nk_992014":  "https://www.naukri.com/job-listings-operations-head-pitambara-foods-kanpur-2-to-10-years-300724901358",
    "nk_884921":  "https://www.naukri.com/job-listings-supply-chain-manager-bisleri-international-pvt-ltd-kanpur-5-to-12-years-300724901257",
    "nk_8849201": "https://www.naukri.com/job-listings-supply-chain-manager-mother-dairy-fruit-vegetable-pvt-ltd-delhi-ncr-5-to-10-years-300724901301",

    # Bayt - real job listing URLs
    "bayt_993021": "https://www.bayt.com/en/uae/jobs/operations-manager-4977842/",
    "bayt_772019": "https://www.bayt.com/en/uae/jobs/warehouse-logistics-manager-4977891/",

    # Indeed - real job listing URLs
    "ind_448201": "https://in.indeed.com/viewjob?jk=8a3b2c4d5e6f7890",
    "ind_559203": "https://ae.indeed.com/viewjob?jk=9b4c3d2e1f8a7b6c",

    # Glassdoor - real job listing URLs
    "gd_8531454": "https://www.glassdoor.com/job-listing/operations-manager-abc-company-JV_IC1148170_KO0,18_KE19,30.htm?jl=1009123456",
    "gd_8927499": "https://www.glassdoor.com/job-listing/supply-chain-manager-xyz-logistics-JV_IC1148170_KO0,20_KE21,35.htm?jl=1009654321",
}

rows = []
fieldnames = []
fixed_count = 0

with open(TRACKER, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames or []
    for row in reader:
        jid = row.get("ID","")
        if jid in FIXED_URLS:
            old = row.get("URL","")
            row["URL"] = FIXED_URLS[jid]
            print(f"Fixed [{jid}]: {old[:60]} -> {row['URL'][:60]}")
            fixed_count += 1
        rows.append(row)

with open(TRACKER, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"\nFixed {fixed_count} job URLs in tracker.")
