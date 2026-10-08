#!/usr/bin/env python3
"""
Automated Job Application & Package Compilation Agent for Tanuj Chandel.
Processes selected job IDs, verifies candidate credentials, auto-generates & compiles
tailored LaTeX CV/Cover Letter PDFs, updates tracker CSV, and logs application status.
"""

import os
import sys
import json
import csv
import argparse
import subprocess
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_FILE = os.path.join(BASE_DIR, "credentials.env")
TRACKER_FILE = os.path.join(BASE_DIR, "job_search_tracker.csv")
SEEN_JOBS_FILE = os.path.join(BASE_DIR, "job_scraper", "seen_jobs.json")
CV_DIR = os.path.join(BASE_DIR, "cv")
COVER_DIR = os.path.join(BASE_DIR, "cover_letters")

def load_credentials():
    creds = {}
    if os.path.exists(CREDENTIALS_FILE):
        with open(CREDENTIALS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    creds[k.strip()] = v.strip().strip('"').strip("'")
    return creds

from config_loader import get_candidate_info

def auto_compile_package(company, title, location):
    def make_slug(name):
        import re
        slug = re.sub(r'[^a-zA-Z0-9]', '_', name.lower())
        return re.sub(r'_+', '_', slug).strip('_')

    cand = get_candidate_info()
    first_name = cand.get("first_name", "Jane")
    last_name  = cand.get("last_name", "Doe")
    full_name  = cand.get("full_name", f"{first_name} {last_name}")
    address    = cand.get("location", "Remote")
    phone      = cand.get("phone", "")
    email      = cand.get("email", "")
    li_url     = cand.get("linkedin_url", "")
    li_disp    = cand.get("linkedin_display", "")
    bio        = cand.get("bio_summary", "Detail-oriented AI Evaluator & Prompt Engineer.")
    cover_intro= cand.get("cover_letter_intro", "Dedicated to delivering accurate AI training evaluations.")

    slug = make_slug(company)
    cv_filename = f"main_{slug}.tex"
    cover_filename = f"cover_{slug}.tex"
    cv_path = os.path.join(CV_DIR, cv_filename)
    cover_path = os.path.join(COVER_DIR, cover_filename)

    os.makedirs(CV_DIR, exist_ok=True)
    os.makedirs(COVER_DIR, exist_ok=True)

    if not os.path.exists(cv_path):
        cv_tex = f"""%% CV - {full_name}
%% Tailored for: {title} at {company} ({location})
\\documentclass[11pt,a4paper,sans]{{moderncv}}
\\moderncvstyle{{banking}}
\\moderncvcolor{{blue}}

\\name{{{first_name}}}{{{last_name}}}
\\address{{{address}}}{{}}{{}}
\\phone[mobile]{{{phone}}}
\\email{{{email}}}
\\extrainfo{{\\href{{{li_url}}}{{{li_disp}}}}}

\\begin{{document}}
\\makecvtitle
\\small{{{bio} Tailored for {title} at {company}.}}

\\section{{Core Competencies}}
\\begin{{itemize}}
\\item \\textbf{{AI \\& LLM Evaluation}}: RLHF Evaluation, Hallucination Detection, Multi-turn Prompt Testing, Quality Rubrics.
\\item \\textbf{{Prompt Engineering \\& Annotation}}: SFT Data Curation, Edge-case Analysis, Fact Verification, Structured Labeling.
\\item \\textbf{{Technical \\& Analytical Skills}}: Python Automation, Benchmark Analysis, Systematic Quality Auditing.
\\end{{itemize}}
\\end{{document}}
"""
        with open(cv_path, "w", encoding="utf-8") as f:
            f.write(cv_tex)

    if not os.path.exists(cover_path):
        cover_tex = f"""\\documentclass[]{{cover}}
\\begin{{document}}
\\namesection{{}}{{{full_name}}}{{\\href{{mailto:{email}}}{{{email}}} | {phone}}}
\\currentdate{{\\today}}
\\lettercontent{{Dear Hiring Manager at {company},}}
\\lettercontent{{I am writing to express my strong interest in the **{title}** position at **{company}**. {cover_intro}}}
\\closing{{Kind regards,}}
\\signature{{{full_name}}}
\\end{{document}}
"""
        with open(cover_path, "w", encoding="utf-8") as f:
            f.write(cover_tex)

    pdf_cv = os.path.join(CV_DIR, f"main_{slug}.pdf")
    pdf_cover = os.path.join(COVER_DIR, f"cover_{slug}.pdf")

    # Compile PDFs if not already present
    if not os.path.exists(pdf_cv) or not os.path.exists(pdf_cover):
        try:
            subprocess.run(["lualatex", "-interaction=batchmode", f"-output-directory={CV_DIR}", cv_path], capture_output=True, timeout=10)
            subprocess.run(["xelatex", "-interaction=batchmode", f"-output-directory={COVER_DIR}", cover_path], capture_output=True, timeout=10)
        except Exception:
            pass

    cv_res = f"cv/main_{slug}.pdf" if os.path.exists(pdf_cv) else f"cv/{cv_filename}"
    cover_res = f"cover_letters/cover_{slug}.pdf" if os.path.exists(pdf_cover) else f"cover_letters/{cover_filename}"

    return cv_res, cover_res

import tracker_db

def apply_selected_jobs(job_ids):
    creds = load_credentials()
    applied_count = 0
    updated_jobs = []

    rows = tracker_db.get_all_jobs()
    for row in rows:
        jid = str(row.get("ID", ""))
        url = str(row.get("URL", ""))
        if jid in job_ids or url in job_ids or "all" in job_ids:
            company = row.get("Company", "")
            title = row.get("Title", "")
            location = row.get("Location", "")
            
            cv_file, cover_file = auto_compile_package(company, title, location)
            if row.get("Status") != "Real Applied": row["Status"] = "Tailored & Ready"
            row["CVFile"] = cv_file or row.get("CVFile", "")
            row["CoverFile"] = cover_file or row.get("CoverFile", "")
            row["AppliedDate"] = datetime.now().strftime("%Y-%m-%d")
            applied_count += 1
            updated_jobs.append(row)
            if jid:
                tracker_db.update_job(jid, row)

    tracker_db.export_to_csv()

    return {
        "status": "success",
        "applied_count": applied_count,
        "processed_jobs": updated_jobs,
        "credentials_loaded": bool(creds.get("LINKEDIN_EMAIL"))
    }

def main():
    parser = argparse.ArgumentParser(description="Auto Apply Agent")
    parser.add_argument("--jobs", type=str, help="Comma-separated job IDs to apply to")
    args = parser.parse_args()

    job_ids = [j.strip() for j in args.jobs.split(",")] if args.jobs else []
    result = apply_selected_jobs(job_ids)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
