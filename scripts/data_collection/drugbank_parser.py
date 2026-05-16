"""
DrugBank Open Data Parser

Parses the DrugBank open vocabulary CSV to extract drug names,
categories, and interaction data for the medical knowledge graph.

Source: https://go.drugbank.com/releases/latest#open-data
Format: CSV — drugbank_vocabulary.csv (free download after registration)
"""

import os
import csv
import json

DATA_DIR = "data/raw/drugbank"
OUTPUT_DIR = "data/raw/drugbank"


def parse_drugbank_vocabulary(csv_path: str = None) -> list[dict]:
    """Parse DrugBank vocabulary CSV into structured records."""

    if csv_path is None:
        csv_path = os.path.join(DATA_DIR, "drugbank_vocabulary.csv")

    if not os.path.exists(csv_path):
        print(f"[WARN] DrugBank CSV not found at {csv_path}")
        print("  Download from: https://go.drugbank.com/releases/latest#open-data")
        print("  Place drugbank_vocabulary.csv in data/raw/drugbank/")
        return generate_seed_drugs()

    drugs = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            drug_id = row.get("DrugBank ID", "").strip()
            name = row.get("Common name", "").strip()
            cas = row.get("CAS", "").strip()
            unii = row.get("UNII", "").strip()
            synonyms = row.get("Synonyms", "").strip()
            description = row.get("Description", "").strip()

            if name:
                # Build text summary for RAG ingestion
                text = f"Drug: {name}."
                if description:
                    text += f" {description}"
                if synonyms:
                    syn_list = [s.strip() for s in synonyms.split("|")][:5]
                    text += f" Also known as: {', '.join(syn_list)}."

                drugs.append({
                    "id": drug_id,
                    "name": name,
                    "generic_name": name.lower(),
                    "cas": cas,
                    "unii": unii,
                    "text": text,
                    "source": "drugbank"
                })

    return drugs


def generate_seed_drugs() -> list[dict]:
    """
    Generate a clinically relevant seed dataset of drugs commonly
    involved in polypharmacy interactions. Used when DrugBank CSV
    is not available.
    """
    print("  Generating seed drug dataset (polypharmacy-relevant)...")

    seed_drugs = [
        {"id": "DB00001", "name": "Warfarin", "drug_class": "Anticoagulant", "metabolism_pathway": "CYP2C9,CYP3A4", "half_life_hours": 40.0,
         "interactions": ["Aspirin", "Fluconazole", "Clarithromycin", "Metronidazole", "Amiodarone"],
         "contraindications": ["Active bleeding", "Severe liver disease", "Pregnancy"],
         "adverse_events": ["Bleeding", "Bruising", "Hemorrhagic stroke"]},

        {"id": "DB00002", "name": "Aspirin", "drug_class": "NSAID/Antiplatelet", "metabolism_pathway": "CYP2C9", "half_life_hours": 6.0,
         "interactions": ["Warfarin", "Ibuprofen", "Clopidogrel", "Methotrexate", "ACE Inhibitors"],
         "contraindications": ["Peptic ulcer", "Bleeding disorders", "Children with viral infection"],
         "adverse_events": ["GI bleeding", "Tinnitus", "Reye syndrome"]},

        {"id": "DB00003", "name": "Metformin", "drug_class": "Biguanide", "metabolism_pathway": "Renal", "half_life_hours": 6.2,
         "interactions": ["Alcohol", "Contrast dye", "Cimetidine", "Furosemide"],
         "contraindications": ["Renal impairment", "Metabolic acidosis", "Severe liver disease"],
         "adverse_events": ["Lactic acidosis", "Diarrhea", "Nausea", "Vitamin B12 deficiency"]},

        {"id": "DB00004", "name": "Simvastatin", "drug_class": "Statin", "metabolism_pathway": "CYP3A4", "half_life_hours": 3.0,
         "interactions": ["Clarithromycin", "Itraconazole", "Amiodarone", "Grapefruit juice", "Cyclosporine"],
         "contraindications": ["Active liver disease", "Pregnancy", "Breastfeeding"],
         "adverse_events": ["Rhabdomyolysis", "Myopathy", "Hepatotoxicity", "Muscle pain"]},

        {"id": "DB00005", "name": "Clarithromycin", "drug_class": "Macrolide antibiotic", "metabolism_pathway": "CYP3A4", "half_life_hours": 5.0,
         "interactions": ["Simvastatin", "Warfarin", "Carbamazepine", "Digoxin", "Colchicine"],
         "contraindications": ["QT prolongation", "Severe hepatic impairment"],
         "adverse_events": ["QT prolongation", "Hepatotoxicity", "C. difficile colitis"]},

        {"id": "DB00006", "name": "Fluconazole", "drug_class": "Azole antifungal", "metabolism_pathway": "CYP2C9,CYP3A4", "half_life_hours": 30.0,
         "interactions": ["Warfarin", "Phenytoin", "Rifampin", "Tacrolimus", "Clopidogrel"],
         "contraindications": ["Severe liver disease"],
         "adverse_events": ["Hepatotoxicity", "QT prolongation", "Stevens-Johnson syndrome"]},

        {"id": "DB00007", "name": "Amiodarone", "drug_class": "Antiarrhythmic", "metabolism_pathway": "CYP3A4,CYP2C8", "half_life_hours": 1200.0,
         "interactions": ["Warfarin", "Simvastatin", "Digoxin", "Phenytoin", "Cyclosporine"],
         "contraindications": ["Severe sinus node disease", "Second/third degree heart block"],
         "adverse_events": ["Pulmonary toxicity", "Thyroid dysfunction", "Hepatotoxicity", "Corneal deposits"]},

        {"id": "DB00008", "name": "Metoprolol", "drug_class": "Beta blocker", "metabolism_pathway": "CYP2D6", "half_life_hours": 5.0,
         "interactions": ["Verapamil", "Clonidine", "Fluoxetine", "Paroxetine", "Rifampin"],
         "contraindications": ["Severe bradycardia", "Decompensated heart failure", "Cardiogenic shock"],
         "adverse_events": ["Bradycardia", "Hypotension", "Fatigue", "Depression"]},

        {"id": "DB00009", "name": "Lisinopril", "drug_class": "ACE inhibitor", "metabolism_pathway": "Renal", "half_life_hours": 12.0,
         "interactions": ["Potassium supplements", "Spironolactone", "NSAIDs", "Lithium"],
         "contraindications": ["Pregnancy", "Angioedema history", "Bilateral renal artery stenosis"],
         "adverse_events": ["Angioedema", "Hyperkalemia", "Dry cough", "Renal impairment"]},

        {"id": "DB00010", "name": "Omeprazole", "drug_class": "Proton pump inhibitor", "metabolism_pathway": "CYP2C19,CYP3A4", "half_life_hours": 1.0,
         "interactions": ["Clopidogrel", "Methotrexate", "Tacrolimus", "Digoxin"],
         "contraindications": ["Hypersensitivity to PPIs"],
         "adverse_events": ["C. difficile infection", "Hypomagnesemia", "Bone fractures", "Vitamin B12 deficiency"]},

        {"id": "DB00011", "name": "Clopidogrel", "drug_class": "Antiplatelet", "metabolism_pathway": "CYP2C19", "half_life_hours": 6.0,
         "interactions": ["Omeprazole", "Aspirin", "Warfarin", "Fluconazole", "NSAIDs"],
         "contraindications": ["Active bleeding", "Severe liver disease"],
         "adverse_events": ["Bleeding", "TTP", "Neutropenia"]},

        {"id": "DB00012", "name": "Digoxin", "drug_class": "Cardiac glycoside", "metabolism_pathway": "P-glycoprotein", "half_life_hours": 39.0,
         "interactions": ["Amiodarone", "Verapamil", "Clarithromycin", "Quinidine"],
         "contraindications": ["Ventricular fibrillation", "Hypokalemia"],
         "adverse_events": ["Digitalis toxicity", "Arrhythmias", "Visual disturbances", "Nausea"]},

        {"id": "DB00013", "name": "Phenytoin", "drug_class": "Anticonvulsant", "metabolism_pathway": "CYP2C9,CYP2C19", "half_life_hours": 22.0,
         "interactions": ["Fluconazole", "Amiodarone", "Carbamazepine", "Valproic acid"],
         "contraindications": ["Sinus bradycardia", "SA block", "Adams-Stokes syndrome"],
         "adverse_events": ["Gingival hyperplasia", "Nystagmus", "Ataxia", "SJS/TEN"]},

        {"id": "DB00014", "name": "Methotrexate", "drug_class": "Antimetabolite", "metabolism_pathway": "Renal", "half_life_hours": 8.0,
         "interactions": ["NSAIDs", "Trimethoprim", "Omeprazole", "Penicillins"],
         "contraindications": ["Pregnancy", "Severe renal impairment", "Severe hepatic impairment"],
         "adverse_events": ["Myelosuppression", "Hepatotoxicity", "Pneumonitis", "Mucositis"]},

        {"id": "DB00015", "name": "Fluoxetine", "drug_class": "SSRI", "metabolism_pathway": "CYP2D6", "half_life_hours": 72.0,
         "interactions": ["MAOIs", "Tramadol", "Metoprolol", "Tamoxifen", "Linezolid"],
         "contraindications": ["MAOIs within 14 days", "Pimozide use"],
         "adverse_events": ["Serotonin syndrome", "Suicidal ideation", "QT prolongation", "Hyponatremia"]},

        {"id": "DB00016", "name": "Ibuprofen", "drug_class": "NSAID", "metabolism_pathway": "CYP2C9", "half_life_hours": 2.0,
         "interactions": ["Aspirin", "Warfarin", "Lithium", "Methotrexate", "ACE inhibitors"],
         "contraindications": ["Active GI bleeding", "Severe renal impairment", "Coronary bypass surgery"],
         "adverse_events": ["GI ulceration", "Renal toxicity", "Cardiovascular events"]},

        {"id": "DB00017", "name": "Amlodipine", "drug_class": "Calcium channel blocker", "metabolism_pathway": "CYP3A4", "half_life_hours": 40.0,
         "interactions": ["Simvastatin", "Cyclosporine", "CYP3A4 inhibitors"],
         "contraindications": ["Severe aortic stenosis", "Cardiogenic shock"],
         "adverse_events": ["Peripheral edema", "Dizziness", "Flushing", "Palpitations"]},

        {"id": "DB00018", "name": "Tramadol", "drug_class": "Opioid analgesic", "metabolism_pathway": "CYP2D6,CYP3A4", "half_life_hours": 6.3,
         "interactions": ["SSRIs", "MAOIs", "Carbamazepine", "Ondansetron"],
         "contraindications": ["MAOIs within 14 days", "Uncontrolled epilepsy", "Acute intoxication"],
         "adverse_events": ["Seizures", "Serotonin syndrome", "Respiratory depression", "Dependence"]},

        {"id": "DB00019", "name": "Spironolactone", "drug_class": "Aldosterone antagonist", "metabolism_pathway": "Hepatic", "half_life_hours": 1.4,
         "interactions": ["ACE inhibitors", "Potassium supplements", "NSAIDs", "Digoxin", "Lithium"],
         "contraindications": ["Hyperkalemia", "Addison's disease", "Severe renal impairment"],
         "adverse_events": ["Hyperkalemia", "Gynecomastia", "Menstrual irregularities"]},

        {"id": "DB00020", "name": "Carbamazepine", "drug_class": "Anticonvulsant", "metabolism_pathway": "CYP3A4", "half_life_hours": 16.0,
         "interactions": ["Clarithromycin", "Phenytoin", "Valproic acid", "Warfarin", "Oral contraceptives"],
         "contraindications": ["Bone marrow depression", "MAOIs within 14 days"],
         "adverse_events": ["Aplastic anemia", "SJS/TEN", "Hepatotoxicity", "Hyponatremia"]},
    ]

    # Build text descriptions for RAG ingestion
    drugs = []
    for d in seed_drugs:
        interactions_text = ", ".join(d["interactions"])
        contra_text = ", ".join(d["contraindications"])
        adverse_text = ", ".join(d["adverse_events"])
        text = (
            f"{d['name']} is a {d['drug_class']} metabolized via {d['metabolism_pathway']} "
            f"with a half-life of {d['half_life_hours']} hours. "
            f"Known drug interactions include: {interactions_text}. "
            f"Contraindications: {contra_text}. "
            f"Adverse events: {adverse_text}."
        )
        drugs.append({
            "id": d["id"],
            "name": d["name"],
            "generic_name": d["name"].lower(),
            "drug_class": d["drug_class"],
            "metabolism_pathway": d["metabolism_pathway"],
            "half_life_hours": d["half_life_hours"],
            "interactions": d["interactions"],
            "contraindications": d["contraindications"],
            "adverse_events": d["adverse_events"],
            "text": text,
            "source": "drugbank_seed"
        })

    return drugs


def save_drugbank_data(drugs: list[dict] = None):
    """Parse and save DrugBank data."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if drugs is None:
        drugs = parse_drugbank_vocabulary()

    output_path = os.path.join(OUTPUT_DIR, "drugbank_drugs.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(drugs, f, indent=2)

    print(f"[OK] Saved {len(drugs)} drugs to {output_path}")
    return drugs


if __name__ == "__main__":
    save_drugbank_data()
