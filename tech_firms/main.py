import pandas as pd
import os
import re
import time
import requests
from search_utils import search_duckduckgo, search_google_playwright, search_overpass
from data_processor import classify_company_size, extract_sector, clean_url, is_likely_company

def main():
    print("Aggressive data collection for Chennai tech firms...")

    output_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(output_dir, "chennai_tech_firms.csv")

    seen_names = set()
    processed_results = []

    if os.path.exists(output_path):
        try:
            existing_df = pd.read_csv(output_path)
            processed_results = existing_df.to_dict('records')
            for r in processed_results:
                name = str(r.get('Company Name', ''))
                if name and name != 'nan':
                    seen_names.add(re.sub(r'[^a-zA-Z0-9]', '', name).lower())
            print(f"Loaded {len(processed_results)} existing records.")
        except: pass

    # Multi-term Alphabetical expansion
    # This phase aims to fill the gap to 1000
    if len(processed_results) < 1000:
        print("Starting Alphabetical Sector Search...")
        terms = ["IT", "Software", "Fintech", "Consulting", "Startup", "MNC", "Enterprise", "Digital", "Tech", "BPO", "Financial", "Services", "Solutions", "Systems", "Technologies", "Interactive", "Creative", "Cloud", "Data", "Security", "Network", "Engineering", "Analytics", "Web", "Mobile", "App"]

        for term in terms:
            if len(processed_results) >= 1100: break
            print(f"  Term: {term}...")
            for char in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
                if len(processed_results) >= 1100: break
                q = f"{term} Chennai starting with {char} list website"
                try:
                    res = search_duckduckgo(q, max_results=100)
                    for r in res:
                        name = r['name']
                        link = clean_url(r['link'])
                        if not name or not link: continue
                        if not is_likely_company(name, r['snippet'], link): continue

                        norm_name = re.sub(r'[^a-zA-Z0-9]', '', name).lower()
                        if norm_name not in seen_names:
                            seen_names.add(norm_name)
                            sector = extract_sector(r['snippet'], name)
                            if sector == "Others": sector = term
                            processed_results.append({
                                'Company Name': name,
                                'Company Website': link,
                                'Company Location': "Chennai",
                                'Sector': sector,
                                'Classification': classify_company_size(r['snippet'], name),
                                'Source': 'DuckDuckGo'
                            })
                    # High frequency search
                    time.sleep(0.01)
                except:
                    time.sleep(2)

    df = pd.DataFrame(processed_results)
    df.to_csv(output_path, index=False)
    print(f"\nFinal count: {len(df)}")
    print(f"Path: {output_path}")

if __name__ == "__main__":
    main()
