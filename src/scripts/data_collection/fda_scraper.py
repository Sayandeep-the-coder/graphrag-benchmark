import os
import json
import requests
from tqdm import tqdm
from dotenv import load_dotenv

load_dotenv()

# Configuration
FDA_API_URL = "https://api.fda.gov/drug/event.json"
MAX_RESULTS = int(os.getenv("FDA_MAX_RESULTS", "6000"))
BATCH_SIZE = 100
DATA_DIR = "data/raw/fda"

def fetch_fda_events():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    print("Fetching FDA Adverse Event reports...")
    all_events = []

    for skip in tqdm(range(0, MAX_RESULTS, BATCH_SIZE)):
        params = {
            "search": 'serious:1 AND patient.drug.drugcharacterization:1', # Suspected primary drug
            "limit": BATCH_SIZE,
            "skip": skip
        }
        try:
            response = requests.get(FDA_API_URL, params=params)
            data = response.json()
            
            if "results" in data:
                for result in data["results"]:
                    # Extract relevant fields for our graph
                    event_id = result.get("safetyreportid")
                    reactions = [r.get("reactionmeddrapt") for r in result.get("patient", {}).get("reaction", [])]
                    drugs = []
                    for d in result.get("patient", {}).get("drug", []):
                        drug_name = d.get("medicinalproduct")
                        indication = d.get("drugindication")
                        if drug_name:
                            drugs.append({"name": drug_name, "indication": indication})
                    
                    if drugs and reactions:
                        # Convert to a text summary for RAG/Graph extraction
                        reaction_str = ", ".join([str(r) for r in reactions if r])
                        drug_str = ", ".join([str(d['name']) for d in drugs])
                        summary = f"Patient taking {drug_str} experienced {reaction_str}."
                        
                        all_events.append({
                            "id": event_id,
                            "text": summary,
                            "raw_data": {
                                "drugs": drugs,
                                "reactions": reactions,
                                "seriousness": result.get("seriousness")
                            },
                            "source": "fda_faers"
                        })
            
            if len(data.get("results", [])) < BATCH_SIZE:
                break # No more results
                
        except (requests.RequestException, ValueError, KeyError) as e:
            print(f"Error fetching FDA data at skip {skip}: {e}")
            continue

    output_path = os.path.join(DATA_DIR, "fda_events.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_events, f, indent=2)
    
    print(f"Successfully saved {len(all_events)} FDA reports to {output_path}")

if __name__ == "__main__":
    fetch_fda_events()
