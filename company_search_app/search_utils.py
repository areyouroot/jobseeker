from duckduckgo_search import DDGS
from playwright.sync_api import sync_playwright
import time
import random

def search_duckduckgo(query, max_results=20):
    """Searches DuckDuckGo and returns a list of results."""
    results = []
    try:
        with DDGS() as ddgs:
            # Simplified search to avoid being blocked or getting no results
            ddgs_results = ddgs.text(query, max_results=max_results)
            for r in ddgs_results:
                results.append({
                    'name': r.get('title'),
                    'link': r.get('href'),
                    'snippet': r.get('body'),
                    'source': 'DuckDuckGo'
                })
    except Exception as e:
        print(f"Error searching DuckDuckGo: {e}")
    return results

def search_google_playwright(query, max_results=10):
    """Searches Google using Playwright and returns a list of results."""
    # Google often blocks automated scripts with CAPTCHAs.
    # We will try, but return empty list if it fails.
    results = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            page.goto(f"https://www.google.com/search?q={query}", timeout=60000)

            # Try to wait for results, but don't hang if CAPTCHA appears
            try:
                page.wait_for_selector("div.g", timeout=5000)
            except:
                print(f"Google search blocked or no results for: {query}")
                browser.close()
                return results

            search_results = page.query_selector_all("div.g")
            for i, result in enumerate(search_results):
                if i >= max_results:
                    break

                title_el = result.query_selector("h3")
                link_el = result.query_selector("a")
                snippet_el = result.query_selector("div.VwiC3b")

                if title_el and link_el:
                    results.append({
                        'name': title_el.inner_text(),
                        'link': link_el.get_attribute("href"),
                        'snippet': snippet_el.inner_text() if snippet_el else "",
                        'source': 'Google'
                    })

            browser.close()
    except Exception as e:
        print(f"Error searching Google via Playwright: {e}")
    return results

if __name__ == "__main__":
    # Quick test
    test_query = "IT companies in Porur Chennai"
    print(f"Testing DDG search for: {test_query}")
    ddg_res = search_duckduckgo(test_query, max_results=5)
    for r in ddg_res:
        print(f"- {r['name']} ({r['link']})")

    print(f"\nTesting Google search for: {test_query}")
    google_res = search_google_playwright(test_query, max_results=5)
    for r in google_res:
        print(f"- {r['name']} ({r['link']})")
