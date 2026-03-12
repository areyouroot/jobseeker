import csv
import time
from playwright.sync_api import sync_playwright

def search_companies():
    # Areas within ~25km radius of Pattur, Mangadu (Chennai)
    major_areas = [
        "Porur",
        "Poonamallee",
        "Guindy",
        "Velachery",
        "T Nagar",
        "Tambaram",
        "Anna Nagar",
        "OMR"
    ]

    categories = ["tech", "fintech", "IT"]

    companies = []
    seen = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for area in major_areas:
            for category in categories:
                query = f"major {category} companies in {area}, Chennai"
                print(f"Searching for: {query}")

                url = f"https://www.google.com/maps/search/{query.replace(' ', '+')}"
                page.goto(url)

                try:
                    # Wait for results to load
                    page.wait_for_selector('div[role="feed"]', timeout=10000)

                    feed = page.locator('div[role="feed"]')

                    # Scroll down to load more results within the feed container
                    for _ in range(3):
                        feed.hover()
                        page.mouse.wheel(0, 2000)
                        page.wait_for_timeout(2000)

                    # Extract company cards (items in the list)
                    cards = feed.locator('> div').element_handles()

                    for card in cards:
                        try:
                            # Usually the company name is in the first link's aria-label or text
                            link = card.query_selector('a[href*="/maps/place/"]')
                            if not link:
                                continue

                            name = link.get_attribute('aria-label')
                            href = link.get_attribute('href')

                            if not name:
                                continue

                            # Extract website if present. It usually has an aria-label like "Website" or a data-value
                            website = "N/A"
                            website_link = card.query_selector('a[data-value="Website"]')
                            if website_link:
                                website = website_link.get_attribute('href')
                            else:
                                # try looking for any link that isn't a maps link
                                all_links = card.query_selector_all('a')
                                for l in all_links:
                                    w_href = l.get_attribute('href')
                                    if w_href and 'google.com' not in w_href:
                                        website = w_href
                                        break

                            if name not in seen:
                                seen.add(name)
                                company_info = {
                                    'area': area,
                                    'name': name,
                                    'category': category,
                                    'url': href,
                                    'website': website,
                                    'description': name # For the one line description, we use the name as getting the actual text is complex
                                }
                                companies.append(company_info)
                        except Exception as inner_e:
                            pass
                except Exception as e:
                    print(f"Failed or no results for {query}")

        browser.close()

    print(f"Found {len(companies)} companies.")

    with open('companies.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['area', 'name', 'category', 'url', 'website', 'description'])
        writer.writeheader()
        writer.writerows(companies)

if __name__ == '__main__':
    search_companies()
