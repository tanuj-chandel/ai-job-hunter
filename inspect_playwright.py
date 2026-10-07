import json, time, re
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    # 1. Turing Jobs
    print("Fetching Turing.com jobs via Playwright...")
    try:
        page.goto("https://www.turing.com/jobs", timeout=40000)
        time.sleep(5)
        # Search for AI or Trainer
        cards = page.query_selector_all('a[href*="/jobs/"]')
        print(f"Turing links with /jobs/: {len(cards)}")
        for c in cards[:10]:
            title = c.inner_text().strip().replace('\n', ' - ')
            href = c.get_attribute('href')
            print(f"  Turing: {title[:60]} -> {href}")
    except Exception as e:
        print("Turing error:", e)

    # 2. Micro1
    print("\nFetching Micro1 jobs via Playwright...")
    try:
        page.goto("https://www.micro1.ai/jobs", timeout=40000)
        time.sleep(5)
        links = page.query_selector_all('a')
        print(f"Micro1 total links: {len(links)}")
        for l in links:
            t = l.inner_text().strip().replace('\n', ' ')
            h = l.get_attribute('href') or ""
            if any(k in t.lower() for k in ['ai', 'engineer', 'trainer', 'evaluator', 'developer', 'prompt']) or 'apply' in h.lower():
                print(f"  Micro1: {t[:60]} -> {h}")
    except Exception as e:
        print("Micro1 error:", e)

    browser.close()
