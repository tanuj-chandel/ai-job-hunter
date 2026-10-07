from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    # Test Micro1 job page
    m1_url = "https://jobs.micro1.ai/post/90990ebf-8198-4b79-a799-add474453dbb"
    print("Testing Micro1 job page:", m1_url)
    try:
        page.goto(m1_url, timeout=30000)
        page.wait_for_timeout(4000)
        print("Micro1 Page Title:", page.title())
        buttons = page.query_selector_all('button, a[href*="apply"], a.btn')
        print(f"Buttons found: {len(buttons)}")
        for b in buttons[:5]:
            print("  Btn:", b.inner_text().strip(), "href:", b.get_attribute('href'))
    except Exception as e:
        print("Micro1 error:", e)

    # Test Remotive job page
    rem_url = "https://remotive.com/remote-jobs/all-others/content-reviewer-united-states-2091144"
    print("\nTesting Remotive job page:", rem_url)
    try:
        page.goto(rem_url, timeout=30000)
        page.wait_for_timeout(4000)
        print("Remotive Page Title:", page.title())
        apply_links = page.query_selector_all('a[href*="apply"], a:has-text("Apply"), button:has-text("Apply")')
        print(f"Apply links found: {len(apply_links)}")
        for b in apply_links[:5]:
            print("  Apply link:", b.inner_text().strip(), "href:", b.get_attribute('href'))
    except Exception as e:
        print("Remotive error:", e)

    browser.close()
