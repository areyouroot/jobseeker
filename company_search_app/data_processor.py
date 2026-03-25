import re

def is_likely_company(name, snippet, link):
    """Filters out non-company results like StackOverflow, Wikipedia articles, and non-corporate entities."""
    exclude_domains = [
        'stackexchange.com', 'stackoverflow.com', 'reddit.com', 'quora.com',
        'github.com', 'wikipedia.org', 'youtube.com', 'facebook.com', 'twitter.com',
        'linkedin.com/posts', 'linkedin.com/news', 'dhs.gov', 'cisa.gov', 'gov.in',
        'en.wikipedia.org', 'wiktionary.org'
    ]
    if any(domain in link.lower() for domain in exclude_domains):
        # Allow Wikipedia if it's specifically a company/corporate page
        if 'wikipedia.org' in link.lower() and ('company' in snippet.lower() or 'corporation' in snippet.lower()):
            return True
        return False

    # Exclude results that look like questions or blog posts
    if any(q in name.lower() for q in ['what is', 'how to', 'difference between', 'best way', '?', 'answer']):
        return False

    # Exclude non-corporate entities like countries or purely administrative offices
    exclude_keywords = [
        'ward office', 'corporation office', 'high commission', 'embassy', 'rto office',
        'meteorological centre', 'telephone exchange', 'research centre', 'school', 'college',
        'university', 'hospital', 'temple', 'church', 'mosque', 'forum', 'bjp', 'congress',
        'head quarters', 'metro water', 'municipality', 'police station', 'railway station'
    ]
    if any(k in name.lower() for k in exclude_keywords):
        return False

    # Heuristic for valid company name (at least 2 letters, not just symbols/numbers)
    if len(re.sub(r'[^a-zA-Z]', '', name)) < 2:
        return False

    return True

def classify_company_size(snippet, name):
    """
    Estimates company size based on snippets and name clues.
    Classification: Startup (<=100), Company (>100), MNC (>1000).
    """
    snippet_lower = snippet.lower()
    name_lower = name.lower()

    # Heuristics for MNC
    mnc_keywords = ['mnc', 'multinational', 'fortune 500', 'global presence', 'offices in', 'worldwide', 'globally']
    if any(k in snippet_lower for k in mnc_keywords):
        return "MNC"

    # Common large MNC names
    known_mncs = ['tcs', 'tata consultancy', 'infosys', 'wipro', 'hcl', 'accenture', 'cognizant', 'ibm', 'amazon', 'google', 'microsoft', 'capgemini', 'oracle', 'dell', 'hp', 'reliance', 'jio']
    if any(k in name_lower for k in known_mncs):
        return "MNC"

    # Regex to find employee counts if mentioned
    emp_match = re.search(r'(\d{1,3}(?:,\d{3})*)\+?\s*(?:employees|people|staff)', snippet_lower)
    if emp_match:
        count_str = emp_match.group(1).replace(',', '')
        count = int(count_str)
        if count > 1000:
            return "MNC"
        elif count > 100:
            return "Company"
        else:
            return "Startup"

    # Fallback heuristics
    if "startup" in snippet_lower or "funded" in snippet_lower or "venture" in snippet_lower:
        return "Startup"

    # Default to 'Company' if not enough info, or 'Startup' for unknown small looking ones
    # For this task, we will mark it as 'Company' as a safe middle ground if unsure.
    return "Company"

def extract_sector(snippet, name):
    """Extracts the sector from snippet or name."""
    snippet_lower = snippet.lower()
    name_lower = name.lower()

    sectors = {
        'IT Services': ['it services', 'software', 'technology', 'app development', 'web development', 'saas', 'cloud', 'digital', 'systems'],
        'Fintech': ['fintech', 'finance', 'banking', 'payment', 'lending', 'investment', 'capital'],
        'Hardware': ['hardware', 'electronics', 'semiconductor', 'manufacturing', 'circuits'],
        'Cybersecurity': ['cybersecurity', 'security', 'infosec', 'network security', 'threat'],
        'Electric/Energy': ['electric', 'ev', 'energy', 'solar', 'lpg', 'power', 'fuel'],
        'Business/Consulting': ['business', 'consulting', 'management', 'solutions', 'advisory'],
        'Logistics': ['logistics', 'supply chain', 'delivery', 'transportation']
    }

    for sector, keywords in sectors.items():
        if any(k in snippet_lower for k in keywords) or any(k in name_lower for k in keywords):
            return sector

    return "Others"

def clean_url(url):
    """Simple URL cleaner."""
    if not url:
        return ""
    if "google.com/url?q=" in url:
        url = url.split("?q=")[1].split("&")[0]
    return url

def process_results(results):
    """Deduplicates and processes raw search results."""
    processed = {}
    for r in results:
        name = r['name']
        link = clean_url(r['link'])
        snippet = r['snippet']

        if not is_likely_company(name, snippet, link):
            continue

        # Very basic normalization
        norm_name = re.sub(r'[^a-zA-Z0-9]', '', name).lower()

        if norm_name not in processed:
            processed[norm_name] = {
                'Company Name': name,
                'Company Website': link,
                'Sector': extract_sector(snippet, name),
                'Type': classify_company_size(snippet, name),
                'Source': r['source'],
                'Snippet': snippet
            }
        else:
            # If we already have it, maybe append source
            if r['source'] not in processed[norm_name]['Source']:
                processed[norm_name]['Source'] += f", {r['source']}"

    return list(processed.values())
