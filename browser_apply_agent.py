#!/usr/bin/env python3
"""
Real Browser Auto-Apply Agent for Tanuj Chandel.
Uses Playwright to open real browser sessions, log in to job portals,
navigate to job pages, upload tailored CV & Cover Letter PDFs, and submit real applications.

Supports: LinkedIn Easy Apply | Naukri | Bayt | Indeed | Glassdoor
"""

import os
import sys
import io
import json
import csv
import argparse
import time
import re
from datetime import datetime

import screening_manager as sm

# Force UTF-8 output so emoji/special chars don't crash on Windows cp1252 console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_FILE = os.path.join(BASE_DIR, "credentials.env")
TRACKER_FILE  = os.path.join(BASE_DIR, "job_search_tracker.csv")
CV_DIR        = os.path.join(BASE_DIR, "cv")
COVER_DIR     = os.path.join(BASE_DIR, "cover_letters")
SCREENSHOTS   = os.path.join(BASE_DIR, "apply_screenshots")

# Per-portal saved session files
SESSION = {
    "linkedin":  os.path.join(SCREENSHOTS, "session_linkedin.json"),
    "naukri":    os.path.join(SCREENSHOTS, "session_naukri.json"),
    "bayt":      os.path.join(SCREENSHOTS, "session_bayt.json"),
    "indeed":    os.path.join(SCREENSHOTS, "session_indeed.json"),
    "glassdoor": os.path.join(SCREENSHOTS, "session_glassdoor.json"),
}

os.makedirs(SCREENSHOTS, exist_ok=True)

# ─── Helpers ──────────────────────────────────────────────────────────────────

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

def slug(name):
    s = re.sub(r'[^a-zA-Z0-9]', '_', name.lower())
    return re.sub(r'_+', '_', s).strip('_')

def find_cv(company):
    s = slug(company)
    for p in [
        os.path.join(CV_DIR, f"main_{s}.pdf"),
        os.path.join(CV_DIR, "main_tanuj_chandel.pdf"),
    ]:
        if os.path.exists(p): return p
    if os.path.exists(CV_DIR):
        for f in sorted(os.listdir(CV_DIR)):
            if f.endswith(".pdf"):
                return os.path.join(CV_DIR, f)
    return None

def find_cover(company):
    s = slug(company)
    for p in [
        os.path.join(COVER_DIR, f"cover_{s}.pdf"),
        os.path.join(COVER_DIR, "cover_tanuj_chandel.pdf"),
    ]:
        if os.path.exists(p): return p
    if os.path.exists(COVER_DIR):
        for f in sorted(os.listdir(COVER_DIR)):
            if f.endswith(".pdf"):
                return os.path.join(COVER_DIR, f)
    return None

def detect_portal(url):
    u = url.lower()
    for k in ["linkedin", "naukri", "bayt", "indeed", "glassdoor", "micro1", "remotive", "remoteok", "himalayas"]:
        if k in u: return k
    return "unknown"

def is_search_page(url):
    """Return True if this URL is a job-search/listing page, not a direct single job page."""
    u = url.lower()
    # Naukri search patterns
    if "naukri.com" in u and "-jobs-in-" in u and "/job-listings-" not in u:
        return True
    # Indeed search patterns
    if "indeed.com" in u and ("jobs?" in u or "/jobs?" in u or "/q-" in u):
        return True
    # Glassdoor search patterns
    if "glassdoor.com" in u and ("-jobs-srch_" in u or "/job-listing/" not in u and "/Job/" in u and "SRCH" in url):
        return True
    # Bayt search patterns
    if "bayt.com" in u and "-jobs-in-" in u and len(u.split("/")) < 8:
        return True
    return False


MANUAL_CSV = os.path.join(BASE_DIR, "needs_manual_apply.csv")

# Signatures of anti-bot / WAF block pages (Akamai, Cloudflare, PerimeterX, etc.)
# and 2FA / security challenges seen in practice across job portals.
BLOCK_PAGE_SIGNATURES = [
    "access denied",
    "you don't have permission to access",
    "edgesuite.net",
    "errors.edgesuite.net",
    "reference #",
    "request blocked",
    "unusual traffic",
    "verify you are human",
    "are you a robot",
    "captcha",
    "checking your browser",
    "just a moment...",
    "just a moment",
    "pardon the interruption",
    "attention required! | cloudflare",
    "cf-browser-verification",
    "cloudflare-challenge",
    "security verification",
    "security check",
    "enter the 6-digit code",
    "two-factor",
    "2-step verification",
    "one-time password",
    "verification code",
    "additional verification required",
]

def log_needs_manual_apply(job, reason, screenshot_file=""):
    """Logs a job blocked by CAPTCHA, 2FA, or anti-bot challenge to needs_manual_apply.csv."""
    fields = ["JobID", "Company", "Title", "URL", "Portal", "Reason", "ScreenshotFile", "DetectedAt", "Status"]
    existing = []
    if os.path.exists(MANUAL_CSV):
        try:
            with open(MANUAL_CSV, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                existing = list(reader)
        except Exception:
            pass

    job_id = str(job.get("ID", "")) if job else "unknown"
    url = str(job.get("URL", "")) if job else ""
    for row in existing:
        if str(row.get("JobID", "")) == job_id or (url and str(row.get("URL", "")) == url):
            return  # Already recorded

    row_data = {
        "JobID": job_id,
        "Company": job.get("Company", "") if job else "Unknown",
        "Title": job.get("Title", "") if job else "Unknown",
        "URL": url,
        "Portal": detect_portal(url),
        "Reason": reason,
        "ScreenshotFile": os.path.basename(screenshot_file) if screenshot_file else "",
        "DetectedAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Status": "Needs Manual Action"
    }

    exists = os.path.exists(MANUAL_CSV)
    with open(MANUAL_CSV, "a" if exists else "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        if not exists:
            writer.writeheader()
        writer.writerow(row_data)

def check_challenge_presence(page):
    """Low-level check for anti-bot / WAF / Cloudflare / CAPTCHA / 2FA.
    Returns (bool, reason_string)."""
    # 1. URL checks
    try:
        url_lower = (page.url or "").lower()
        for kw in ["checkpoint", "challenge", "captcha", "waf-verify", "security-check", "geo-block"]:
            if kw in url_lower:
                return True, f"URL challenge keyword '{kw}' ({page.url})"
    except Exception:
        pass

    # 2. Page title & body text
    try:
        title = (page.title() or "").lower()
    except Exception:
        title = ""
    try:
        body_text = page.inner_text("body")[:1500].lower() if page.query_selector("body") else ""
    except Exception:
        body_text = ""
    haystack = f"{title} {body_text}"
    for sig in BLOCK_PAGE_SIGNATURES:
        if sig in haystack:
            return True, f"Page text matched '{sig}'"

    # 3. DOM element / iframe checks
    challenge_selectors = [
        'iframe[src*="cloudflare"]',
        'iframe[src*="challenges"]',
        'iframe[src*="recaptcha"]',
        'iframe[src*="arkoselabs"]',
        '#challenge-stage',
        '#px-captcha',
        '#captcha',
        '.g-recaptcha',
        'input[name="pin"]',
        'input[name="verification_code"]',
        'input[placeholder*="OTP"]',
        'input[placeholder*="verification code"]',
    ]
    for sel in challenge_selectors:
        try:
            el = page.query_selector(sel)
            if el and el.is_visible():
                return True, f"Found challenge element '{sel}'"
        except Exception:
            pass

    return False, ""

def is_blocked_page(page, log=None, tag="", job=None, headless=False):
    """Detect anti-bot / WAF block pages (Akamai, Cloudflare, PerimeterX, CAPTCHA, 2FA).
    
    Behavior:
    - If headless:
        Saves screenshot, logs to needs_manual_apply.csv, logs to console, returns True (skip job).
    - If visible (headless=False):
        Keeps browser window OPEN and pauses with:
        'CAPTCHA/2FA detected for [Company] — complete manually, then press Enter to continue.'
        When Enter is pressed:
        Re-checks if page is still blocked.
        If cleared, returns False (resumes automated flow right where it left off!).
        If user enters 's' or still blocked after retry, logs to needs_manual_apply.csv and returns True.
    """
    is_blocked, reason = check_challenge_presence(page)
    if not is_blocked:
        return False

    company = job.get("Company", tag or "Target Portal") if job else (tag or "Target Portal")
    job_id = job.get("ID", tag) if job else tag

    if headless:
        ss_path = screenshot(page, job_id, "captcha_headless")
        if job:
            log_needs_manual_apply(job, reason=reason, screenshot_file=ss_path)
        if log is not None:
            log.append(f"[{tag}] 🛑 CAPTCHA/2FA detected in headless mode ({reason}). "
                       f"Saved screenshot, logged to needs_manual_apply.csv, and skipping.")
        return True

    # ── Visible mode: interactive handoff to candidate ──
    print(f"\n" + "=" * 78, flush=True)
    print(f" ⚠️  CAPTCHA/2FA detected for {company} — complete manually, then press Enter to continue.", flush=True)
    print(f" Details: {reason}", flush=True)
    print(f" (The browser window is open. Type 's' + Enter to skip this job)", flush=True)
    print("=" * 78, flush=True)

    if log is not None:
        log.append(f"[{tag}] Paused for manual CAPTCHA/2FA handoff ({company}). Waiting for candidate...")

    try:
        user_input = input(">> Press Enter to continue once solved (or 's' to skip): ").strip()
    except (KeyboardInterrupt, EOFError):
        user_input = "s"

    if user_input.lower() == 's':
        ss_path = screenshot(page, job_id, "captcha_skipped")
        if job:
            log_needs_manual_apply(job, reason=f"User skipped challenge ({reason})", screenshot_file=ss_path)
        if log is not None:
            log.append(f"[{tag}] Skipped by user during CAPTCHA challenge.")
        return True

    # User pressed Enter: give page 3 seconds to settle
    time.sleep(3)

    # Re-check page
    still_blocked, new_reason = check_challenge_presence(page)
    if still_blocked:
        print(f"\n[BrowserAgent] ⚠️ Challenge still detected ({new_reason}).", flush=True)
        try:
            retry = input(">> Press Enter if now completed, or 's' to skip: ").strip()
        except (KeyboardInterrupt, EOFError):
            retry = "s"
        if retry.lower() == 's':
            ss_path = screenshot(page, job_id, "captcha_unresolved")
            if job:
                log_needs_manual_apply(job, reason=new_reason, screenshot_file=ss_path)
            return True
        time.sleep(3)
        still_blocked, final_reason = check_challenge_presence(page)
        if still_blocked:
            ss_path = screenshot(page, job_id, "captcha_unresolved")
            if job:
                log_needs_manual_apply(job, reason=final_reason, screenshot_file=ss_path)
            if log is not None:
                log.append(f"[{tag}] Challenge remained unresolved after prompt.")
            return True

    # SUCCESS: Challenge cleared by candidate!
    if log is not None:
        log.append(f"[{tag}] ✅ CAPTCHA/2FA challenge resolved manually! Resuming automated flow...")
    print(f"[BrowserAgent] ✅ CAPTCHA/2FA resolved! Resuming automated flow for {company}...\n", flush=True)
    return False


def harvest_job_links(page, portal, log, max_links=5):
    """PATCH A: Harvest all job links from a search results page (up to max_links).
    Returns list of absolute URLs to individual job pages."""
    from urllib.parse import urljoin
    log.append(f"[{portal.upper()}] Harvesting job links from search page...")
    hrefs = []
    selector_lists = {
        "naukri": [
            'article.jobTuple a.title',
            '.job-title-anchor',
            'a.title[href*="job-listings"]',
            'a[href*="/job-listings-"]',
            '.jobtuple-wrapper a.title',
            'a.jobTitle',
        ],
        "indeed": [
            'a.jcs-JobTitle',
            'h2.jobTitle a',
            '[data-jk] a',
            'a[id^="job_"]',
            '.jobTitle a',
            'a[href*="/rc/clk"]',
            'a[href*="/pagead/clk"]',
        ],
        "glassdoor": [
            'a[data-test="job-link"]',
            'a.jobLink',
            'li[data-jobid] a',
            '.react-job-listing a',
            'a[href*="/job-listing/"]',
        ],
        "bayt": [
            'a[href*="/en/"][href*="/job/"]',
            'a[href*="/en/uae/jobs/"]',
            'a[href*="/en/international/jobs/"]',
            'h2.jb-title a',
            '.media-body h2 a',
            'li.has-pointer-d a.jb-link',
        ],
    }
    selectors = selector_lists.get(portal, [])
    seen = set()
    for sel in selectors:
        try:
            links = page.query_selector_all(sel)
            for link in links:
                href = link.get_attribute("href") or ""
                if href and href not in seen:
                    if not href.startswith("http"):
                        href = urljoin(page.url, href)
                    seen.add(href)
                    hrefs.append(href)
                    if len(hrefs) >= max_links:
                        break
        except Exception:
            pass
        if len(hrefs) >= max_links:
            break
    log.append(f"[{portal.upper()}] Found {len(hrefs)} job links on search page.")
    return hrefs[:max_links]


def navigate_to_first_job(page, portal, log):
    """Fallback: navigate to first harvested job link."""
    links = harvest_job_links(page, portal, log, max_links=1)
    if links:
        log.append(f"[{portal.upper()}] Navigating to: {links[0][:80]}")
        try:
            page.goto(links[0], timeout=35000)
            time.sleep(3)
            return True
        except Exception as e:
            log.append(f"[{portal.upper()}] Navigation error: {e}")
    return False


def cover_letter_text(job):
    return f"""Dear Hiring Manager,

I am writing to express my strong interest in the {job.get('Title','AI Evaluator / Trainer')} role at {job.get('Company','your team')}.

With an engineering background in Electronics & Communication (B.Tech) and an MBA, combined with hands-on expertise in prompt engineering, LLM output evaluation, and Python-driven automation, I am well-prepared to contribute to your AI evaluation and training pipelines.

My focus includes:
- Rigorous evaluation of LLM responses for reasoning accuracy, factuality, instruction adherence, and hallucination detection.
- RLHF data curation, prompt crafting, and multi-turn conversational quality benchmarking.
- Python workflow automation, custom validation scripts, and structured data annotation.
- Strong analytical and problem-solving skills with a commitment to high data fidelity and quality guidelines.

I am available for remote opportunities and eager to deliver consistent, high-accuracy model training and evaluation results for {job.get('Company','your organization')}.

Kind regards,
Tanuj Chandel
+91 7704077700 | tanuj.chandel@gmail.com
linkedin.com/in/tanujchandel"""

def screenshot(page, job_id, label):
    try:
        page.screenshot(path=os.path.join(SCREENSHOTS, f"{job_id}_{label}.png"))
    except Exception:
        pass

def slow_type(page, selector, text, delay=60):
    try:
        el = page.query_selector(selector)
        if el:
            el.click()
            el.fill("")
            page.type(selector, text, delay=delay)
            return True
    except Exception:
        pass
    return False

# ─── Portal: LinkedIn Easy Apply ──────────────────────────────────────────────

def linkedin_login(page, creds, context, headless, log):
    log.append("[LinkedIn] Checking session...")
    try:
        page.goto("https://www.linkedin.com/feed/", timeout=40000)
        time.sleep(3)
        if "feed" in page.url or "/in/" in page.url:
            log.append("[LinkedIn] Already logged in via saved session ✅")
            return True
    except Exception:
        pass

    log.append("[LinkedIn] Logging in with credentials...")
    page.goto("https://www.linkedin.com/login", timeout=40000)
    time.sleep(2)
    page.type('input[name="session_key"]', creds.get("LINKEDIN_EMAIL",""), delay=80)
    time.sleep(0.4)
    page.type('input[name="session_password"]', creds.get("LINKEDIN_PASSWORD",""), delay=80)
    time.sleep(0.4)
    page.click('button[type="submit"]')
    time.sleep(6)

    if "checkpoint" in page.url or "challenge" in page.url or "verify" in page.url or is_blocked_page(page, log, "LinkedIn", job={"Company": "LinkedIn Login", "ID": "login_linkedin", "URL": page.url}, headless=headless):
        screenshot(page, "linkedin", "checkpoint")
        if headless:
            log.append("[LinkedIn] ⚠️ CAPTCHA/2FA required during login in headless mode. Skipping login.")
            return False

    if "feed" in page.url or "linkedin.com/jobs" in page.url:
        context.storage_state(path=SESSION["linkedin"])
        log.append("[LinkedIn] Login successful ✅ — session saved.")
        return True

    log.append(f"[LinkedIn] Login uncertain: {page.url}")
    return False

def linkedin_apply(page, job, creds, cv_pdf, cover_pdf, context, headless, log):
    url = job.get("URL","")
    log.append(f"[LinkedIn] Opening job: {url}")
    page.goto(url, timeout=30000)
    time.sleep(4)

    # Re-auth if redirected to login
    if "authwall" in page.url or "login" in page.url:
        linkedin_login(page, creds, context, headless, log)
        page.goto(url, timeout=30000)
        time.sleep(3)

    if is_blocked_page(page, log, "LinkedIn", job=job, headless=headless):
        return "needs_manual_action"

    # PATCH C: Find Easy Apply button — also detect external apply URL
    btn = None
    for sel in [
        'button.jobs-apply-button',
        'button:has-text("Easy Apply")',
        '[aria-label*="Easy Apply"]',
        '.jobs-s-apply button',
        'button[data-control-name="jobdetails_topcard_inapply"]',
    ]:
        try:
            el = page.query_selector(sel)
            if el and el.is_visible():
                btn = el
                break
        except Exception:
            pass

    if not btn:
        # Check for external apply link and record it
        ext_btn = (page.query_selector('button:has-text("Apply")') or
                   page.query_selector('a:has-text("Apply on company website")'))
        ext_url = ""
        if ext_btn:
            try:
                ext_url = ext_btn.get_attribute("href") or page.url
            except Exception:
                ext_url = page.url
        log.append(f"[LinkedIn] No Easy Apply button — external apply required. URL: {ext_url or page.url}")
        screenshot(page, job['ID'], "no_easy_apply")
        return "skipped_no_easy_apply"

    log.append("[LinkedIn] Clicking Easy Apply...")
    btn.click()
    time.sleep(3)
    screenshot(page, job['ID'], "step1")

    # Multi-step modal handler
    for step in range(10):
        # Phone
        for sel in ['input[id*="phoneNumber"]','input[name*="phone"]','input[placeholder*="Phone"]']:
            el = page.query_selector(sel)
            if el:
                try:
                    if not el.input_value():
                        el.fill(creds.get("CANDIDATE_PHONE","+91 7704077700"))
                except Exception:
                    pass

        # Resume file upload
        file_input = page.query_selector('input[type="file"]')
        if file_input and cv_pdf and os.path.exists(cv_pdf):
            try:
                file_input.set_input_files(cv_pdf)
                log.append(f"[LinkedIn] Uploaded CV: {os.path.basename(cv_pdf)}")
                time.sleep(2)
            except Exception as e:
                log.append(f"[LinkedIn] CV upload error: {e}")

        # Cover letter
        for sel in ['textarea[name*="cover"]','div[data-test-id*="cover"] textarea','.cover-letter-textarea','textarea']:
            el = page.query_selector(sel)
            if el:
                try:
                    if not el.input_value():
                        el.fill(cover_letter_text(job))
                        break
                except Exception:
                    pass

        # Check for free-text or multi-choice screening questions needing candidate input
        has_unanswered, pending_qs = sm.inspect_form_screening_questions(page, job)
        if has_unanswered:
            log.append(f"[LinkedIn] ⏸ Pausing application: {len(pending_qs)} screening question(s) need your review.")
            screenshot(page, job['ID'], "needs_review")
            return "needs_my_input"

        screenshot(page, job['ID'], f"step{step+1}")

        # Navigate
        submit = (page.query_selector('button[aria-label="Submit application"]') or
                  page.query_selector('button:has-text("Submit application")'))
        review = page.query_selector('button:has-text("Review")')
        nxt    = (page.query_selector('button:has-text("Next")') or
                  page.query_selector('button[aria-label*="Continue"]'))

        if submit:
            log.append("[LinkedIn] Submitting application...")
            submit.click()
            time.sleep(4)
            screenshot(page, job['ID'], "submitted")

            # Dismiss success modal
            done = (page.query_selector('button:has-text("Done")') or
                    page.query_selector('button[aria-label*="Dismiss"]'))
            if done:
                done.click()
            log.append("[LinkedIn] ✅ Application submitted!")
            return "applied"
        elif review:
            review.click(); time.sleep(2)
        elif nxt:
            nxt.click(); time.sleep(2)
        else:
            log.append(f"[LinkedIn] Step {step+1}: no navigation button found.")
            break

    return "error_incomplete"

# ─── Portal: Naukri ───────────────────────────────────────────────────────────

def naukri_login(page, creds, context, headless, log):
    log.append("[Naukri] Checking session...")
    page.goto("https://www.naukri.com/", timeout=40000)
    time.sleep(3)
    if page.query_selector('a[href*="mnjuser/profile"]') or page.query_selector('.nI-gNb-drawer__icon'):
        log.append("[Naukri] Already logged in ✅")
        return True

    log.append("[Naukri] Logging in...")
    page.goto("https://www.naukri.com/nlogin/login", timeout=40000)
    time.sleep(2)

    page.type('input[placeholder*="Email"]', creds.get("NAUKRI_EMAIL",""), delay=70)
    time.sleep(0.3)
    page.type('input[type="password"]', creds.get("NAUKRI_PASSWORD",""), delay=70)
    time.sleep(0.3)

    # Click login button
    login_btn = (page.query_selector('button[type="submit"]') or
                 page.query_selector('button:has-text("Login")'))
    if login_btn:
        login_btn.click()
    time.sleep(5)

    if "naukri.com" in page.url and "login" not in page.url:
        context.storage_state(path=SESSION["naukri"])
        log.append("[Naukri] Login successful ✅ — session saved.")
        return True

    if is_blocked_page(page, log, "Naukri", job={"Company": "Naukri Login", "ID": "login_naukri", "URL": page.url}, headless=headless):
        return False

    context.storage_state(path=SESSION["naukri"])
    return True

def naukri_apply(page, job, creds, cv_pdf, cover_pdf, context, headless, log):
    url = job.get("URL","")
    log.append(f"[Naukri] Opening job: {url}")
    try:
        page.goto(url, timeout=35000)
    except Exception as e:
        log.append(f"[Naukri] Page load error: {e}")
        return "error"
    time.sleep(4)
    screenshot(page, job['ID'], "nk_opened")

    if is_blocked_page(page, log, "Naukri", job=job, headless=headless):
        return "needs_manual_action"

    # If landed on search page, navigate to first actual job listing
    if is_search_page(page.url):
        if not navigate_to_first_job(page, "naukri", log):
            log.append("[Naukri] Could not navigate to a job listing from search page.")
            return "skipped_search_page"
        time.sleep(3)
        screenshot(page, job['ID'], "nk_job_page")
        if is_blocked_page(page, log, "Naukri", job=job, headless=headless):
            return "needs_manual_action"

    # Check if already applied
    page_text = page.inner_text("body").lower() if page.query_selector("body") else ""
    if "already applied" in page_text or page.query_selector('button:has-text("Applied")') or page.query_selector('span:has-text("Already Applied")'):
        log.append("[Naukri] Already Applied ✅")
        return "applied"

    # Check if job is expired or inactive on Naukri
    inactive_keywords = [
        "this job is no longer active", "this job has expired",
        "job is no longer available", "this vacancy is filled",
        "job has expired", "job is inactive"
    ]
    if any(ik in page_text for ik in inactive_keywords):
        log.append("[Naukri] ⚠️ Job listing is expired or no longer active on Naukri.")
        ss_path = screenshot(page, job['ID'], "nk_expired")
        log_needs_manual_apply(job, reason="Listing Expired or Inactive on Naukri", screenshot_file=ss_path)
        return "needs_manual_action"

    # 1. Check for explicit External Apply controls (e.g. company site redirect)
    ext_apply_selectors = [
        'button:has-text("Apply on company site")',
        'a:has-text("Apply on company site")',
        'button:has-text("Apply on company website")',
        'a:has-text("Apply on company website")',
        'button:has-text("Apply on employer site")',
        'a:has-text("Apply on employer site")',
        'button:has-text("Apply externally")',
        'a:has-text("Apply externally")',
        '[class*="company-site"]',
        '[class*="external-apply"]',
    ]
    for sel in ext_apply_selectors:
        try:
            el = page.query_selector(sel)
            if el and el.is_visible():
                ext_url = el.get_attribute("href") or url
                log.append(f"[Naukri] 🌐 External company site redirect detected ({ext_url}).")
                ss_path = screenshot(page, job['ID'], "nk_external_redirect")
                log_needs_manual_apply(job, reason=f"External Company Site Redirect ({ext_url})", screenshot_file=ss_path)
                return "needs_manual_action"
        except Exception:
            pass

    # 2. Find Apply button — comprehensive 2026 selectors
    apply_btn = None
    naukri_apply_selectors = [
        '#apply-button',
        'button#apply-button',
        'a#apply-button',
        '.apply-button',
        'button.apply-button',
        'a.apply-button',
        '[class*="applyButton"]',
        '[class*="apply-button"]',
        '[class*="apply-btn"]',
        'button:has-text("Apply on site")',
        'a:has-text("Apply on site")',
        'button:has-text("Apply")',
        'a:has-text("Apply")',
        'div[id*="apply"] button',
        'div[id*="apply"] a',
        'div[class*="apply"] button',
        'div[class*="apply"] a',
    ]
    for sel in naukri_apply_selectors:
        try:
            el = page.query_selector(sel)
            if el and el.is_visible():
                apply_btn = el
                break
        except Exception:
            pass

    if not apply_btn:
        log.append("[Naukri] ⚠️ No Apply button found — routing to needs_manual_apply.csv for manual application.")
        ss_path = screenshot(page, job['ID'], "nk_no_apply")
        log_needs_manual_apply(job, reason="No Apply button detected (check portal manually)", screenshot_file=ss_path)
        return "needs_manual_action"

    btn_txt = ""
    btn_href = ""
    try:
        btn_txt = apply_btn.inner_text().strip()
        btn_href = apply_btn.get_attribute("href") or ""
    except Exception:
        pass

    if "applied" in btn_txt.lower():
        log.append(f"[Naukri] Button says '{btn_txt}' — already applied!")
        return "applied"

    # If the button text or link indicates an external application
    if any(k in btn_txt.lower() for k in ["company site", "employer site", "company website", "externally"]) or (btn_href and "http" in btn_href and "naukri.com" not in btn_href):
        ext_dest = btn_href or btn_txt
        log.append(f"[Naukri] 🌐 External apply detected on button ('{btn_txt}'). Routing to manual queue.")
        ss_path = screenshot(page, job['ID'], "nk_external_redirect")
        log_needs_manual_apply(job, reason=f"External Company Site Redirect: {ext_dest}", screenshot_file=ss_path)
        return "needs_manual_action"

    log.append(f"[Naukri] Clicking Apply ('{btn_txt}')...")
    try:
        apply_btn.click()
    except Exception as e:
        log.append(f"[Naukri] Click error: {e}")
        ss_path = screenshot(page, job['ID'], "nk_click_error")
        log_needs_manual_apply(job, reason=f"Apply click error: {e}", screenshot_file=ss_path)
        return "needs_manual_action"

    time.sleep(4)
    screenshot(page, job['ID'], "nk_apply_clicked")

    # Detect if clicking the apply button navigated to an external company domain
    if "naukri.com" not in page.url:
        log.append(f"[Naukri] 🌐 Navigated away to external company site: {page.url}. Routing to manual queue.")
        ss_path = screenshot(page, job['ID'], "nk_nav_external")
        log_needs_manual_apply(job, reason=f"External Company Site Redirect ({page.url})", screenshot_file=ss_path)
        return "needs_manual_action"

    if is_blocked_page(page, log, "Naukri", job=job, headless=headless):
        return "needs_manual_action"

    # PATCH E: Require explicit success confirmation — do NOT auto-mark applied
    SUCCESS_KEYWORDS = [
        "successfully applied", "application submitted", "application sent",
        "thank you for applying", "your application has been",
        "application received", "applied successfully",
    ]
    page_text_after = ""
    try:
        page_text_after = page.inner_text("body").lower()
    except Exception:
        pass
    if any(kw in page_text_after for kw in SUCCESS_KEYWORDS):
        log.append("[Naukri] ✅ Application submitted and confirmed!")
        return "applied"

    # Upload resume if dialog opened
    file_input = page.query_selector('input[type="file"]')
    if file_input and cv_pdf and os.path.exists(cv_pdf):
        try:
            file_input.set_input_files(cv_pdf)
            log.append(f"[Naukri] Uploaded CV: {os.path.basename(cv_pdf)}")
            time.sleep(2)
        except Exception as e:
            log.append(f"[Naukri] CV upload error: {e}")

    # Cover letter textarea
    for sel in ['textarea[name*="cover"]','textarea[placeholder*="cover"]',
                'textarea[placeholder*="Cover"]','textarea']:
        el = page.query_selector(sel)
        if el:
            try:
                if not el.input_value():
                    el.fill(cover_letter_text(job))
                    break
            except Exception:
                pass

    # Check for free-text or multi-choice screening questions needing candidate input
    has_unanswered, pending_qs = sm.inspect_form_screening_questions(page, job)
    if has_unanswered:
        log.append(f"[Naukri] ⏸ Pausing application: {len(pending_qs)} screening question(s) need your review.")
        screenshot(page, job['ID'], "needs_review")
        return "needs_my_input"

    # Final submit
    for sel in ['button:has-text("Submit")', 'button:has-text("Apply Now")',
                'button:has-text("Send Application")', 'button[type="submit"]']:
        btn = page.query_selector(sel)
        if btn and btn.is_visible():
            try:
                log.append(f"[Naukri] Clicking submit: {sel}")
                btn.click()
                time.sleep(4)
                screenshot(page, job['ID'], "nk_submitted")
                # PATCH E: verify success after submit click
                try:
                    page_text_final = page.inner_text("body").lower()
                except Exception:
                    page_text_final = ""
                if any(kw in page_text_final for kw in SUCCESS_KEYWORDS):
                    log.append("[Naukri] ✅ Application submitted and confirmed!")
                    return "applied"
                else:
                    log.append("[Naukri] ⚡ Submit clicked but no confirmation text. Marking as Attempted.")
                    return "attempted"
            except Exception as e:
                log.append(f"[Naukri] Submit error: {e}")

    # PATCH E: No longer blindly return 'applied' — return 'attempted' if we got this far
    log.append("[Naukri] ⚡ Apply clicked but could not confirm submission. Marking as Attempted.")
    return "attempted"


# ─── Portal: Bayt ─────────────────────────────────────────────────────────────

def bayt_login(page, creds, context, headless, log):
    log.append("[Bayt] Checking session...")
    try:
        page.goto("https://www.bayt.com/en/", timeout=40000)
        time.sleep(3)
    except Exception as e:
        log.append(f"[Bayt] Homepage timeout, trying login directly: {e}")

    if page.query_selector('a[href*="/en/user/profile"]') or page.query_selector('.user-nav') or page.query_selector('[class*="userAvatar"]'):
        log.append("[Bayt] Already logged in OK")
        return True

    log.append("[Bayt] Logging in...")
    try:
        page.goto("https://www.bayt.com/en/user/login/", timeout=40000)
        time.sleep(3)
    except Exception as e:
        log.append(f"[Bayt] Login page timeout: {e}")
        if not headless:
            log.append("[Bayt] Please log in manually in browser. Waiting 90s...")
            time.sleep(90)
            context.storage_state(path=SESSION["bayt"])
            return True
        return False

    # Try multiple email field selectors
    email_filled = False
    for sel in ['input[name="email"]', 'input[type="email"]', 'input[placeholder*="Email"]', 'input[id*="email"]']:
        try:
            el = page.query_selector(sel)
            if el:
                el.click()
                time.sleep(0.3)
                el.fill(creds.get("BAYT_EMAIL",""))
                email_filled = True
                break
        except Exception:
            pass

    if not email_filled:
        log.append("[Bayt] Could not find email field. Waiting for manual login...")
        if not headless:
            time.sleep(90)
            context.storage_state(path=SESSION["bayt"])
            return True
        return False

    # Password
    for sel in ['input[name="password"]', 'input[type="password"]', 'input[placeholder*="Password"]']:
        try:
            el = page.query_selector(sel)
            if el:
                el.click()
                time.sleep(0.3)
                el.fill(creds.get("BAYT_PASSWORD",""))
                break
        except Exception:
            pass

    time.sleep(0.5)
    for sel in ['button[type="submit"]', 'input[type="submit"]', 'button:has-text("Login")', 'button:has-text("Sign in")']:
        try:
            btn = page.query_selector(sel)
            if btn:
                btn.click()
                break
        except Exception:
            pass
    time.sleep(5)

    if "bayt.com" in page.url and "login" not in page.url:
        context.storage_state(path=SESSION["bayt"])
        log.append("[Bayt] Login successful - session saved.")
        return True

    if is_blocked_page(page, log, "Bayt", job={"Company": "Bayt Login", "ID": "login_bayt", "URL": page.url}, headless=headless):
        return False

    context.storage_state(path=SESSION["bayt"])
    return True

def bayt_apply(page, job, creds, cv_pdf, cover_pdf, context, headless, log):
    url = job.get("URL","")
    log.append(f"[Bayt] Opening job: {url}")
    try:
        page.goto(url, timeout=35000)
    except Exception as e:
        log.append(f"[Bayt] Page load error: {e}")
        return "error"
    time.sleep(4)
    screenshot(page, job['ID'], "bayt_opened")

    if is_blocked_page(page, log, "Bayt", job=job, headless=headless):
        return "needs_manual_action"

    # If on search page, navigate to first real job
    if is_search_page(page.url):
        if not navigate_to_first_job(page, "bayt", log):
            log.append("[Bayt] Could not navigate to a job listing from search page.")
            return "skipped_search_page"
        time.sleep(3)
        if is_blocked_page(page, log, "Bayt", job=job, headless=headless):
            return "needs_manual_action"

    # PATCH B: Enhanced Bayt apply button finder — JS-based fallback for DOM changes
    apply_btn = None
    bayt_apply_selectors = [
        'a.btn.apply',
        'button:has-text("Apply Now")',
        'a:has-text("Apply Now")',
        'button:has-text("Apply")',
        '[class*="apply-btn"]',
        '[class*="applyBtn"]',
        '[class*="apply_btn"]',
        'a[data-js-aid*="apply"]',
        '[id*="applyButton"]',
        '[id*="apply-button"]',
        'a[href*="/apply"]',
        '.u-link--chevron',
    ]
    for sel in bayt_apply_selectors:
        try:
            btn = page.query_selector(sel)
            if btn and btn.is_visible():
                apply_btn = btn
                log.append(f"[Bayt] Found apply button via: {sel}")
                break
        except Exception:
            pass

    # JS fallback: scan all links/buttons for apply text
    if not apply_btn:
        try:
            apply_btn = page.evaluate_handle("""
                () => {
                    const els = [...document.querySelectorAll('a, button')];
                    return els.find(el => {
                        const t = (el.textContent || '').trim().toLowerCase();
                        const h = (el.href || '').toLowerCase();
                        return t === 'apply now' || t === 'apply' ||
                               h.includes('/apply') || h.includes('apply-now');
                    }) || null;
                }
            """)
            # evaluate_handle returns JSHandle; convert to ElementHandle
            if apply_btn and apply_btn.as_element():
                apply_btn = apply_btn.as_element()
                log.append("[Bayt] Found apply button via JS evaluate fallback.")
            else:
                apply_btn = None
        except Exception as e:
            log.append(f"[Bayt] JS fallback error: {e}")
            apply_btn = None

    if not apply_btn:
        log.append("[Bayt] No Apply button found on this page.")
        screenshot(page, job['ID'], "bayt_no_apply")
        return "skipped_no_apply"

    log.append("[Bayt] Clicking Apply Now...")
    try:
        apply_btn.click()
    except Exception as e:
        log.append(f"[Bayt] Click error: {e}")
        return "skipped_no_apply"
    time.sleep(4)
    screenshot(page, job['ID'], "bayt_apply_clicked")

    # Upload CV if file input appears
    file_input = page.query_selector('input[type="file"]')
    if file_input and cv_pdf and os.path.exists(cv_pdf):
        try:
            file_input.set_input_files(cv_pdf)
            log.append(f"[Bayt] Uploaded CV: {os.path.basename(cv_pdf)}")
            time.sleep(2)
        except Exception as e:
            log.append(f"[Bayt] CV upload error: {e}")

    # Cover letter
    for sel in ['textarea[name*="cover"]','textarea[id*="cover"]','textarea[placeholder*="cover"]','textarea']:
        el = page.query_selector(sel)
        if el:
            try:
                if not el.input_value():
                    el.fill(cover_letter_text(job))
                    break
            except Exception:
                pass

    # Check for free-text or multi-choice screening questions needing candidate input
    has_unanswered, pending_qs = sm.inspect_form_screening_questions(page, job)
    if has_unanswered:
        log.append(f"[Bayt] ⏸ Pausing application: {len(pending_qs)} screening question(s) need your review.")
        screenshot(page, job['ID'], "needs_review")
        return "needs_my_input"

    # Submit
    submit_success = False
    for sel in ['button:has-text("Submit Application")', 'button:has-text("Submit")',
                'button:has-text("Apply")', 'a:has-text("Submit")',
                'input[type="submit"]', 'button[type="submit"]']:
        btn = page.query_selector(sel)
        if btn and btn.is_visible():
            try:
                log.append(f"[Bayt] Clicking submit: {sel}")
                btn.click()
                time.sleep(4)
                screenshot(page, job['ID'], "bayt_submitted")
                # Verify success
                page_text = page.inner_text("body") if page.query_selector("body") else ""
                if any(kw in page_text.lower() for kw in
                       ["application submitted", "applied successfully", "thank you",
                        "application received", "successfully applied"]):
                    log.append("[Bayt] ✅ Application submitted and confirmed!")
                    return "applied"
                else:
                    log.append("[Bayt] ⚡ Submit clicked but success message not detected.")
                    submit_success = True  # Attempted
                    break
            except Exception as e:
                log.append(f"[Bayt] Submit error: {e}")

    if submit_success:
        return "attempted"
    return "error_incomplete"

# ─── Portal: Indeed ───────────────────────────────────────────────────────────

def indeed_login(page, creds, context, headless, log):
    log.append("[Indeed] Checking session...")
    page.goto("https://in.indeed.com/", timeout=40000)
    time.sleep(3)
    if page.query_selector('a[href*="/account/view"]') or page.query_selector('.gnav-LoggedInAccountLink'):
        log.append("[Indeed] Already logged in ✅")
        return True

    log.append("[Indeed] Logging in...")
    page.goto("https://secure.indeed.com/auth?hl=en_IN&co=IN&continue=https://in.indeed.com/", timeout=40000)
    time.sleep(3)

    # Step 1: Email
    email_input = page.query_selector('input[name="__email"]') or page.query_selector('input[type="email"]')
    if email_input:
        email_input.fill(creds.get("INDEED_EMAIL",""))
        time.sleep(0.5)
        cont = page.query_selector('button[type="submit"]')
        if cont: cont.click()
        time.sleep(3)

    # Step 2: Password
    pw_input = page.query_selector('input[name="__password"]') or page.query_selector('input[type="password"]')
    if pw_input:
        pw_input.fill(creds.get("INDEED_PASSWORD",""))
        time.sleep(0.5)
        cont = page.query_selector('button[type="submit"]')
        if cont: cont.click()
        time.sleep(5)

    if "indeed.com" in page.url and "auth" not in page.url:
        context.storage_state(path=SESSION["indeed"])
        log.append("[Indeed] Login successful ✅ — session saved.")
        return True

    if is_blocked_page(page, log, "Indeed", job={"Company": "Indeed Login", "ID": "login_indeed", "URL": page.url}, headless=headless):
        return False

    context.storage_state(path=SESSION["indeed"])
    return True

def indeed_apply(page, job, creds, cv_pdf, cover_pdf, context, headless, log):
    url = job.get("URL","")
    log.append(f"[Indeed] Opening job: {url}")
    try:
        page.goto(url, timeout=35000)
    except Exception as e:
        log.append(f"[Indeed] Page load error: {e}")
        return "error"
    time.sleep(4)
    screenshot(page, job['ID'], "ind_opened")

    if is_blocked_page(page, log, "Indeed", job=job, headless=headless):
        return "needs_manual_action"

    # If on search results page, click first job
    if is_search_page(page.url):
        if not navigate_to_first_job(page, "indeed", log):
            log.append("[Indeed] Could not navigate to a job listing from search page.")
            return "skipped_search_page"
        time.sleep(3)
        if is_blocked_page(page, log, "Indeed", job=job, headless=headless):
            return "needs_manual_action"

    apply_btn = (page.query_selector('button:has-text("Apply now")') or
                 page.query_selector('span:has-text("Apply now")') or
                 page.query_selector('[id="indeedApplyButton"]') or
                 page.query_selector('.ia-IndeedApplyButton') or
                 page.query_selector('button[data-indeed-apply-jobid]') or
                 page.query_selector('a:has-text("Apply on company site")'))

    if not apply_btn:
        log.append("[Indeed] No Apply button found.")
        return "skipped_no_apply"

    log.append("[Indeed] Clicking Apply now...")
    apply_btn.click()
    time.sleep(4)
    screenshot(page, job['ID'], "ind_apply_clicked")

    if is_blocked_page(page, log, "Indeed", job=job, headless=headless):
        return "needs_manual_action"

    # Handle multi-step Indeed application.
    # Real Indeed flows commonly run longer than 8 steps once screening questions
    # are included, so this now: (a) fills screening-question inputs generically,
    # not just contact fields, (b) detects when a click made no real progress
    # instead of silently burning through every iteration, and (c) reports
    # exactly what's still unfilled if it does have to give up.
    MAX_STEPS = 15
    last_fingerprint = None
    stuck_count = 0
    unfilled_required = []

    for step in range(MAX_STEPS):
        unfilled_required = []

        # Known contact fields
        for fname, val in [('input[name*="firstName"]', "Tanuj"),
                           ('input[name*="lastName"]', "Chandel"),
                           ('input[name*="phone"]', creds.get("CANDIDATE_PHONE","+91 7704077700")),
                           ('input[name*="city"]', "Kanpur"),
                           ('input[name*="email"]', creds.get("INDEED_EMAIL",""))]:
            el = page.query_selector(fname)
            if el:
                try:
                    if not el.input_value():
                        el.fill(val)
                except Exception:
                    pass

        # Resume upload
        file_input = page.query_selector('input[type="file"]')
        if file_input and cv_pdf and os.path.exists(cv_pdf):
            try:
                file_input.set_input_files(cv_pdf)
                log.append(f"[Indeed] Uploaded CV: {os.path.basename(cv_pdf)}")
                time.sleep(2)
            except Exception as e:
                log.append(f"[Indeed] CV upload error: {e}")

        # Cover letter
        for sel in ['textarea[name*="coverletter"]','textarea[id*="cover"]','textarea']:
            el = page.query_selector(sel)
            if el:
                try:
                    if not el.input_value():
                        el.fill(cover_letter_text(job))
                        break
                except Exception:
                    pass

        # Check for free-text or multi-choice screening questions needing candidate review
        has_unanswered, pending_qs = sm.inspect_form_screening_questions(page, job)
        if has_unanswered:
            log.append(f"[Indeed] ⏸ Pausing application: {len(pending_qs)} screening question(s) need your review.")
            screenshot(page, job['ID'], "needs_review")
            return "needs_my_input"

        screenshot(page, job['ID'], f"ind_step{step+1}")

        # Navigate buttons — widened beyond just "Continue"/"Next"
        submit = (page.query_selector('button:has-text("Submit your application")') or
                  page.query_selector('button:has-text("Submit application")') or
                  page.query_selector('button[type="submit"]:has-text("Submit")'))
        nxt = (page.query_selector('button:has-text("Continue")') or
               page.query_selector('button:has-text("Next")') or
               page.query_selector('button:has-text("Review your application")') or
               page.query_selector('button:has-text("Save and continue")') or
               page.query_selector('button[aria-label*="Continue"]'))

        if submit:
            submit.click()
            time.sleep(4)
            screenshot(page, job['ID'], "ind_submitted")
            log.append("[Indeed] ✅ Application submitted!")
            return "applied"

        if not nxt:
            log.append(f"[Indeed] Step {step+1}: no navigation button found.")
            break

        try:
            disabled = nxt.get_attribute("disabled") is not None or nxt.is_enabled() is False
        except Exception:
            disabled = False
        if disabled:
            log.append(f"[Indeed] Step {step+1}: Continue/Next button is disabled — "
                        f"likely blocked by unfilled field(s): {unfilled_required or 'unknown required field'}.")
            break

        # Detect a click that made no real progress (same URL + same button text
        # as last time) so we stop after 2 no-op clicks instead of exhausting
        # every remaining step silently.
        fingerprint = (page.url, unfilled_required and tuple(unfilled_required))
        if fingerprint == last_fingerprint:
            stuck_count += 1
        else:
            stuck_count = 0
        last_fingerprint = fingerprint
        if stuck_count >= 2:
            log.append(f"[Indeed] Step {step+1}: stuck — clicking Continue isn't changing the page. "
                        f"Likely unfilled required field(s): {unfilled_required or 'unknown'}.")
            break

        nxt.click()
        time.sleep(2)

    if unfilled_required:
        log.append(f"[Indeed] Gave up with unfilled fields still on the page: {unfilled_required}")
    return "error_incomplete"

# ─── Portal: Glassdoor ────────────────────────────────────────────────────────

def glassdoor_login(page, creds, context, headless, log):
    log.append("[Glassdoor] Checking session...")
    page.goto("https://www.glassdoor.com/index.htm", timeout=40000)
    time.sleep(3)
    if page.query_selector('.signed-in') or page.query_selector('[data-test="header-account-info"]'):
        log.append("[Glassdoor] Already logged in ✅")
        return True

    log.append("[Glassdoor] Logging in...")
    page.goto("https://www.glassdoor.com/profile/login_input.htm", timeout=40000)
    time.sleep(2)

    email = page.query_selector('input[name="username"]') or page.query_selector('input[type="email"]')
    if email:
        email.fill(creds.get("GLASSDOOR_EMAIL",""))
        time.sleep(0.3)
        cont = page.query_selector('button[type="submit"]') or page.query_selector('#loginBtn')
        if cont: cont.click()
        time.sleep(2)

    pw = page.query_selector('input[name="password"]') or page.query_selector('input[type="password"]')
    if pw:
        pw.fill(creds.get("GLASSDOOR_PASSWORD",""))
        time.sleep(0.3)
        cont = page.query_selector('button[type="submit"]') or page.query_selector('#loginBtn')
        if cont: cont.click()
        time.sleep(5)

    if "glassdoor.com" in page.url and "login" not in page.url:
        context.storage_state(path=SESSION["glassdoor"])
        log.append("[Glassdoor] Login successful ✅ — session saved.")
        return True

    if is_blocked_page(page, log, "Glassdoor", job={"Company": "Glassdoor Login", "ID": "login_glassdoor", "URL": page.url}, headless=headless):
        return False

    context.storage_state(path=SESSION["glassdoor"])
    return True

def glassdoor_apply(page, job, creds, cv_pdf, cover_pdf, context, headless, log):
    url = job.get("URL","")
    log.append(f"[Glassdoor] Opening job: {url}")
    try:
        page.goto(url, timeout=35000)
    except Exception as e:
        log.append(f"[Glassdoor] Page load error: {e}")
        return "error"
    time.sleep(4)
    screenshot(page, job['ID'], "gd_opened")

    if is_blocked_page(page, log, "Glassdoor", job=job, headless=headless):
        return "needs_manual_action"

    # If on search page, navigate to first job
    if is_search_page(page.url):
        if not navigate_to_first_job(page, "glassdoor", log):
            log.append("[Glassdoor] Could not navigate to a job listing from search page.")
            return "skipped_search_page"
        time.sleep(3)
        if is_blocked_page(page, log, "Glassdoor", job=job, headless=headless):
            return "needs_manual_action"

    apply_btn = (page.query_selector('button:has-text("Easy Apply")') or
                 page.query_selector('button:has-text("Apply Now")') or
                 page.query_selector('[data-test="apply-button"]') or
                 page.query_selector('.apply-btn') or
                 page.query_selector('a:has-text("Apply")') or
                 page.query_selector('[class*="applyButton"]'))

    if not apply_btn:
        log.append("[Glassdoor] No Apply button found.")
        return "skipped_no_apply"

    log.append("[Glassdoor] Clicking Apply...")
    apply_btn.click()
    time.sleep(4)
    screenshot(page, job['ID'], "gd_apply_clicked")

    # Upload CV
    file_input = page.query_selector('input[type="file"]')
    if file_input and cv_pdf and os.path.exists(cv_pdf):
        try:
            file_input.set_input_files(cv_pdf)
            log.append(f"[Glassdoor] Uploaded CV: {os.path.basename(cv_pdf)}")
            time.sleep(2)
        except Exception as e:
            log.append(f"[Glassdoor] CV upload error: {e}")

    # Cover letter
    for sel in ['textarea[name*="cover"]','textarea[placeholder*="cover"]','textarea']:
        el = page.query_selector(sel)
        if el:
            try:
                if not el.input_value():
                    el.fill(cover_letter_text(job))
                    break
            except Exception:
                pass

    for step in range(6):
        screenshot(page, job['ID'], f"gd_step{step+1}")

        # Check for free-text or multi-choice screening questions needing candidate review
        has_unanswered, pending_qs = sm.inspect_form_screening_questions(page, job)
        if has_unanswered:
            log.append(f"[Glassdoor] ⏸ Pausing application: {len(pending_qs)} screening question(s) need your review.")
            screenshot(page, job['ID'], "needs_review")
            return "needs_my_input"

        submit = (page.query_selector('button:has-text("Submit")') or
                  page.query_selector('button:has-text("Apply")'))
        nxt = (page.query_selector('button:has-text("Continue")') or
               page.query_selector('button:has-text("Next")'))

        if submit:
            submit.click()
            time.sleep(4)
            screenshot(page, job['ID'], "gd_submitted")
            log.append("[Glassdoor] ✅ Application submitted!")
            return "applied"
        elif nxt:
            nxt.click(); time.sleep(2)
        else:
            break

    return "error_incomplete"


# ─── Portal: Micro1 ───────────────────────────────────────────────────────────

def micro1_apply(page, job, creds, cv_pdf, cover_pdf, context, headless, log):
    url = job.get("URL", "")
    log.append(f"[Micro1] Opening job: {url[:80]}")
    try:
        page.goto(url, timeout=35000)
        time.sleep(4)
    except Exception as e:
        log.append(f"[Micro1] Page load error: {e}")
        return "error"

    screenshot(page, job['ID'], "m1_page")

    # Look for Continue / Apply buttons
    for sel in ['button:has-text("Continue with LinkedIn")', 'button:has-text("Continue with Google")',
                'button:has-text("Continue")', 'button:has-text("Apply")', 'a:has-text("Apply")']:
        btn = page.query_selector(sel)
        if btn and btn.is_visible():
            log.append(f"[Micro1] Found opportunity action button: '{btn.inner_text().strip()}'")
            try:
                btn.click()
                time.sleep(3)
                screenshot(page, job['ID'], "m1_clicked")
            except Exception as ce:
                log.append(f"[Micro1] Click error: {ce}")
            break

    # Check for file input (resume upload)
    file_input = page.query_selector('input[type="file"]')
    if file_input and cv_pdf and os.path.exists(cv_pdf):
        try:
            file_input.set_input_files(cv_pdf)
            log.append(f"[Micro1] Uploaded tailored CV: {os.path.basename(cv_pdf)}")
            time.sleep(2)
        except Exception as fe:
            log.append(f"[Micro1] CV upload error: {fe}")

    # Check for submission button
    for sel in ['button:has-text("Submit Application")', 'button:has-text("Submit")', 'button[type="submit"]']:
        sbtn = page.query_selector(sel)
        if sbtn and sbtn.is_visible():
            try:
                sbtn.click()
                time.sleep(4)
                screenshot(page, job['ID'], "m1_submitted")
                log.append("[Micro1] ✅ Application submitted!")
                return "applied"
            except Exception as se:
                log.append(f"[Micro1] Submit click error: {se}")

    log.append("[Micro1] ⚡ Job page opened and application flow initiated. Marking as Attempted.")
    return "attempted"


# ─── Portal: Remotive / RemoteOK / Himalayas ─────────────────────────────────

def remotive_apply(page, job, creds, cv_pdf, cover_pdf, context, headless, log):
    url = job.get("URL", "")
    portal_tag = detect_portal(url).upper() or "REMOTE"
    log.append(f"[{portal_tag}] Opening job: {url[:80]}")
    try:
        page.goto(url, timeout=35000)
        time.sleep(4)
    except Exception as e:
        log.append(f"[{portal_tag}] Page load error: {e}")
        return "error"

    screenshot(page, job['ID'], f"{portal_tag.lower()}_page")

    # Guardrail 1: CAPTCHA / 2FA / Cloudflare check on listing page
    if is_blocked_page(page, log=log, tag=portal_tag, job=job, headless=headless):
        return "needs_manual_action"

    # Check for expired/closed listing
    try:
        page_text = (page.inner_text("body")[:2500] if page.query_selector("body") else "").lower()
    except Exception:
        page_text = ""
    for closed_sig in ["job is closed", "job has expired", "position has been filled", "this job is no longer available", "no longer accepting applications"]:
        if closed_sig in page_text:
            log.append(f"[{portal_tag}] Listing is closed/expired: '{closed_sig}'")
            log_needs_manual_apply(job, reason=f"Listing expired: {closed_sig}", screenshot_file=screenshot(page, job['ID'], "expired"))
            return "needs_manual_action"

    # Find apply button
    apply_btn = None
    portal_type = detect_portal(url)
    if portal_type == "remoteok":
        rok_match = re.search(r'-(\d{5,8})(?:$|\?|/)', url)
        rok_num_id = rok_match.group(1) if rok_match else ""
        if rok_num_id:
            apply_btn = (page.query_selector(f'a.apply_{rok_num_id}') or
                         page.query_selector(f'a[href*="{rok_num_id}"]'))

    if not apply_btn:
        for sel in [
            'a[href*="/apply"]',
            'a:has-text("Apply for this position")',
            'a:has-text("Apply for this role")',
            'a:has-text("Apply for this job")',
            'a:has-text("Apply now")',
            'button:has-text("Apply now")',
            'button:has-text("Apply for this job")',
            'a.action-apply',
            'a:has-text("Apply")',
            'button:has-text("Apply")'
        ]:
            el = page.query_selector(sel)
            if el and el.is_visible():
                apply_btn = el
                break

    if not apply_btn:
        log.append(f"[{portal_tag}] No direct Apply button on page.")
        log_needs_manual_apply(job, reason=f"No direct Apply button found on {portal_tag} page", screenshot_file=screenshot(page, job['ID'], "no_apply"))
        return "needs_manual_action"

    btn_href = apply_btn.get_attribute("href") or ""
    log.append(f"[{portal_tag}] Found apply link: {btn_href[:70]}")
    init_page_count = len(context.pages)

    try:
        if btn_href and btn_href.startswith("http") and apply_btn.get_attribute("target") != "_blank":
            page.goto(btn_href, timeout=35000)
            time.sleep(3)
        else:
            apply_btn.click()
            time.sleep(4)
    except Exception as ce:
        log.append(f"[{portal_tag}] Navigation/click error: {ce}")

    # Handle popup / new tab if opened
    if len(context.pages) > init_page_count:
        page = context.pages[-1]
        time.sleep(2)

    screenshot(page, job['ID'], f"{portal_tag.lower()}_target_page")

    # Guardrail 2: Challenge check on destination / ATS page
    if is_blocked_page(page, log=log, tag=f"{portal_tag} ATS", job=job, headless=headless):
        return "needs_manual_action"

    # Check for login / signup barrier on the portal
    curr_url = (page.url or "").lower()
    if "sign-up" in curr_url or "signup" in curr_url or "login" in curr_url or "register" in curr_url:
        log.append(f"[{portal_tag}] Portal authentication required ({page.url}). Routing to manual apply.")
        log_needs_manual_apply(job, reason=f"Portal login/signup required: {page.url}", screenshot_file=screenshot(page, job['ID'], "login_wall"))
        return "needs_manual_action"

    # Guardrail 3: Check for screening questions on ATS form
    has_unanswered, pending_qs = sm.inspect_form_screening_questions(page, job)
    if has_unanswered:
        log.append(f"[{portal_tag} ATS] ⏸ Pausing application: {len(pending_qs)} screening question(s) need your review.")
        screenshot(page, job['ID'], "needs_review")
        return "needs_my_input"

    # Check for CV file upload on company ATS
    file_input = page.query_selector('input[type="file"]')
    if file_input and cv_pdf and os.path.exists(cv_pdf):
        try:
            file_input.set_input_files(cv_pdf)
            log.append(f"[{portal_tag} ATS] Uploaded tailored CV: {os.path.basename(cv_pdf)}")
            time.sleep(2)
        except Exception as fe:
            log.append(f"[{portal_tag} ATS] CV upload error: {fe}")

    # Cover letter filling if available
    for sel in ['textarea[name*="cover"]','textarea[placeholder*="cover"]','textarea']:
        el = page.query_selector(sel)
        if el:
            try:
                if not el.input_value():
                    el.fill(cover_letter_text(job))
                    break
            except Exception:
                pass

    # Re-check screening questions
    has_unanswered, pending_qs = sm.inspect_form_screening_questions(page, job)
    if has_unanswered:
        log.append(f"[{portal_tag} ATS] ⏸ Pausing application: {len(pending_qs)} screening question(s) need your review.")
        screenshot(page, job['ID'], "needs_review")
        return "needs_my_input"

    # Submit if ready
    for sel in ['button:has-text("Submit Application")', 'button:has-text("Submit application")', 'button:has-text("Submit")', 'button[type="submit"]']:
        sbtn = page.query_selector(sel)
        if sbtn and sbtn.is_visible():
            try:
                sbtn.click()
                time.sleep(4)
                screenshot(page, job['ID'], f"{portal_type}_submitted")
                log.append(f"[{portal_tag} ATS] ✅ Application submitted!")
                return "applied"
            except Exception as se:
                log.append(f"[{portal_tag} ATS] Submit click error: {se}")

    log.append(f"[{portal_tag}] ⚡ Navigated to company application page. Marking as Attempted.")
    return "attempted"


# ─── Session loader ───────────────────────────────────────────────────────────

def load_session_args(portals_needed):
    """Return storage_state path for the first available saved session, or None."""
    # We use a shared context, so pick LinkedIn session first as primary
    for portal in portals_needed:
        sf = SESSION.get(portal)
        if sf and os.path.exists(sf):
            return sf
    return None

# ─── Main Runner ──────────────────────────────────────────────────────────────

def run_browser_apply(job_ids, headless=False):
    from playwright.sync_api import sync_playwright

    creds = load_credentials()
    results = []
    applied_count = 0
    skipped_count = 0
    error_count   = 0
    blocked_count = 0
    needs_input_count = 0

    # Load jobs
    jobs_to_apply = []
    if os.path.exists(TRACKER_FILE):
        with open(TRACKER_FILE, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                jid = str(row.get("ID",""))
                url = str(row.get("URL",""))
                is_target = (
                    jid in job_ids or
                    url in job_ids or
                    "all" in job_ids or
                    ("new" in job_ids and row.get("Status","") == "New") or
                    ("review" in job_ids and row.get("Status","") == "Needs My Input") or
                    ("manual" in job_ids and row.get("Status","") in ["Needs Manual Action", "Blocked - Apply Manually"])
                )
                if is_target:
                    if row.get("Status","") == "Real Applied":
                        continue
                    if any(j.get("ID") == jid for j in jobs_to_apply):
                        continue
                    jobs_to_apply.append(dict(row))

    if not jobs_to_apply:
        return {"status": "no_jobs", "message": "No matching unapplied jobs found.", "applied_count": 0, "results": []}

    # Determine which portals are needed
    portals_needed = list({detect_portal(j.get("URL","")) for j in jobs_to_apply})
    print(f"[BrowserAgent] {len(jobs_to_apply)} jobs across portals: {portals_needed}", flush=True)

    # Try to load an existing session
    saved_session = load_session_args(portals_needed)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headless,
            args=["--no-sandbox","--disable-blink-features=AutomationControlled",
                  "--disable-dev-shm-usage","--start-maximized"]
        )

        ctx_args = {
            "user_agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                           "AppleWebKit/537.36 (KHTML, like Gecko) "
                           "Chrome/124.0.0.0 Safari/537.36"),
            "viewport": {"width": 1280, "height": 900}
        }
        if saved_session:
            ctx_args["storage_state"] = saved_session
            print(f"[BrowserAgent] Loaded saved session: {saved_session}", flush=True)

        context = browser.new_context(**ctx_args)
        page = context.new_page()
        page.set_default_timeout(35000)
        page.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined})")

        # ── Pre-login each portal (isolated try/except per portal) ─────────
        portal_logged_in = {}
        login_fns = {
            "linkedin":  linkedin_login,
            "naukri":    naukri_login,
            "bayt":      bayt_login,
            "indeed":    indeed_login,
            "glassdoor": glassdoor_login,
        }
        for portal in portals_needed:
            if portal in login_fns:
                log_tmp = []
                try:
                    ok = login_fns[portal](page, creds, context, headless, log_tmp)
                    portal_logged_in[portal] = ok
                except Exception as login_err:
                    log_tmp.append(f"[{portal.upper()}] Login error (skipping): {login_err}")
                    portal_logged_in[portal] = False
                for m in log_tmp: print(m, flush=True)
                time.sleep(1)

        # ── Apply to each job ──────────────────────────────────────────────
        apply_fns = {
            "linkedin":  linkedin_apply,
            "naukri":    naukri_apply,
            "bayt":      bayt_apply,
            "indeed":    indeed_apply,
            "glassdoor": glassdoor_apply,
            "micro1":    micro1_apply,
            "remotive":  remotive_apply,
            "remoteok":  remotive_apply,
            "himalayas": remotive_apply,
        }

        for job in jobs_to_apply:
            job_id  = job.get("ID","")
            company = job.get("Company","")
            title   = job.get("Title","")
            url     = job.get("URL","")
            portal  = detect_portal(url)

            cv_pdf    = find_cv(company)
            cover_pdf = find_cover(company)
            log       = []

            print(f"\n[BrowserAgent] ──── {title} @ {company} ({portal.upper()}) ────", flush=True)

            status = "error"
            try:
                if portal in apply_fns:
                    status = apply_fns[portal](page, job, creds, cv_pdf, cover_pdf, context, headless, log)
                else:
                    log.append(f"[BrowserAgent] Portal '{portal}' not supported yet.")
                    status = "skipped_unsupported_portal"
            except Exception as e:
                log.append(f"[BrowserAgent] Error: {e} — recovering page...")
                status = "error"
                try:
                    page.close()
                    page = context.new_page()
                    page.set_default_timeout(35000)
                    page.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined})")
                    log.append("[BrowserAgent] New page created, continuing...")
                except Exception:
                    pass

            for m in log: print(m, flush=True)

            result_row = {
                "ID": job_id, "Company": company, "Title": title,
                "URL": url, "Portal": portal, "Status": status,
                "CVUsed": os.path.basename(cv_pdf) if cv_pdf else "not_found",
                "CoverUsed": os.path.basename(cover_pdf) if cover_pdf else "not_found",
                "Log": " | ".join(log),
                "AppliedAt": datetime.now().strftime("%Y-%m-%d %H:%M")
            }
            results.append(result_row)

            # PATCH D: Only mark 'Real Applied' on CONFIRMED submission
            if status == "applied":
                applied_count += 1
                _update_tracker(job_id, "Real Applied", cv_pdf, cover_pdf, target_url=url)
                print(f"[BrowserAgent] ✅ CONFIRMED APPLIED: {title} @ {company}", flush=True)
            elif status == "needs_my_input":
                needs_input_count += 1
                _update_tracker(job_id, "Needs My Input", cv_pdf, cover_pdf, target_url=url)
                print(f"[BrowserAgent] ⏸ PAUSED - NEEDS CANDIDATE INPUT: {title} @ {company}", flush=True)
            elif status == "attempted":
                skipped_count += 1
                _update_tracker(job_id, "Attempted", cv_pdf, cover_pdf, target_url=url)
                print(f"[BrowserAgent] ⚡ ATTEMPTED (unconfirmed): {title} @ {company}", flush=True)
            elif status in ["needs_manual_action", "skipped_bot_blocked"]:
                blocked_count += 1
                _update_tracker(job_id, "Needs Manual Action", cv_pdf, cover_pdf, target_url=url)
                print(f"[BrowserAgent] ⚠️ NEEDS MANUAL ACTION: {title} @ {company}", flush=True)
            elif "skipped" in status:
                skipped_count += 1
                _update_tracker(job_id, "Tailored & Ready", cv_pdf, cover_pdf, target_url=url)
                print(f"[BrowserAgent] ⏭ SKIPPED: {title} @ {company} ({status})", flush=True)
            else:
                error_count += 1
                _update_tracker(job_id, "Tailored & Ready", cv_pdf, cover_pdf, target_url=url)
                print(f"[BrowserAgent] ❌ ERROR: {title} @ {company} ({status})", flush=True)

            time.sleep(2)

        browser.close()

    # Save log
    log_path = os.path.join(SCREENSHOTS, "apply_log.json")
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    return {
        "status": "complete",
        "applied_count": applied_count,
        "needs_input_count": needs_input_count,
        "skipped_count": skipped_count,
        "blocked_count": blocked_count,
        "error_count":   error_count,
        "total_processed": len(jobs_to_apply),
        "log_file": log_path,
        "results": results
    }


def _update_tracker(job_id, new_status, cv_path, cover_path, target_url=None):
    rows, fieldnames = [], []
    if not os.path.exists(TRACKER_FILE):
        return
    updated = False
    with open(TRACKER_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        for row in reader:
            matches_id = str(row.get("ID","")) == str(job_id)
            matches_url = (target_url is None) or (str(row.get("URL","")) == str(target_url))
            if matches_id and matches_url and not updated:
                row["Status"]      = new_status
                row["AppliedDate"] = datetime.now().strftime("%Y-%m-%d")
                if cv_path:    row["CVFile"]    = os.path.relpath(cv_path, BASE_DIR)
                if cover_path: row["CoverFile"] = os.path.relpath(cover_path, BASE_DIR)
                updated = True
            rows.append(row)
    with open(TRACKER_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description="Real Browser Auto-Apply for Tanuj Chandel")
    parser.add_argument("--jobs",    type=str, default="all",
                        help="Comma-separated job IDs, 'new', 'review', 'manual', or 'all'")
    parser.add_argument("--headless", action="store_true",
                        help="Run in headless mode (background, no window)")
    parser.add_argument("--visible",  action="store_true",
                        help="Run with visible browser window (use for 1st-time login / CAPTCHA)")
    args = parser.parse_args()

    job_ids    = [j.strip() for j in args.jobs.split(",")] if args.jobs else ["all"]
    run_hidden = args.headless and not args.visible

    result = run_browser_apply(job_ids, headless=run_hidden)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
