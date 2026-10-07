#!/usr/bin/env python3
"""
Review Screening Questions CLI & Web UI for Tanuj Chandel.
Allows reviewing questions from pending_review_questions.csv, confirming or editing answers,
and triggering browser_apply_agent.py to resume the application.
"""

import os
import sys
import io
import csv
import argparse
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
from datetime import datetime

import screening_manager as sm

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_pending_questions():
    sm.init_csv()
    pending = []
    with open(sm.PENDING_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            if r.get("Status") == "Pending":
                pending.append(r)
    return pending

def run_cli():
    print("=" * 75)
    print(" 📋 SCREENING QUESTION REVIEW & APPROVAL PORTAL")
    print("=" * 75)

    pending = get_pending_questions()
    if not pending:
        print("\n✅ No pending screening questions! All applications are clear or completed.\n")
        return

    print(f"\nFound {len(pending)} pending question(s) awaiting your input:\n")

    answered_jobs = set()

    for idx, q in enumerate(pending):
        qid = q["QuestionID"]
        job_id = q["JobID"]
        company = q["Company"]
        title = q["Title"]
        q_text = q["QuestionText"]
        q_type = q.get("QuestionType", "text")
        options = q.get("Options", "")
        suggested = q.get("SuggestedAnswer", "")

        # If empty in row, check cache live
        if not suggested:
            suggested = sm.get_cached_suggestion(q_text)

        print("-" * 75)
        print(f"[{idx+1}/{len(pending)}] Job: {title} @ {company} (ID: {job_id})")
        print(f"❓ Question ({q_type.upper()}): {q_text}")
        if options:
            print(f"   Options available: {options}")

        if suggested:
            print(f"\n💡 Suggested Answer (from your prior response):")
            print(f"   \"{suggested}\"")
            prompt_str = f"   Enter your answer [Press ENTER to accept suggestion, 's' to skip, 'q' to quit]: "
        else:
            prompt_str = f"   Enter your answer ['s' to skip, 'q' to quit]: "

        try:
            user_input = input(prompt_str).strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting review.")
            break

        if user_input.lower() == 'q':
            print("Stopping review.")
            break
        elif user_input.lower() == 's':
            print("Skipped.")
            continue
        elif not user_input and suggested:
            # Accepted suggestion
            final_ans = suggested
        elif user_input:
            final_ans = user_input
        else:
            print("No answer entered. Skipping.")
            continue

        sm.record_answer(qid, final_ans)
        answered_jobs.add(job_id)
        print(f"✅ Saved answer for {company}!")

    if answered_jobs:
        print("\n" + "=" * 75)
        print(f"🎉 Answered questions for {len(answered_jobs)} job(s)!")
        resume_choice = input(f"Would you like to resume and apply to these {len(answered_jobs)} job(s) now in visible browser? (y/n): ").strip().lower()
        if resume_choice == 'y':
            for jid in answered_jobs:
                print(f"\n[Resuming] Launching browser_apply_agent for Job: {jid}...")
                cmd = [sys.executable, os.path.join(BASE_DIR, "browser_apply_agent.py"), "--jobs", jid, "--visible"]
                subprocess.run(cmd)

def get_answered_jobs():
    sm.init_csv()
    jobs = {}
    with open(sm.PENDING_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            jid = r.get("JobID")
            if jid:
                jobs.setdefault(jid, {"company": r.get("Company", ""), "title": r.get("Title", ""), "pending": 0, "answered": 0})
                if r.get("Status") == "Pending":
                    jobs[jid]["pending"] += 1
                elif r.get("Status") == "Answered":
                    jobs[jid]["answered"] += 1
    ready = [jid for jid, info in jobs.items() if info["pending"] == 0 and info["answered"] > 0]
    return ready, jobs

class WebReviewHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        pending = get_pending_questions()
        ready_jobs, all_jobs_info = get_answered_jobs()
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Screening Questions Review</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 24px; }}
        .container {{ max-width: 850px; margin: 0 auto; }}
        h1 {{ color: #38bdf8; font-size: 24px; margin-bottom: 8px; }}
        .subtitle {{ color: #94a3b8; margin-bottom: 24px; font-size: 14px; }}
        .card {{ background: #1e293b; border-radius: 12px; padding: 20px; margin-bottom: 20px; border: 1px solid #334155; }}
        .resume-card {{ background: #064e3b; border: 1px solid #059669; border-radius: 12px; padding: 18px 24px; margin-bottom: 24px; display: flex; justify-content: space-between; align-items: center; }}
        .job-header {{ display: flex; justify-content: space-between; margin-bottom: 12px; font-size: 14px; color: #38bdf8; }}
        .q-text {{ font-size: 16px; font-weight: 600; color: #f1f5f9; margin-bottom: 12px; }}
        .options {{ font-size: 13px; color: #cbd5e1; margin-bottom: 12px; background: #0f172a; padding: 8px 12px; border-radius: 6px; }}
        .suggested {{ font-size: 13px; color: #34d399; margin-bottom: 12px; }}
        input[type="text"], textarea {{ width: 100%; box-sizing: border-box; background: #0f172a; border: 1px solid #475569; color: #f8fafc; border-radius: 8px; padding: 10px; font-size: 14px; }}
        button {{ background: #2563eb; color: #ffffff; border: none; border-radius: 8px; padding: 10px 20px; font-weight: 600; cursor: pointer; margin-top: 10px; }}
        button:hover {{ background: #1d4ed8; }}
        .btn-success {{ background: #10b981; margin-top: 0; }}
        .btn-success:hover {{ background: #059669; }}
        .empty {{ text-align: center; padding: 60px 20px; color: #94a3b8; font-size: 18px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📋 Screening Question Review & Approval</h1>
        <div class="subtitle">Review pending questions from job application forms. Answers are saved and cached for future suggestions.</div>
"""
        if ready_jobs:
            target_ids = ",".join(ready_jobs)
            html += f"""
        <div class="resume-card">
            <div>
                <strong style="color: #6ee7b7; font-size: 16px;">Ready to Resume ({len(ready_jobs)} Application(s))</strong>
                <div style="color: #a7f3d0; font-size: 13px; margin-top: 4px;">Answers approved for: {', '.join([all_jobs_info[jid]['company'] for jid in ready_jobs])}</div>
            </div>
            <form method="POST" action="/resume" style="margin: 0;">
                <input type="hidden" name="job_ids" value="{target_ids}">
                <button type="submit" class="btn-success">▶ Resume in Browser</button>
            </form>
        </div>"""

        if not pending:
            html += """<div class="empty">🎉 All caught up! No pending screening questions require your review.</div>"""
        else:
            for q in pending:
                qid = q["QuestionID"]
                sug = q.get("SuggestedAnswer") or sm.get_cached_suggestion(q["QuestionText"])
                html += f"""
        <div class="card">
            <div class="job-header">
                <strong>{q['Company']}</strong>
                <span>ID: {q['JobID']}</span>
            </div>
            <div class="q-text">{q['QuestionText']}</div>
            {f'<div class="options">Options: {q["Options"]}</div>' if q.get("Options") else ''}
            {f'<div class="suggested">💡 Prior Answer Found: <em>"{sug}"</em></div>' if sug else ''}
            <form method="POST" action="/save">
                <input type="hidden" name="qid" value="{qid}">
                <input type="text" name="answer" value="{sug}" placeholder="Type your honest answer here..." required>
                <button type="submit">Approve & Save Answer</button>
            </form>
        </div>"""
        html += """
    </div>
</body>
</html>"""
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8')
        params = urllib.parse.parse_qs(body)

        if self.path == "/save":
            qid = params.get("qid", [""])[0]
            answer = params.get("answer", [""])[0]
            if qid and answer:
                sm.record_answer(qid, answer)
            self.send_response(303)
            self.send_header("Location", "/")
            self.end_headers()
        elif self.path == "/resume":
            job_ids = params.get("job_ids", [""])[0]
            if job_ids:
                cmd = [sys.executable, os.path.join(BASE_DIR, "browser_apply_agent.py"), "--jobs", job_ids, "--visible"]
                subprocess.Popen(cmd)
            self.send_response(303)
            self.send_header("Location", "/")
            self.end_headers()

def run_web(port=8085):
    server = HTTPServer(('127.0.0.1', port), WebReviewHandler)
    print(f"\n🌐 Web Review UI running on: http://localhost:{port}/")
    print("Press Ctrl+C to stop.\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nWeb server stopped.")

def main():
    parser = argparse.ArgumentParser(description="Review and Answer Job Screening Questions")
    parser.add_argument("--web", action="store_true", help="Launch simple local browser UI on http://localhost:8085")
    parser.add_argument("--port", type=int, default=8085, help="Port for web review UI")
    args = parser.parse_args()

    if args.web:
        run_web(args.port)
    else:
        run_cli()

if __name__ == "__main__":
    main()
