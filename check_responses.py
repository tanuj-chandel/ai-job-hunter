#!/usr/bin/env python3
"""
Recruiter Response Checker & Tracker Outcome Synchronizer
Uses the Gmail API (strictly read-only scope: https://www.googleapis.com/auth/gmail.readonly)
to scan for recruiter responses, interview invitations, and application updates.

Matching emails are presented to the candidate with an intelligent suggestion.
Upon candidate confirmation, job_search_tracker.csv is updated automatically.
NO emails are ever sent, replied to, or deleted.
"""

import os
import sys
import io
import csv
import re
import argparse
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime

# Force UTF-8 stdout/stderr for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TRACKER_FILE = os.path.join(BASE_DIR, "job_search_tracker.csv")
CREDENTIALS_FILE = os.path.join(BASE_DIR, "credentials.json")
TOKEN_FILE = os.path.join(BASE_DIR, "token.json")

# STRICT READ-ONLY SCOPE: No send, modify, or delete permissions
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

COMMON_SUFFIXES = [
    r'\bpvt\b', r'\bltd\b', r'\binc\b', r'\bcorp\b', r'\bcorporation\b',
    r'\bllc\b', r'\bllp\b', r'\bgmbh\b', r'\btechnologies\b', r'\bsolutions\b',
    r'\bservices\b', r'\bconsulting\b', r'\bco\b', r'\bgroup\b', r'\bteam\b'
]

def clean_company_name(name):
    """Normalize company name to canonical lowercase tokens."""
    if not name:
        return ""
    t = name.lower()
    for suff in COMMON_SUFFIXES:
        t = re.sub(suff, '', t)
    t = re.sub(r'[^a-z0-9\s]', ' ', t)
    return re.sub(r'\s+', ' ', t).strip()

import tracker_db

def load_tracker():
    """Load jobs from tracker_db."""
    rows = tracker_db.get_all_jobs()
    return rows, tracker_db.FIELDS

def save_tracker(rows, fieldnames):
    """Safely write updated rows back to tracker.db and export to CSV."""
    tracker_db.insert_jobs(rows)
    tracker_db.export_to_csv()

def build_company_lookup(tracker_rows):
    """
    Build index of {clean_name: [matching_rows]} for rapid recruiter email matching.
    """
    lookup = {}
    for row in tracker_rows:
        raw_company = row.get("Company", "").strip()
        cleaned = clean_company_name(raw_company)
        if cleaned:
            lookup.setdefault(cleaned, []).append(row)
        # Also store original lower
        orig_lower = raw_company.lower().strip()
        if orig_lower and orig_lower != cleaned:
            lookup.setdefault(orig_lower, []).append(row)
    return lookup

def get_gmail_service():
    """
    Authenticates with Gmail API using OAuth 2.0 (read-only scope).
    Uses token.json if cached, otherwise credentials.json.
    """
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except ImportError as e:
        print(f"[Error] Missing Google API client library: {e}", file=sys.stderr)
        print("Please install via: pip install google-api-python-client google-auth-oauthlib", file=sys.stderr)
        return None

    creds = None
    if os.path.exists(TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        except Exception as e:
            print(f"[Gmail Auth] Error reading {TOKEN_FILE}: {e}", file=sys.stderr)
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                print("[Gmail Auth] Refreshing expired access token...")
                creds.refresh(Request())
            except Exception as e:
                print(f"[Gmail Auth] Token refresh failed: {e}", file=sys.stderr)
                creds = None

        if not creds:
            if not os.path.exists(CREDENTIALS_FILE):
                print("\n" + "=" * 78)
                print(" 🔑 GMAIL API SETUP REQUIRED (One-Time Setup)")
                print("=" * 78)
                print(" To scan your inbox for recruiter responses:")
                print(" 1. Open Google Cloud Console: https://console.cloud.google.com/")
                print(" 2. Create a project (or select an existing one) and enable the 'Gmail API'.")
                print(" 3. Go to 'APIs & Services' > 'Credentials' > 'Create Credentials' > 'OAuth client ID'.")
                print(" 4. Select Application type: 'Desktop app', name it 'AI Job Search', and click Create.")
                print(f" 5. Download the JSON credentials file and save it as:")
                print(f"    {CREDENTIALS_FILE}")
                print(" 6. Re-run: python check_responses.py")
                print("=" * 78 + "\n")
                return None

            print("[Gmail Auth] Launching browser for one-time Google authentication (Read-Only)...")
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        # Cache credentials for subsequent runs
        try:
            with open(TOKEN_FILE, "w", encoding="utf-8") as token_f:
                token_f.write(creds.to_json())
            print(f"[Gmail Auth] Saved authorized token to {os.path.basename(TOKEN_FILE)}")
        except Exception as e:
            print(f"[Gmail Auth] Warning: could not cache token: {e}", file=sys.stderr)

    try:
        service = build('gmail', 'v1', credentials=creds)
        return service
    except Exception as e:
        print(f"[Gmail Auth] Error building Gmail service: {e}", file=sys.stderr)
        return None

def heuristic_classify_email(subject, snippet, body=""):
    """
    Analyzes subject, snippet, and body for outcome predictions:
    Returns (predicted_outcome, is_interview, confidence_reason)
    """
    text = f"{subject} {snippet} {body}".lower()

    # Rejection signatures
    rejection_keywords = [
        "unfortunately", "not moving forward", "other candidates",
        "pursuing other", "regret to inform", "not selected",
        "decided not to proceed", "will not be moving forward",
        "position has been filled", "unable to offer", "not a match at this time"
    ]
    for kw in rejection_keywords:
        if kw in text:
            return "Rejected", "No", f"Matched rejection phrase '{kw}'"

    # Interview signatures
    interview_keywords = [
        "interview", "invitation", "schedule a call", "calendly.com",
        "zoom.us", "meet.google.com", "teams.microsoft.com",
        "speaking with you", "discuss your application", "chat with our team",
        "next round", "shortlisted for", "availability for a call"
    ]
    for kw in interview_keywords:
        if kw in text:
            return "Interview", "Yes", f"Matched interview keyword '{kw}'"

    # Offer signatures
    offer_keywords = [
        "offer letter", "pleased to offer", "job offer", "congratulations on your offer",
        "formal offer"
    ]
    for kw in offer_keywords:
        if kw in text:
            return "Offer", "Yes", f"Matched offer phrase '{kw}'"

    # Assessment signatures
    assessment_keywords = [
        "coding test", "assessment", "hackerrank", "codesignal",
        "take-home", "technical task", "online test"
    ]
    for kw in assessment_keywords:
        if kw in text:
            return "Assessment", "No", f"Matched assessment keyword '{kw}'"

    return "Pending", "No", "General recruiter response / status update"

def find_matching_jobs(sender_name, sender_email, subject, snippet, company_lookup):
    """
    Finds which tracked company matches the given email.
    Returns list of matched job rows.
    """
    clean_sender = clean_company_name(f"{sender_name} {sender_email}")
    domain_match = re.search(r'@([a-zA-Z0-9.\-]+)\.([a-zA-Z]{2,})', sender_email)
    domain_name = domain_match.group(1).lower() if domain_match else ""
    # Strip common email providers (gmail, yahoo, etc.)
    if domain_name in ["gmail", "yahoo", "outlook", "hotmail", "icloud", "mail"]:
        domain_name = ""

    clean_subj = clean_company_name(subject)
    clean_snip = clean_company_name(snippet)

    matched_jobs = []
    seen_ids = set()

    for comp_key, jobs in company_lookup.items():
        if len(comp_key) < 3:
            continue
        # Direct word match against sender or domain
        is_match = False
        if domain_name and domain_name in comp_key:
            is_match = True
        elif comp_key in clean_sender or clean_sender in comp_key:
            is_match = True
        elif comp_key in clean_subj:
            is_match = True
        elif len(comp_key) >= 5 and comp_key in clean_snip:
            is_match = True

        if is_match:
            for job in jobs:
                jid = job.get("ID", "")
                if jid not in seen_ids:
                    seen_ids.add(jid)
                    matched_jobs.append(job)

    return matched_jobs

def parse_email_message(service, msg_id):
    """Fetches and parses a single email message metadata."""
    try:
        msg = service.users().messages().get(userId='me', id=msg_id, format='metadata',
                                             metadataHeaders=['From', 'Subject', 'Date']).execute()
    except Exception as e:
        print(f"[Gmail API] Error fetching message {msg_id}: {e}", file=sys.stderr)
        return None

    headers = {h['name']: h['value'] for h in msg.get('payload', {}).get('headers', [])}
    from_raw = headers.get('From', '')
    subject = headers.get('Subject', '(No Subject)')
    date_raw = headers.get('Date', '')
    snippet = msg.get('snippet', '')

    # Extract sender email and display name
    from_email = ""
    from_name = from_raw
    email_match = re.search(r'<([^>]+)>', from_raw)
    if email_match:
        from_email = email_match.group(1).strip()
        from_name = from_raw.replace(f"<{from_email}>", "").strip().strip('"').strip("'")
    else:
        from_email = from_raw.strip()

    # Parse date to YYYY-MM-DD
    parsed_date = datetime.now().strftime("%Y-%m-%d")
    if date_raw:
        try:
            dt = parsedate_to_datetime(date_raw)
            parsed_date = dt.strftime("%Y-%m-%d")
        except Exception:
            pass

    return {
        "id": msg_id,
        "from_raw": from_raw,
        "from_name": from_name,
        "from_email": from_email,
        "subject": subject,
        "date_str": parsed_date,
        "date_raw": date_raw,
        "snippet": snippet
    }

def scan_inbox(service, company_lookup, days=14, max_emails=50, target_company=None):
    """
    Queries Gmail for recruiter/application emails in the past N days.
    """
    cutoff = datetime.now() - timedelta(days=days)
    after_date = cutoff.strftime("%Y/%m/%d")

    # Build targeted query
    if target_company:
        clean_target = clean_company_name(target_company)
        query = f'after:{after_date} ("{target_company}" OR "{clean_target}")'
    else:
        query = f'after:{after_date} (interview OR application OR offer OR status OR regret OR assessment OR shortlisted OR "thank you for applying" OR candidate OR recruiter)'

    print(f"[Gmail API] Searching messages with query: {query}")
    try:
        results = service.users().messages().list(userId='me', q=query, maxResults=max_emails).execute()
        messages = results.get('messages', [])
    except Exception as e:
        print(f"[Gmail API] Error listing messages: {e}", file=sys.stderr)
        return []

    print(f"[Gmail API] Found {len(messages)} message(s) in date range. Inspecting for tracker matches...\n")
    matches = []

    for idx, m in enumerate(messages, 1):
        parsed = parse_email_message(service, m['id'])
        if not parsed:
            continue

        matched_jobs = find_matching_jobs(
            parsed['from_name'], parsed['from_email'],
            parsed['subject'], parsed['snippet'],
            company_lookup
        )

        if matched_jobs:
            pred_outcome, is_interview, reason = heuristic_classify_email(
                parsed['subject'], parsed['snippet']
            )
            matches.append({
                "email": parsed,
                "jobs": matched_jobs,
                "pred_outcome": pred_outcome,
                "is_interview": is_interview,
                "reason": reason
            })

    return matches

def run_interactive_review(matches, tracker_rows, fieldnames, dry_run=False):
    """
    Presents matched recruiter emails to the candidate and asks for confirmation.
    """
    print("=" * 78)
    print(" 📬 RECRUITER RESPONSE REVIEW & CONFIRMATION PORTAL")
    print("=" * 78)
    print(f" Identified {len(matches)} matching recruiter email(s) across tracked companies.\n")

    updated_count = 0
    tracker_by_id = {r.get("ID"): r for r in tracker_rows}

    for idx, match in enumerate(matches, 1):
        email = match["email"]
        jobs = match["jobs"]
        pred_outcome = match["pred_outcome"]
        is_interview = match["is_interview"]
        reason = match["reason"]

        print("-" * 78)
        print(f"[{idx}/{len(matches)}] MATCH DETECTED:")
        print(f"  From:    {email['from_raw']}")
        print(f"  Date:    {email['date_str']}")
        print(f"  Subject: {email['subject']}")
        print(f"  Snippet: {email['snippet'][:150]}...")
        print(f"  AI Suggestion: {pred_outcome.upper()} ({reason})")
        print("\n  Matched Tracker Opportunity:")
        for j_idx, job in enumerate(jobs):
            current_outcome = job.get('Outcome', '') or 'None'
            current_status = job.get('Status', '')
            print(f"    [{j_idx+1}] {job.get('Title')} @ {job.get('Company')} (ID: {job.get('ID')})")
            print(f"        Current Status: {current_status} | Current Outcome: {current_outcome}")

        # Choose which job to associate if multiple
        target_job = jobs[0]
        if len(jobs) > 1:
            try:
                choice = input(f"  Select job to update [1-{len(jobs)}, 's' to skip]: ").strip()
                if choice.lower() == 's':
                    print("  Skipped.")
                    continue
                sel_idx = int(choice) - 1
                if 0 <= sel_idx < len(jobs):
                    target_job = jobs[sel_idx]
            except Exception:
                target_job = jobs[0]

        # Suggest default key
        default_opt = "1" if pred_outcome == "Interview" else ("2" if pred_outcome == "Rejected" else ("3" if pred_outcome == "Assessment" else ("4" if pred_outcome == "Offer" else "1")))

        print(f"\n  Confirm Outcome to Record for {target_job.get('Company')}:")
        print("    [1] Interview Scheduled (Outcome: Interview, InterviewScheduled: Yes)")
        print("    [2] Rejection (Outcome: Rejected, InterviewScheduled: No)")
        print("    [3] Assessment / Technical Task (Outcome: Assessment, InterviewScheduled: No)")
        print("    [4] Job Offer (Outcome: Offer, InterviewScheduled: Yes)")
        print("    [5] Ignore / False positive (Do not modify tracker)")
        print("    [s] Skip this email")

        prompt_text = f"  Select option [Press ENTER for suggested '{pred_outcome}', or 1-5, s]: "
        try:
            user_opt = input(prompt_text).strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting review.")
            break

        if user_opt.lower() == 's':
            print("  Skipped.")
            continue
        elif user_opt == '5':
            print("  Ignored.")
            continue
        elif not user_opt:
            selected_choice = default_opt
        else:
            selected_choice = user_opt

        # Map choice
        outcome_map = {
            "1": ("Interview", "Yes"),
            "2": ("Rejected", "No"),
            "3": ("Assessment", "No"),
            "4": ("Offer", "Yes"),
        }

        final_outcome, final_interview = outcome_map.get(selected_choice, (pred_outcome, is_interview))

        jid = target_job.get("ID")
        if jid in tracker_by_id:
            row = tracker_by_id[jid]
            row["ResponseReceived"] = "Yes"
            row["ResponseDate"] = email["date_str"]
            row["InterviewScheduled"] = final_interview
            row["Outcome"] = final_outcome

            # Optionally reflect milestone in status column
            if final_outcome == "Interview":
                row["Status"] = "Interview Scheduled"
            elif final_outcome == "Rejected":
                row["Status"] = "Rejected"

            updated_count += 1
            print(f"  ✅ Updated tracker: {target_job.get('Company')} -> Outcome: {final_outcome}, ResponseDate: {email['date_str']}")

    if updated_count > 0 and not dry_run:
        save_tracker(tracker_rows, fieldnames)
        print("\n" + "=" * 78)
        print(f"🎉 Successfully updated {updated_count} application outcome(s) in {os.path.basename(TRACKER_FILE)}!")
        print("=" * 78)
    elif dry_run:
        print("\n[Dry Run] Changes were not written to tracker.")
    else:
        print("\nNo tracker changes made.")

def main():
    parser = argparse.ArgumentParser(description="Scan Gmail for Recruiter Responses and Update Tracker Outcomes")
    parser.add_argument("--days", type=int, default=14, help="Number of past days to scan (default: 14)")
    parser.add_argument("--limit", type=int, default=50, help="Maximum emails to fetch (default: 50)")
    parser.add_argument("--company", type=str, default=None, help="Scan specifically for a single company name")
    parser.add_argument("--dry-run", action="store_true", help="Scan and display matches without writing to tracker")
    args = parser.parse_args()

    tracker_rows, fieldnames = load_tracker()
    if not tracker_rows:
        print("No job records found in tracker to match against.")
        return

    company_lookup = build_company_lookup(tracker_rows)
    print(f"[Tracker] Loaded {len(tracker_rows)} job records across {len(company_lookup)} unique company aliases.")

    service = get_gmail_service()
    if not service:
        return

    matches = scan_inbox(service, company_lookup, days=args.days, max_emails=args.limit, target_company=args.company)
    if not matches:
        print(f"✅ No matching recruiter responses found in the last {args.days} day(s).")
        return

    run_interactive_review(matches, tracker_rows, fieldnames, dry_run=args.dry_run)

if __name__ == "__main__":
    main()
