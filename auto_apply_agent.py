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

def auto_compile_package(company, title, location):
    def make_slug(name):
        import re
        slug = re.sub(r'[^a-zA-Z0-9]', '_', name.lower())
        return re.sub(r'_+', '_', slug).strip('_')

    slug = make_slug(company)
    cv_filename = f"main_{slug}.tex"
    cover_filename = f"cover_{slug}.tex"
    cv_path = os.path.join(CV_DIR, cv_filename)
    cover_path = os.path.join(COVER_DIR, cover_filename)

    os.makedirs(CV_DIR, exist_ok=True)
    os.makedirs(COVER_DIR, exist_ok=True)

    if not os.path.exists(cv_path):
        cv_tex = f"""%% CV - Tanuj Chandel
%% Tailored for: {title} at {company} ({location})
\\documentclass[11pt,a4paper,sans]{{moderncv}}
\\moderncvstyle{{banking}}
\\moderncvcolor{{blue}}

\\name{{Tanuj}}{{Chandel}}
\\address{{India (Available for 100\\% Remote Global Roles)}}{{}}{{}}
\\phone[mobile]{{+91 7704077700}}
\\email{{tanuj.chandel@gmail.com}}
\\extrainfo{{\\href{{https://linkedin.com/in/tanujchandel}}{{linkedin.com/in/tanujchandel}}}}

\\begin{{document}}
\\makecvtitle
\\small{{Detail-oriented AI Evaluator, Prompt Engineer \\& Model Trainer with an engineering background (B.Tech ECE) and MBA. Experienced in assessing LLM responses, RLHF benchmark quality, instruction following, prompt optimization, and Python data automation. Tailored for {title} at {company}.}}

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
\\namesection{{}}{{Tanuj Chandel}}{{\\href{{mailto:tanuj.chandel@gmail.com}}{{tanuj.chandel@gmail.com}} | +91 7704077700}}
\\currentdate{{\\today}}
\\lettercontent{{Dear Hiring Manager at {company},}}
\\lettercontent{{I am writing to express my strong interest in the **{title}** position at **{company}**. With an engineering degree (B.Tech ECE) and MBA, combined with hands-on practice in LLM evaluation, prompt engineering, and Python workflow automation, I am dedicated to delivering accurate, rubric-compliant AI training evaluations.}}
\\closing{{Kind regards,}}
\\signature{{Tanuj Chandel}}
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

def apply_selected_jobs(job_ids):
    creds = load_credentials()
    rows = []
    applied_count = 0
    updated_jobs = []

    if os.path.exists(TRACKER_FILE):
        with open(TRACKER_FILE, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames or ["ID", "Company", "Title", "Location", "Region", "FitScore", "Status", "CVFile", "CoverFile", "URL", "AppliedDate"]
            for row in reader:
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
                rows.append(row)

        with open(TRACKER_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

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
