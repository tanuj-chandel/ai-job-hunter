#!/usr/bin/env python3
"""
Screening Question Manager & Human-in-the-Loop Review System
Handles detection, logging, caching, and review of job application screening questions.
"""

import os
import sys
import csv
import json
import re
import hashlib
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PENDING_CSV = os.path.join(BASE_DIR, "pending_review_questions.csv")
CACHE_FILE = os.path.join(BASE_DIR, "answered_questions_cache.json")

CSV_FIELDS = [
    "QuestionID",
    "JobID",
    "Company",
    "Title",
    "QuestionText",
    "QuestionType",
    "Options",
    "Answer",
    "SuggestedAnswer",
    "Status",
    "CreatedAt",
    "AnsweredAt"
]

# Standard profile field keywords that should NOT be treated as screening questions
STANDARD_FIELD_KEYWORDS = [
    "first name", "firstname", "last name", "lastname", "full name", "fullname",
    "email", "phone", "mobile", "telephone", "city", "state", "postal", "zip",
    "address", "resume", "cv", "cover letter", "headline", "summary",
    "upload", "attach", "file", "photo"
]

def normalize_text(text):
    """Normalize question text for comparison and caching."""
    if not text:
        return ""
    t = text.lower().strip()
    t = re.sub(r'[\r\n\t]+', ' ', t)
    t = re.sub(r'[*?:;,.\-_/\\()\[\]"]+', ' ', t)
    return re.sub(r'\s+', ' ', t).strip()

def make_qid(job_id, question_text):
    norm = normalize_text(question_text)
    h = hashlib.md5(f"{job_id}_{norm}".encode('utf-8')).hexdigest()[:10]
    return f"q_{h}"

def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_cache(cache_data):
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[ScreeningManager] Error saving cache: {e}", file=sys.stderr)

def get_cached_suggestion(question_text):
    """Return prior answer suggestion if matching or highly similar question was answered before."""
    norm = normalize_text(question_text)
    if not norm:
        return ""
    cache = load_cache()

    # Exact normalized match
    if norm in cache:
        return cache[norm].get("answer", "")

    # Fuzzy / token subset match
    words = set(norm.split())
    if len(words) >= 3:
        for cached_norm, data in cache.items():
            cached_words = set(cached_norm.split())
            intersection = words.intersection(cached_words)
            similarity = len(intersection) / max(len(words), len(cached_words))
            if similarity >= 0.75:
                return data.get("answer", "")

    return ""

def init_csv():
    if not os.path.exists(PENDING_CSV):
        with open(PENDING_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
            writer.writeheader()

def get_job_questions(job_id):
    """Get all questions logged for a specific job."""
    init_csv()
    rows = []
    with open(PENDING_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            if r.get("JobID") == str(job_id):
                rows.append(r)
    return rows

def get_approved_answers(job_id):
    """Return dict of {normalized_question: answer} for questions with Status='Answered' for this job."""
    questions = get_job_questions(job_id)
    answers = {}
    for q in questions:
        if q.get("Status") == "Answered" and q.get("Answer"):
            answers[normalize_text(q.get("QuestionText",""))] = q.get("Answer","")
    return answers

def log_pending_question(job_id, company, title, question_text, question_type="text", options=""):
    """Log an unanswered screening question to pending_review_questions.csv."""
    init_csv()
    clean_q = question_text.strip()
    if not clean_q:
        return None

    qid = make_qid(job_id, clean_q)
    existing_rows = []
    found = False

    with open(PENDING_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            if r.get("QuestionID") == qid:
                found = True
            existing_rows.append(r)

    if not found:
        suggested = get_cached_suggestion(clean_q)
        new_row = {
            "QuestionID": qid,
            "JobID": str(job_id),
            "Company": company,
            "Title": title,
            "QuestionText": clean_q,
            "QuestionType": question_type,
            "Options": options,
            "Answer": "",
            "SuggestedAnswer": suggested,
            "Status": "Pending",
            "CreatedAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "AnsweredAt": ""
        }
        existing_rows.append(new_row)
        with open(PENDING_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
            writer.writeheader()
            writer.writerows(existing_rows)
        return new_row

    return None

def record_answer(qid, answer_text):
    """Record user's verified answer for a question and update cache."""
    init_csv()
    rows = []
    updated = False
    norm_q = ""

    with open(PENDING_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            if r.get("QuestionID") == qid:
                r["Answer"] = answer_text.strip()
                r["Status"] = "Answered"
                r["AnsweredAt"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                updated = True
                norm_q = normalize_text(r.get("QuestionText",""))
            rows.append(r)

    if updated:
        with open(PENDING_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
            writer.writeheader()
            writer.writerows(rows)

        # Update cache for future suggestions
        if norm_q and answer_text.strip():
            cache = load_cache()
            prior = cache.get(norm_q, {})
            cache[norm_q] = {
                "answer": answer_text.strip(),
                "last_used": datetime.now().strftime("%Y-%m-%d"),
                "times_used": prior.get("times_used", 0) + 1
            }
            save_cache(cache)
        return True

    return False

def is_standard_field(label_or_name):
    norm = normalize_text(label_or_name)
    return any(std in norm for std in STANDARD_FIELD_KEYWORDS)

def inspect_form_screening_questions(page, job):
    """
    Scans the active page/modal for non-standard screening questions (free text, textarea, select, radio).
    Returns (has_unanswered: bool, pending_list: list).
    If an answered entry exists in pending_review_questions.csv for this job, fills it automatically.
    """
    job_id = job.get("ID", "")
    company = job.get("Company", "")
    title = job.get("Title", "")

    approved_answers = get_approved_answers(job_id)
    unanswered_detected = []

    # 1. Inspect text inputs & textareas
    elements = page.query_selector_all('input[type="text"], input[type="number"], input:not([type]), textarea')
    for el in elements:
        try:
            if not el.is_visible():
                continue

            # Skip standard contact & cover fields
            name_attr = (el.get_attribute("name") or el.get_attribute("id") or "").lower()
            placeholder = (el.get_attribute("placeholder") or "").lower()
            aria_label = (el.get_attribute("aria-label") or "").lower()

            if is_standard_field(f"{name_attr} {placeholder} {aria_label}"):
                continue

            # Find question label text
            q_text = ""
            # Try linked label by id
            el_id = el.get_attribute("id")
            if el_id:
                lbl = page.query_selector(f'label[for="{el_id}"]')
                if lbl and lbl.is_visible():
                    q_text = lbl.inner_text().strip()

            # Try parent / preceding container label
            if not q_text:
                q_text = page.evaluate("""(el) => {
                    let parent = el.closest('div, fieldset, li, section');
                    if (!parent) return '';
                    let labels = parent.querySelectorAll('label, legend, span, p, h3, h4');
                    for (let l of labels) {
                        let txt = (l.textContent || '').trim();
                        if (txt.length > 5 && txt.length < 250 && !txt.includes('optional') && !txt.includes('Resume')) {
                            return txt;
                        }
                    }
                    return '';
                }""", el) or ""

            if not q_text:
                q_text = aria_label or placeholder or name_attr

            if not q_text or is_standard_field(q_text):
                continue

            norm_q = normalize_text(q_text)

            # Check if candidate has approved an answer for this question
            if norm_q in approved_answers:
                approved_val = approved_answers[norm_q]
                if not el.input_value():
                    el.fill(approved_val)
            else:
                # Needs candidate review
                q_type = "textarea" if el.evaluate("e => e.tagName.toLowerCase() == 'textarea'") else "text"
                logged = log_pending_question(job_id, company, title, q_text, question_type=q_type)
                unanswered_detected.append({
                    "question": q_text,
                    "type": q_type,
                    "element": el
                })
        except Exception:
            pass

    # 2. Inspect Select dropdowns
    selects = page.query_selector_all('select')
    for sel in selects:
        try:
            if not sel.is_visible():
                continue
            name_attr = (sel.get_attribute("name") or sel.get_attribute("id") or "").lower()
            if is_standard_field(name_attr):
                continue

            q_text = ""
            el_id = sel.get_attribute("id")
            if el_id:
                lbl = page.query_selector(f'label[for="{el_id}"]')
                if lbl and lbl.is_visible():
                    q_text = lbl.inner_text().strip()
            if not q_text:
                q_text = sel.evaluate("""(el) => {
                    let parent = el.closest('div, fieldset, li');
                    if (!parent) return '';
                    let l = parent.querySelector('label, legend, span');
                    return l ? l.textContent.trim() : '';
                }""") or name_attr

            if not q_text or is_standard_field(q_text):
                continue

            norm_q = normalize_text(q_text)
            options = [opt.inner_text().strip() for opt in sel.query_selector_all('option') if opt.inner_text().strip()]
            options_str = " | ".join(options[:10])

            if norm_q in approved_answers:
                approved_val = approved_answers[norm_q]
                sel.select_option(label=approved_val)
            else:
                log_pending_question(job_id, company, title, q_text, question_type="select", options=options_str)
                unanswered_detected.append({
                    "question": q_text,
                    "type": "select",
                    "options": options_str
                })
        except Exception:
            pass

    # 3. Inspect Radio Button groups
    radio_groups = {}
    for r in page.query_selector_all('input[type="radio"]'):
        try:
            if not r.is_visible():
                continue
            gname = r.get_attribute("name")
            if gname:
                radio_groups.setdefault(gname, []).append(r)
        except Exception:
            pass

    for gname, radios in radio_groups.items():
        try:
            if is_standard_field(gname):
                continue
            # Extract question text from fieldset/legend
            q_text = page.evaluate("""(el) => {
                let parent = el.closest('fieldset, div, li');
                if (!parent) return '';
                let legend = parent.querySelector('legend, label, p, span');
                return legend ? legend.textContent.trim() : '';
            }""", radios[0]) or gname

            if not q_text or is_standard_field(q_text):
                continue

            norm_q = normalize_text(q_text)
            opts = []
            for rb in radios:
                rb_lbl = page.evaluate("""(el) => {
                    let p = el.parentElement;
                    return p ? p.textContent.trim() : (el.value || '');
                }""", rb)
                if rb_lbl:
                    opts.append(rb_lbl)
            options_str = " | ".join(opts)

            if norm_q in approved_answers:
                approved_val = approved_answers[norm_q]
                for rb in radios:
                    rb_val = (rb.get_attribute("value") or "").lower()
                    parent_text = (rb.evaluate("e => e.parentElement ? e.parentElement.textContent : ''") or "").lower()
                    if approved_val.lower() in rb_val or approved_val.lower() in parent_text:
                        rb.check()
                        break
            else:
                log_pending_question(job_id, company, title, q_text, question_type="radio", options=options_str)
                unanswered_detected.append({
                    "question": q_text,
                    "type": "radio",
                    "options": options_str
                })
        except Exception:
            pass

    return (len(unanswered_detected) > 0, unanswered_detected)
