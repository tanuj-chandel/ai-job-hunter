#!/usr/bin/env python3
"""
FitScore Conversion & Outcome Analytics Report
Analyzes job application response rates and outcomes by FitScore bands.
"""

import os
import sys
import io
import csv

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TRACKER_FILE = os.path.join(BASE_DIR, "job_search_tracker.csv")

BANDS = [
    {"name": "High Fit (85% - 100%)",  "min": 85, "max": 100, "label": "High"},
    {"name": "Medium Fit (70% - 84%)","min": 70, "max": 84,  "label": "Medium"},
    {"name": "Low Fit (< 70%)",        "min": 0,  "max": 69,  "label": "Low"},
]

def load_data():
    if not os.path.exists(TRACKER_FILE):
        print(f"[Error] Tracker file not found: {TRACKER_FILE}", file=sys.stderr)
        return []
    records = []
    with open(TRACKER_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(row)
    return records

def parse_score(val):
    try:
        return int(float(str(val).strip()))
    except (ValueError, TypeError):
        return 0

def compute_analytics():
    records = load_data()
    if not records:
        return None

    # Initialize stats per band
    stats = {
        b["name"]: {
            "min": b["min"],
            "max": b["max"],
            "label": b["label"],
            "tracked": 0,
            "applied": 0,
            "pending": 0,
            "responses": 0,
            "interviews": 0,
            "offers": 0,
            "rejections": 0,
        }
        for b in BANDS
    }

    total_tracked = len(records)
    total_applied = 0
    total_responses = 0
    total_interviews = 0
    total_offers = 0
    total_rejections = 0

    for r in records:
        score = parse_score(r.get("FitScore", 0))
        status = (r.get("Status") or "").strip()
        resp = (r.get("ResponseReceived") or "").strip().lower()
        interview = (r.get("InterviewScheduled") or "").strip().lower()
        outcome = (r.get("Outcome") or "").strip().lower()

        is_applied = status in ["Real Applied", "Attempted", "Applied"]

        # Assign to band
        matched_band = None
        for b in BANDS:
            if b["min"] <= score <= b["max"]:
                matched_band = b["name"]
                break
        if not matched_band:
            matched_band = BANDS[-1]["name"]

        band_stat = stats[matched_band]
        band_stat["tracked"] += 1

        if is_applied:
            band_stat["applied"] += 1
            total_applied += 1

            if resp == "yes":
                band_stat["responses"] += 1
                total_responses += 1
            elif resp == "pending" or not resp:
                band_stat["pending"] += 1

            if interview == "yes" or outcome == "interview":
                band_stat["interviews"] += 1
                total_interviews += 1

            if outcome == "offer":
                band_stat["offers"] += 1
                total_offers += 1
            elif outcome == "rejected":
                band_stat["rejections"] += 1
                total_rejections += 1

    for b in BANDS:
        s = stats[b["name"]]
        s["responseRate"] = round((s["responses"] / s["applied"] * 100), 1) if s["applied"] > 0 else 0.0
        s["interviewRate"] = round((s["interviews"] / s["applied"] * 100), 1) if s["applied"] > 0 else 0.0

    overall_resp_rate = round((total_responses / total_applied * 100), 1) if total_applied > 0 else 0.0
    overall_int_rate = round((total_interviews / total_applied * 100), 1) if total_applied > 0 else 0.0

    return {
        "bands": stats,
        "bandList": [stats[b["name"]] for b in BANDS],
        "totalTracked": total_tracked,
        "totalApplied": total_applied,
        "totalPending": total_applied - total_responses,
        "totalResponses": total_responses,
        "totalInterviews": total_interviews,
        "totalOffers": total_offers,
        "totalRejections": total_rejections,
        "overallResponseRate": overall_resp_rate,
        "overallInterviewRate": overall_int_rate,
    }

def generate_report():
    data = compute_analytics()
    if not data:
        print("No job records found to analyze.")
        return

    stats = data["bands"]
    total_tracked = data["totalTracked"]
    total_applied = data["totalApplied"]
    total_responses = data["totalResponses"]
    total_interviews = data["totalInterviews"]
    total_offers = data["totalOffers"]

    # Render Report
    print("=" * 86)
    print(" 📊 FITSCORE RESPONSE RATE & CONVERSION ANALYTICS REPORT")
    print(f" Source: {os.path.basename(TRACKER_FILE)} | Total Records: {total_tracked}")
    print("=" * 86)

    header = f"{'FitScore Band':<24} | {'Tracked':<8} | {'Applied':<8} | {'Pending':<8} | {'Responses':<10} | {'Resp Rate':<10} | {'Interviews':<10}"
    print(header)
    print("-" * 86)

    for b in BANDS:
        s = stats[b["name"]]
        resp_rate = f"{s['responseRate']:.1f}%" if s['applied'] > 0 else "N/A (0)"
        int_rate = f"{s['interviews']} ({s['interviewRate']:.1f}%)" if s['applied'] > 0 else "0 (0.0%)"
        print(f"{b['name']:<24} | {s['tracked']:<8} | {s['applied']:<8} | {s['pending']:<8} | {s['responses']:<10} | {resp_rate:<10} | {int_rate:<10}")

    print("-" * 86)
    overall_resp_rate = f"{data['overallResponseRate']:.1f}%"
    overall_int_rate = f"{total_interviews} ({data['overallInterviewRate']:.1f}%)" if total_applied > 0 else "0 (0.0%)"
    print(f"{'OVERALL TOTALS':<24} | {total_tracked:<8} | {total_applied:<8} | {data['totalPending']:<8} | {total_responses:<10} | {overall_resp_rate:<10} | {overall_int_rate:<10}")
    print("=" * 86)

    # Key Observations & Status Notes
    print("\n🔍 KEY OBSERVATIONS & PIPELINE STATUS:")
    print(f" • Total Real Applied Submissions: {total_applied}")
    print(f" • Pending Review (No response yet): {data['totalPending']} applications")
    print(f" • Confirmed Recruiter Responses: {total_responses}")
    print(f" • Interviews Scheduled: {total_interviews}")
    print(f" • Confirmed Offers: {total_offers}")

    if total_applied > 0 and total_responses == 0:
        print("\n💡 NOTE: All currently applied roles are in 'Pending' status (applied recently).")
        print("  As recruiter responses arrive via email or portal, update `ResponseReceived` to 'Yes'")
        print("  and `InterviewScheduled` to 'Yes' in `job_search_tracker.csv` to track live conversion.\n")

if __name__ == "__main__":
    generate_report()
