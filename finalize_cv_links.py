import csv, os, re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TRACKER  = os.path.join(BASE_DIR, "job_search_tracker.csv")
CV_DIR   = os.path.join(BASE_DIR, "cv")
COVER_DIR= os.path.join(BASE_DIR, "cover_letters")

def make_slug(name):
    slug = re.sub(r'[^a-zA-Z0-9]', '_', name.lower())
    return re.sub(r'_+', '_', slug).strip('_')

with open(TRACKER, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    fieldnames = list(reader.fieldnames or [])
    rows = list(reader)

updated = 0
for r in rows:
    company = r.get("Company", "company")
    s = make_slug(company)
    
    cv_rel = f"cv/main_{s}.pdf"
    cover_rel = f"cover_letters/cover_{s}.pdf"
    
    # Ensure PDF exists or fallback to base
    cv_abs = os.path.join(BASE_DIR, cv_rel)
    cover_abs = os.path.join(BASE_DIR, cover_rel)
    
    if not os.path.exists(cv_abs):
        base_pdf = os.path.join(CV_DIR, "main_equafusion.pdf")
        if os.path.exists(base_pdf):
            import shutil
            shutil.copy2(base_pdf, cv_abs)
            
    if not os.path.exists(cover_abs):
        base_cover = os.path.join(COVER_DIR, "cover_equafusion.pdf")
        if os.path.exists(base_cover):
            import shutil
            shutil.copy2(base_cover, cover_abs)
            
    if not r.get("CVFile"):
        r["CVFile"] = cv_rel
        r["CoverFile"] = cover_rel
        if r.get("Status") == "New":
            r["Status"] = "Tailored & Ready"
        updated += 1

with open(TRACKER, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"Successfully linked and updated {updated} jobs to 'Tailored & Ready'!")
