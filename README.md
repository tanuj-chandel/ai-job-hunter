# AI Job Hunter — Discovery, Fit Scoring, Tailored CVs and Verified Applications

A personal job-search pipeline that scrapes job portals and remote-work APIs, scores each posting against my profile, generates a company-specific LaTeX CV and cover letter, and tracks every application with a strict "only count it if the confirmation page was seen" rule.

Built on top of [MadsLorentzen/ai-job-search](https://github.com/MadsLorentzen/ai-job-search) (MIT), which provides the Claude Code skill structure and portal CLI pattern. Everything in the root directory — the Indian/remote portal scrapers, fit scoring, browser apply agent, verification layer, dashboard and tracker tooling — is my own work, built with AI-assisted development tools and run daily since mid-2026.

> **Status:** In daily use. 146 postings tracked; 112 with tailored CV + cover letter generated; 18 verified real applications. Auto-apply is used sparingly; the default workflow is discover → score → generate documents → apply manually.

<!-- Replace with a real screenshot of dashboard.html -->
![Job Hunter dashboard](docs/dashboard.png)

## How it works

1. **Discover** — `easy_apply_scraper.py` and `scrape_naukri_jobs.py` pull postings from Naukri, LinkedIn, Indeed, Bayt, Glassdoor (Playwright) and from RemoteOK, Remotive and Himalayas (REST). Search terms are configured for AI Evaluator / Trainer / Prompt Engineer / RLHF roles plus operations leadership.
2. **Score** — `fit_score()` assigns 0–100 using weighted keyword tiers on the job title (high-fit terms like "AI evaluator", "prompt engineer", "operations lead"; medium like "annotation", "analytics"; disqualifiers like "driver", "telecaller"). ≥85 → apply queue, 70–84 → review, <70 → dropped. It is a deliberate heuristic, not a semantic model; it's fast, transparent, and easy to tune.
3. **Generate** — `generate_all_cv_packages.py` fills a `moderncv` LaTeX template per company and compiles PDF CV + cover letter with `lualatex`. `finalize_cv_links.py` records the paths in the tracker.
4. **Apply** — `browser_apply_agent.py` (Playwright, headless or visible) fills forms and uploads documents. CAPTCHAs and multi-step screeners are never bypassed; they're screenshotted and routed to `needs_manual_apply.csv` for me.
5. **Verify** — An application is marked `Real Applied` only when a confirmation screen is captured. Everything else stays `Attempted` or `Needs Manual Action`. `reset_phantom_applied.py` exists because the first version over-counted — the fix was to make the tracker pessimistic by default.
6. **Track & review** — `job_search_tracker.csv` is the source of truth; `dashboard.html` (served by `start_dashboard.py` on :8080) shows pipeline analytics; `check_responses.py` and `screening_manager.py` handle follow-ups and recruiter screening questions.

## Stack

Python 3.12 · Playwright · Requests · LaTeX (moderncv, lualatex) · CSV/SQLite · vanilla HTML/JS dashboard · Windows Task Scheduler for the daily run

## Run it

```bash
pip install -r requirements.txt
playwright install chromium
cp credentials.env.example credentials.env     # your details + portal logins; never commit
python auto_daily_job_search.py                # scrape + score + generate documents
python start_dashboard.py                      # http://localhost:8080/dashboard.html
python browser_apply_agent.py --visible        # apply with a visible browser you can watch
```

## What I'd tell a reviewer

- **Portal automation is against most portals' terms.** Logging into LinkedIn or Naukri with a bot can get the account restricted. That's why the agent has a visible mode, never solves CAPTCHAs, and why I apply manually for anything I actually care about. The tool's real value is discovery and document generation, not clicking Submit.
- **The fit score is a keyword heuristic.** I called it "semantic" in an early spec; it isn't. A title-based tiered keyword score catches 90% of what matters for my search and I can explain every decision it makes. An embedding-based scorer is on the roadmap but hasn't been needed.
- **Tracker hygiene is most of the work.** Half the scripts in this repo exist to clean URLs, dedupe, reset bad states and migrate columns. That's what a real pipeline looks like after two months of daily use.

## Roadmap

- [ ] Replace keyword fit score with embedding similarity against my profile text
- [ ] Move tracker from CSV to SQLite with proper migrations
- [ ] Separate the generic framework from my personal configuration so others can fork it

## Author

Tanuj Chandel · [LinkedIn](https://www.linkedin.com/in/tanuj-chandel-53373221/) · [GitHub](https://github.com/tanuj-chandel)
