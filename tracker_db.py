"""
SQLite Tracker Database for AI Job Hunter.
Manages tracker.db and provides SQLite persistence with CSV export for dashboard.
"""
import os
import sqlite3
import csv
import argparse
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "tracker.db")
CSV_FILE = os.path.join(BASE_DIR, "job_search_tracker.csv")

FIELDS = [
    "ID", "Company", "Title", "Location", "Region", "FitScore", "Status",
    "CVFile", "CoverFile", "URL", "AppliedDate", "Source",
    "ResponseReceived", "ResponseDate", "InterviewScheduled", "Outcome"
]

def get_connection(db_path=None):
    path = db_path or DB_FILE
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path=None):
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                ID TEXT PRIMARY KEY,
                Company TEXT,
                Title TEXT,
                Location TEXT,
                Region TEXT,
                FitScore INTEGER,
                Status TEXT,
                CVFile TEXT,
                CoverFile TEXT,
                URL TEXT,
                AppliedDate TEXT,
                Source TEXT,
                ResponseReceived TEXT,
                ResponseDate TEXT,
                InterviewScheduled TEXT,
                Outcome TEXT,
                CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UpdatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(Status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_url ON jobs(URL)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs(Company)")
        conn.commit()

def get_all_jobs(db_path=None):
    init_db(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM jobs ORDER BY rowid ASC")
        rows = cursor.fetchall()
        result = []
        for r in rows:
            d = {f: r[f] if r[f] is not None else "" for f in FIELDS}
            result.append(d)
        return result

def get_existing_urls(db_path=None):
    init_db(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT URL FROM jobs WHERE URL IS NOT NULL AND URL != ''")
        return {r["URL"].strip() for r in cursor.fetchall()}

def get_job_by_id(job_id, db_path=None):
    init_db(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM jobs WHERE ID = ?", (job_id,))
        row = cursor.fetchone()
        if row:
            return {f: row[f] if row[f] is not None else "" for f in FIELDS}
        return None

def insert_job(job_dict, db_path=None):
    init_db(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cols = [f for f in FIELDS if f in job_dict]
        placeholders = ", ".join(["?"] * len(cols))
        col_names = ", ".join(cols)
        values = [job_dict.get(c, "") for c in cols]
        sql = f"INSERT OR REPLACE INTO jobs ({col_names}, UpdatedAt) VALUES ({placeholders}, CURRENT_TIMESTAMP)"
        cursor.execute(sql, values)
        conn.commit()

def insert_jobs(jobs_list, db_path=None):
    if not jobs_list:
        return
    init_db(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        for j in jobs_list:
            cols = [f for f in FIELDS if f in j]
            placeholders = ", ".join(["?"] * len(cols))
            col_names = ", ".join(cols)
            values = [j.get(c, "") for c in cols]
            sql = f"INSERT OR REPLACE INTO jobs ({col_names}, UpdatedAt) VALUES ({placeholders}, CURRENT_TIMESTAMP)"
            cursor.execute(sql, values)
        conn.commit()

def update_job(job_id, updates_dict, db_path=None):
    init_db(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        set_clauses = []
        values = []
        for k, v in updates_dict.items():
            if k in FIELDS:
                set_clauses.append(f"{k} = ?")
                values.append(v)
        if not set_clauses:
            return
        set_clauses.append("UpdatedAt = CURRENT_TIMESTAMP")
        values.append(job_id)
        sql = f"UPDATE jobs SET {', '.join(set_clauses)} WHERE ID = ?"
        cursor.execute(sql, values)
        conn.commit()

def update_job_status(job_id, status, cv_path=None, cover_path=None, target_url=None, db_path=None):
    init_db(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        updates = [("Status", status), ("AppliedDate", datetime.now().strftime("%Y-%m-%d"))]
        if cv_path:
            updates.append(("CVFile", os.path.relpath(cv_path, BASE_DIR) if os.path.isabs(cv_path) else cv_path))
        if cover_path:
            updates.append(("CoverFile", os.path.relpath(cover_path, BASE_DIR) if os.path.isabs(cover_path) else cover_path))

        set_sql = ", ".join([f"{k} = ?" for k, _ in updates]) + ", UpdatedAt = CURRENT_TIMESTAMP"
        params = [v for _, v in updates]

        if target_url:
            sql = f"UPDATE jobs SET {set_sql} WHERE ID = ? OR URL = ?"
            params.extend([job_id, target_url])
        else:
            sql = f"UPDATE jobs SET {set_sql} WHERE ID = ?"
            params.append(job_id)

        cursor.execute(sql, params)
        conn.commit()

def export_to_csv(csv_path=None, db_path=None):
    target_csv = csv_path or CSV_FILE
    jobs = get_all_jobs(db_path)
    with open(target_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        for j in jobs:
            writer.writerow({f: j.get(f, "") for f in FIELDS})
    return len(jobs)

def main():
    parser = argparse.ArgumentParser(description="Tracker Database Manager")
    parser.add_argument("--export", action="store_true", help="Export tracker.db to job_search_tracker.csv")
    parser.add_argument("--stats", action="store_true", help="Show tracker statistics")
    args = parser.parse_args()

    if args.export:
        count = export_to_csv()
        print(f"Exported {count} jobs from tracker.db to {CSV_FILE}")
    elif args.stats:
        jobs = get_all_jobs()
        print(f"Total jobs tracked: {len(jobs)}")
        statuses = {}
        for j in jobs:
            s = j.get("Status") or "Unknown"
            statuses[s] = statuses.get(s, 0) + 1
        for s, count in sorted(statuses.items(), key=lambda x: -x[1]):
            print(f"  {s}: {count}")
    else:
        init_db()
        print(f"Database initialized at {DB_FILE}")

if __name__ == "__main__":
    main()
