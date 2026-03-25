import pandas as pd
import os
import requests
import re
from search_utils import search_duckduckgo, search_google_playwright
from data_processor import classify_company_size, extract_sector, clean_url, is_likely_company

def search_overpass(lat, lon, radius_meters=20000):
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

def main():
    print("Starting combined company search (DuckDuckGo, Google, OpenStreetMap) near Porur, Chennai...")

    # Porur Chennai coordinates
    lat, lon = 13.0382, 80.1544
    base_location = "Porur Chennai"

    # 1. SEARCH ENGINES (DDG, Google)
    target_queries = [
        f"IT services companies in {base_location}",
        f"Fintech companies in {base_location}",
        f"Hardware technology companies in {base_location}",
        f"Cybersecurity companies in {base_location}",
        f"Electric vehicles EV companies in {base_location}",
        f"Business consulting firms in {base_location}",
        f"SaaS companies near {base_location}",
        f"Tech MNCs in {base_location}",
        f"LPG energy companies near {base_location}"
    ]

    all_raw_results = []

    for query in target_queries:
        print(f"Searching for: {query}")
        # DuckDuckGo search
        ddg_res = search_duckduckgo(query, max_results=20)
        all_raw_results.extend(ddg_res)
        # Google search (Playwright)
        google_res = search_google_playwright(query, max_results=10)
        all_raw_results.extend(google_res)

    print(f"Search engines total raw results: {len(all_raw_results)}")

    processed_results = []
    seen_names = set()

    # Deduplicate and initial processing of engine results
    for r in all_raw_results:
        link = clean_url(r['link'])
        name = r['name']
        snippet = r['snippet']

        if not is_likely_company(name, snippet, link):
            continue

        norm_name = re.sub(r'[^a-zA-Z0-9]', '', name).lower()
        if norm_name not in seen_names:
            seen_names.add(norm_name)
            processed_results.append({
                'Company Name': name,
                'Company Website': link,
                'Company Location': "Porur, Chennai Radius",
                'Sector': extract_sector(snippet, name),
                'Classification': classify_company_size(snippet, name),
                'Source': r['source']
            })
        else:
            for p in processed_results:
                if re.sub(r'[^a-zA-Z0-9]', '', p['Company Name']).lower() == norm_name:
                    if r['source'] not in p['Source']:
                        p['Source'] += f", {r['source']}"
                    break

    # 2. OPENSTREETMAP (OVERPASS)
    print("Searching OpenStreetMap (Overpass)...")
    osm_data = search_overpass(lat, lon, 20000)
    if osm_data and 'elements' in osm_data:
        print(f"OSM raw elements: {len(osm_data['elements'])}")
        for element in osm_data['elements']:
            tags = element.get('tags', {})
            name = tags.get('name')
            if not name:
                continue

            if not is_likely_company(name, "", ""):
                continue

            norm_name = re.sub(r'[^a-zA-Z0-9]', '', name).lower()
            if norm_name not in seen_names:
                seen_names.add(norm_name)

                # Heuristics for sector from OSM tags
                office = tags.get('office', '').lower()
                industrial = tags.get('industrial', '').lower()
                business = tags.get('business', '').lower()
                desc = f"{office} {industrial} {business}".strip()

                sector = "Other/Company"
                if any(k in desc for k in ['it', 'software', 'technology', 'systems']):
                    sector = "IT Services"
                elif any(k in desc for k in ['finance', 'bank', 'insurance']):
                    sector = "Fintech"
                elif any(k in desc for k in ['energy', 'electric', 'gas', 'power']):
                    sector = "Electric/Energy"
                elif any(k in desc for k in ['electronics', 'manufacturing', 'hardware']):
                    sector = "Hardware"

                processed_results.append({
                    'Company Name': name,
                    'Company Website': tags.get('website', tags.get('contact:website', '')),
                    'Company Location': f"{tags.get('addr:street', '')} {tags.get('addr:suburb', '')}".strip() or "Porur, Chennai Radius",
                    'Sector': sector,
                    'Classification': classify_company_size("", name),
                    'Source': 'OpenStreetMap'
                })
            else:
                for p in processed_results:
                    if re.sub(r'[^a-zA-Z0-9]', '', p['Company Name']).lower() == norm_name:
                        if 'OpenStreetMap' not in p['Source']:
                            p['Source'] += ", OpenStreetMap"
                        break

    # Final filtering for data quality
    final_list = []
    for p in processed_results:
        # Avoid generic titles
        if len(p['Company Name'].split()) > 6:
            continue
        final_list.append(p)

    # Convert and Save
    df = pd.DataFrame(final_list)
    output_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(output_dir, "companies_porur_chennai.csv")
    df.to_csv(csv_path, index=False)

    print(f"\nSaved {len(df)} unique companies to: {csv_path}")
    if not df.empty:
        print("\nSample results:")
        print(df[['Company Name', 'Sector', 'Classification']].head())

if __name__ == "__main__":
    main()
