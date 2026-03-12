import csv
import time
from playwright.sync_api import sync_playwright

def search_companies():
    # Searching for tech, fintech, and IT companies near Pattur, Mangadu.
    # The search query will naturally restrict to the area.

    queries = [
        "tech companies near Pattur, Mangadu",
        "fintech companies near Pattur, Mangadu",
        "IT companies near Pattur, Mangadu"
    ]

    companies = []
    seen = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for query in queries:
            print(f"Searching for: {query}")
            url = f"https://www.google.com/maps/search/{query.replace(' ', '+')}"
            page.goto(url)

            # Wait for results to load
            page.wait_for_timeout(5000)

            # Scroll down to load more results
            for _ in range(10):
                page.mouse.wheel(0, 1000)
                page.wait_for_timeout(2000)

            # Extract company elements
            links = page.locator('a[href*="/maps/place/"]').element_handles()

            for link in links:
                try:
                    name = link.get_attribute('aria-label')
                    href = link.get_attribute('href')
                    if name and name not in seen:
                        seen.add(name)
                        companies.append({'name': name, 'url': href, 'category': query.split(' ')[0]})
                except Exception as e:
                    pass

        browser.close()

    print(f"Found {len(companies)} companies.")

    with open('companies.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['name', 'category', 'url'])
        writer.writeheader()
        writer.writerows(companies)

if __name__ == '__main__':
    search_companies()
