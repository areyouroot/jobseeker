from duckduckgo_search import DDGS
from playwright.sync_api import sync_playwright
import time
import requests

def search_duckduckgo(query, max_results=20):
    """Searches DuckDuckGo and returns a list of results."""
    results = []
    try:
        with DDGS() as ddgs:
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
    results = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            page.goto(f"https://www.google.com/search?q={query}", timeout=60000)

            try:
                page.wait_for_selector("div.g", timeout=5000)
            except:
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

def search_overpass(lat, lon, radius_meters=10000):
    """
    Search for companies and offices using OpenStreetMap Overpass API.
    """
    query = f"""
    [out:json][timeout:90];
    (
      node["office"](around:{radius_meters},{lat},{lon});
      way["office"](around:{radius_meters},{lat},{lon});
      relation["office"](around:{radius_meters},{lat},{lon});
      node["company"](around:{radius_meters},{lat},{lon});
      way["company"](around:{radius_meters},{lat},{lon});
      relation["company"](around:{radius_meters},{lat},{lon});
      node["industrial"](around:{radius_meters},{lat},{lon});
      way["industrial"](around:{radius_meters},{lat},{lon});
      relation["industrial"](around:{radius_meters},{lat},{lon});
      node["business"](around:{radius_meters},{lat},{lon});
      way["business"](around:{radius_meters},{lat},{lon});
      relation["business"](around:{radius_meters},{lat},{lon});
    );
    out body;
    >;
    out skel qt;
    """
    url = "https://overpass-api.de/api/interpreter"
    try:
        response = requests.get(url, params={'data': query})
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Overpass error: {e}")
    return None
