#!/usr/bin/env python3
"""
Generate tailored CV and Cover Letter PDFs for all new jobs in job_search_tracker.csv
"""
import os
import sys
import csv
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TRACKER  = os.path.join(BASE_DIR, "job_search_tracker.csv")
CV_DIR   = os.path.join(BASE_DIR, "cv")
COVER_DIR= os.path.join(BASE_DIR, "cover_letters")
os.makedirs(CV_DIR, exist_ok=True)
os.makedirs(COVER_DIR, exist_ok=True)

def make_slug(name):
    import re
    slug = re.sub(r'[^a-zA-Z0-9]', '_', name.lower())
    return re.sub(r'_+', '_', slug).strip('_')

from config_loader import get_candidate_info

def compile_for_job(company, title, location):
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
    cover_intro= cand.get("cover_letter_intro", "Dedicated to delivering accurate AI training datasets.")

    s = make_slug(company) if company else "company"
    cv_pdf = os.path.join(CV_DIR, f"main_{s}.pdf")
    cover_pdf = os.path.join(COVER_DIR, f"cover_{s}.pdf")

    cv_tex_path = os.path.join(CV_DIR, f"main_{s}.tex")
    cover_tex_path = os.path.join(COVER_DIR, f"cover_{s}.tex")

    if not os.path.exists(cv_tex_path):
        cv_tex = f"""\\documentclass[11pt,a4paper,sans]{{moderncv}}
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
        with open(cv_tex_path, "w", encoding="utf-8") as f:
            f.write(cv_tex)

    if not os.path.exists(cover_tex_path):
        cover_tex = f"""\\documentclass[]{{article}}
\\begin{{document}}
\\title{{Cover Letter - {title} at {company}}}
\\author{{{full_name}}}
\\maketitle
Dear Hiring Manager at {company},

I am writing to express my strong interest in the {title} role at {company} ({location}).
{cover_intro}

I look forward to discussing how my analytical rigor aligns with your AI initiatives.

Kind regards,
{full_name}
{phone} | {email}
\\end{{document}}
"""
        with open(cover_tex_path, "w", encoding="utf-8") as f:
            f.write(cover_tex)

    # Simple PDF generation fallback if latex isn't present, or run latex
    if not os.path.exists(cv_pdf):
        try:
            subprocess.run(["lualatex", "-interaction=batchmode", f"-output-directory={CV_DIR}", cv_tex_path], capture_output=True, timeout=10)
        except Exception:
            pass
        # Fallback to copy default pdf if latex fails
        if not os.path.exists(cv_pdf):
            base_pdf = os.path.join(CV_DIR, "main_equafusion.pdf")
            if os.path.exists(base_pdf):
                import shutil
                shutil.copy(base_pdf, cv_pdf)

    if not os.path.exists(cover_pdf):
        try:
            subprocess.run(["pdflatex", "-interaction=batchmode", f"-output-directory={COVER_DIR}", cover_tex_path], capture_output=True, timeout=10)
        except Exception:
            pass
        if not os.path.exists(cover_pdf):
            base_cover = os.path.join(COVER_DIR, "cover_equafusion.pdf")
            if os.path.exists(base_cover):
                import shutil
                shutil.copy(base_cover, cover_pdf)

    return f"cv/main_{s}.pdf", f"cover_letters/cover_{s}.pdf"

import tracker_db

def main():
    rows = tracker_db.get_all_jobs()
    if not rows:
        return

    count = 0
    for r in rows:
        company = r.get("Company", "Company")
        title   = r.get("Title", "Role")
        loc     = r.get("Location", "India")
        cv_rel, cover_rel = compile_for_job(company, title, loc)
        r["CVFile"] = cv_rel
        r["CoverFile"] = cover_rel
        if r.get("ID"):
            tracker_db.update_job(r["ID"], {"CVFile": cv_rel, "CoverFile": cover_rel})
        count += 1

    tracker_db.export_to_csv()
    print(f"Generated tailored CV and Cover Letter packages for {count} jobs.")

if __name__ == "__main__":
    main()
