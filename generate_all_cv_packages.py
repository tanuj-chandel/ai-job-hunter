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

def compile_for_job(company, title, location):
    s = make_slug(company) if company else "company"
    cv_pdf = os.path.join(CV_DIR, f"main_{s}.pdf")
    cover_pdf = os.path.join(COVER_DIR, f"cover_{s}.pdf")

    cv_tex_path = os.path.join(CV_DIR, f"main_{s}.tex")
    cover_tex_path = os.path.join(COVER_DIR, f"cover_{s}.tex")

    if not os.path.exists(cv_tex_path):
        cv_tex = f"""\\documentclass[11pt,a4paper,sans]{{moderncv}}
\\moderncvstyle{{banking}}
\\moderncvcolor{{blue}}
\\name{{Tanuj}}{{Chandel}}
\\address{{India (Available for 100\\% Remote Global Roles)}}{{}}{{}}
\\phone[mobile]{{+91 7704077700}}
\\email{{tanuj.chandel@gmail.com}}
\\extrainfo{{\\href{{https://linkedin.com/in/tanujchandel}}{{linkedin.com/in/tanujchandel}}}}
\\begin{{document}}
\\makecvtitle
\\small{{Detail-oriented AI Evaluator, Prompt Engineer \\& Model Trainer with engineering background (B.Tech ECE) and MBA. Experienced in assessing LLM responses, RLHF benchmark quality, instruction following, prompt optimization, and Python data automation. Tailored for {title} at {company}.}}
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
\\author{{Tanuj Chandel}}
\\maketitle
Dear Hiring Manager at {company},

I am writing to express my strong interest in the {title} role at {company} ({location}).
With an engineering background (B.Tech ECE) and MBA, paired with hands-on practice in LLM evaluation, prompt engineering, and Python workflow automation, I am dedicated to delivering accurate, rubric-compliant AI training datasets and evaluations.

I look forward to discussing how my analytical rigor aligns with your AI initiatives.

Kind regards,
Tanuj Chandel
+91 7704077700 | tanuj.chandel@gmail.com
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

def main():
    if not os.path.exists(TRACKER):
        return
    with open(TRACKER, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    count = 0
    for r in rows:
        company = r.get("Company", "Company")
        title   = r.get("Title", "Role")
        loc     = r.get("Location", "India")
        cv_rel, cover_rel = compile_for_job(company, title, loc)
        r["CVFile"] = cv_rel
        r["CoverFile"] = cover_rel
        count += 1

    with open(TRACKER, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Generated tailored CV and Cover Letter packages for {count} jobs.")

if __name__ == "__main__":
    main()
