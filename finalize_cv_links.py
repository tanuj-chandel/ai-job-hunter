import os, re, shutil
import tracker_db

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CV_DIR   = os.path.join(BASE_DIR, "cv")
COVER_DIR= os.path.join(BASE_DIR, "cover_letters")

def make_slug(name):
    slug = re.sub(r'[^a-zA-Z0-9]', '_', name.lower())
    return re.sub(r'_+', '_', slug).strip('_')

rows = tracker_db.get_all_jobs()
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
            shutil.copy2(base_pdf, cv_abs)

    if not os.path.exists(cover_abs):
        base_cover = os.path.join(COVER_DIR, "cover_equafusion.pdf")
        if os.path.exists(base_cover):
            shutil.copy2(base_cover, cover_abs)

    if not r.get("CVFile"):
        r["CVFile"] = cv_rel
        r["CoverFile"] = cover_rel
        if r.get("Status") == "New":
            r["Status"] = "Tailored & Ready"
        if r.get("ID"):
            tracker_db.update_job(r["ID"], r)
        updated += 1

tracker_db.export_to_csv()
print(f"Successfully linked and updated {updated} jobs to 'Tailored & Ready'!")
