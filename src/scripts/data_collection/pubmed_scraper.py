import os
import json
import time
import requests
import xml.etree.ElementTree as ET
from tqdm import tqdm
from dotenv import load_dotenv

load_dotenv()

# Configuration
EMAIL = os.getenv("EMAIL_FOR_PUBMED", "your@email.com")
QUERY = 'polypharmacy[Title] OR "drug interaction"[Title] OR "adverse drug reaction"[Title]'
MAX_RESULTS = int(os.getenv("PUBMED_MAX_RESULTS", "9000"))
DATA_DIR = "data/raw/pubmed"
EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


def _get_text(node):
    """Return all text content under an XML node."""
    if node is None:
        return ""
    return " ".join(part.strip() for part in node.itertext() if part and part.strip())


def _search_pubmed_ids():
    """Search PubMed via ESearch without requiring Biopython."""
    response = requests.get(
        f"{EUTILS}/esearch.fcgi",
        params={
            "db": "pubmed",
            "term": QUERY,
            "retmax": MAX_RESULTS,
            "retmode": "xml",
            "email": EMAIL,
        },
        timeout=60,
    )
    response.raise_for_status()
    root = ET.fromstring(response.content)
    count = int(root.findtext("Count") or 0)
    ids = [node.text for node in root.findall(".//Id") if node.text]
    return count, ids


def _fetch_pubmed_batch(batch_ids):
    """Fetch PubMed XML records for a batch of IDs."""
    response = requests.post(
        f"{EUTILS}/efetch.fcgi",
        data={
            "db": "pubmed",
            "id": ",".join(batch_ids),
            "retmode": "xml",
            "email": EMAIL,
        },
        timeout=120,
    )
    response.raise_for_status()
    return ET.fromstring(response.content)

def fetch_pubmed_abstracts():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    print(f"Searching PubMed for: {QUERY}")
    count, id_list = _search_pubmed_ids()
    print(f"Found {count} results. Fetching top {len(id_list)}...")

    batch_size = 100
    all_abstracts = []

    for i in tqdm(range(0, len(id_list), batch_size)):
        batch_ids = id_list[i : i + batch_size]
        try:
            batch_root = _fetch_pubmed_batch(batch_ids)

            for article in batch_root.findall(".//PubmedArticle"):
                try:
                    pmid = article.findtext(".//MedlineCitation/PMID") or ""
                    title = _get_text(article.find(".//ArticleTitle"))
                    abstract_nodes = article.findall(".//Abstract/AbstractText")
                    abstract = " ".join(_get_text(node) for node in abstract_nodes).strip()

                    if abstract:
                        all_abstracts.append({
                            "id": pmid,
                            "title": title,
                            "text": abstract,
                            "source": "pubmed"
                        })
                except (AttributeError, ValueError):
                    continue

            time.sleep(0.5)  # Respect NCBI rate limits
        except (requests.RequestException, ET.ParseError, RuntimeError, ValueError) as e:
            print(f"Error fetching batch: {e}")
            continue

    output_path = os.path.join(DATA_DIR, "pubmed_abstracts.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_abstracts, f, indent=2)
    
    print(f"Successfully saved {len(all_abstracts)} abstracts to {output_path}")

if __name__ == "__main__":
    fetch_pubmed_abstracts()
