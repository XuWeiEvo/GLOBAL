# -*- coding: utf-8 -*-

import requests
import pandas as pd
from bs4 import BeautifulSoup
import time

# Function: Get species ID from IPNI
def fetch_ipni_id(species_name):
    """
    Get the IPNI ID of a species based on its scientific name.
    """
    base_url = "https://www.ipni.org/api/1/search"
    params = {"q": species_name, "type": "names"}
    try:
        # Request IPNI API
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Extract the ID from the first result
        if data and "results" in data and len(data["results"]) > 0:
            ipni_id = data["results"][0]["id"].split(":")[-1]  # Extract the ID part
            return ipni_id
        else:
            return None
    except Exception as e:
        print(f"Error retrieving IPNI ID for {species_name}: {e}")
        return None

# Function: Extract synonym data from the POWO page
def fetch_synonyms_from_powo(powo_url):
    """
    Extract synonym information from a POWO taxon page.
    """
    try:
        # Request POWO page
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(powo_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Locate the Synonyms section
        synonyms_section = soup.find('section', id='synonyms')
        if not synonyms_section:
            return None  # No Synonyms section found
        
        # Find all <li> tags under the c-synonym-list
        synonyms_list = synonyms_section.find('ul', class_='c-synonym-list')
        if not synonyms_list:
            return None  # No synonym list found
        
        # Extract the text of each synonym
        synonyms = [li.text.strip() for li in synonyms_list.find_all('li')]
        return synonyms  # Return list of synonyms
    except Exception as e:
        print(f"Error fetching synonyms from {powo_url}: {e}")
        return None

# Main function: Combine IPNI lookup and POWO synonym extraction
def main(input_csv, output_csv):
    """
    Main function: query IPNI ID by species name, construct POWO URL, and extract synonym data.
    """
    # Load the input CSV file; assume it has a 'Species' column
    species_df = pd.read_csv(input_csv)
    
    # Ensure required column is present
    if 'Species' not in species_df.columns:
        raise ValueError("The input file must contain a 'Species' column.")
    
    results = []
    for _, row in species_df.iterrows():
        species_name = row['Species'].strip()  # Remove extra spaces
        print(f"Processing species: {species_name}")
        
        # Step 1: Get IPNI ID
        ipni_id = fetch_ipni_id(species_name)
        if not ipni_id:
            print(f"No IPNI ID found for {species_name}")
            results.append({'Species': species_name, 'POWO_URL': "Not Found", 'Synonyms': "None"})
            continue
        
        # Step 2: Construct POWO URL
        powo_url = f"https://powo.science.kew.org/taxon/urn:lsid:ipni.org:names:{ipni_id}"
        print(f"Constructed POWO URL: {powo_url}")
        
        # Step 3: Extract synonyms from POWO page
        synonyms = fetch_synonyms_from_powo(powo_url)
        results.append({
            'Species': species_name,
            'POWO_URL': powo_url,
            'Synonyms': '; '.join(synonyms) if synonyms else "None"
        })
        
        # Delay to avoid triggering anti-bot mechanisms
        time.sleep(2)
    
    # Save results to output CSV
    output_df = pd.DataFrame(results)
    output_df.to_csv(output_csv, index=False)
    print(f"Results saved to {output_csv}")

# Run the script
if __name__ == '__main__':
    input_csv = 'species_list.csv'  # Input file containing 'Species' column
    output_csv = 'species_results.csv'  # Output file
    main(input_csv, output_csv)
