"""
Disease-Symptom Dataset Loader

Generates a comprehensive disease-symptom-treatment mapping dataset
for the medical knowledge graph. Based on common clinical associations.
"""

import os
import json

OUTPUT_DIR = "data/raw/diseases"


def generate_disease_symptom_data() -> list[dict]:
    """
    Generate clinically accurate disease-symptom-treatment mappings
    focused on conditions commonly seen in polypharmacy patients.
    """

    diseases = [
        {
            "id": "DIS001", "name": "Type 2 Diabetes Mellitus",
            "icd_code": "E11", "category": "Endocrine", "chronic": True,
            "symptoms": [
                {"name": "Polyuria", "frequency": 0.85, "early_sign": True},
                {"name": "Polydipsia", "frequency": 0.80, "early_sign": True},
                {"name": "Fatigue", "frequency": 0.75, "early_sign": False},
                {"name": "Blurred vision", "frequency": 0.50, "early_sign": False},
                {"name": "Weight loss", "frequency": 0.45, "early_sign": False},
                {"name": "Peripheral neuropathy", "frequency": 0.30, "early_sign": False},
            ],
            "first_line_drugs": ["Metformin"],
            "second_line_drugs": ["Glipizide", "Sitagliptin", "Empagliflozin"],
            "comorbidities": ["Hypertension", "Chronic Kidney Disease", "Coronary Artery Disease"],
        },
        {
            "id": "DIS002", "name": "Hypertension",
            "icd_code": "I10", "category": "Cardiovascular", "chronic": True,
            "symptoms": [
                {"name": "Headache", "frequency": 0.40, "early_sign": False},
                {"name": "Dizziness", "frequency": 0.35, "early_sign": False},
                {"name": "Chest pain", "frequency": 0.20, "early_sign": False},
                {"name": "Visual disturbances", "frequency": 0.15, "early_sign": False},
            ],
            "first_line_drugs": ["Lisinopril", "Amlodipine", "Losartan"],
            "second_line_drugs": ["Metoprolol", "Spironolactone", "Hydrochlorothiazide"],
            "comorbidities": ["Type 2 Diabetes Mellitus", "Chronic Kidney Disease", "Heart Failure"],
        },
        {
            "id": "DIS003", "name": "Atrial Fibrillation",
            "icd_code": "I48", "category": "Cardiovascular", "chronic": True,
            "symptoms": [
                {"name": "Palpitations", "frequency": 0.80, "early_sign": True},
                {"name": "Fatigue", "frequency": 0.60, "early_sign": False},
                {"name": "Dyspnea", "frequency": 0.55, "early_sign": False},
                {"name": "Dizziness", "frequency": 0.40, "early_sign": False},
                {"name": "Chest pain", "frequency": 0.30, "early_sign": False},
            ],
            "first_line_drugs": ["Warfarin", "Metoprolol", "Digoxin"],
            "second_line_drugs": ["Amiodarone", "Apixaban", "Rivaroxaban"],
            "comorbidities": ["Heart Failure", "Hypertension", "Stroke"],
        },
        {
            "id": "DIS004", "name": "Coronary Artery Disease",
            "icd_code": "I25", "category": "Cardiovascular", "chronic": True,
            "symptoms": [
                {"name": "Chest pain", "frequency": 0.90, "early_sign": True},
                {"name": "Dyspnea", "frequency": 0.65, "early_sign": False},
                {"name": "Fatigue", "frequency": 0.50, "early_sign": False},
                {"name": "Palpitations", "frequency": 0.30, "early_sign": False},
            ],
            "first_line_drugs": ["Aspirin", "Atorvastatin", "Metoprolol"],
            "second_line_drugs": ["Clopidogrel", "Amlodipine", "Lisinopril"],
            "comorbidities": ["Hypertension", "Type 2 Diabetes Mellitus", "Hyperlipidemia"],
        },
        {
            "id": "DIS005", "name": "Heart Failure",
            "icd_code": "I50", "category": "Cardiovascular", "chronic": True,
            "symptoms": [
                {"name": "Dyspnea", "frequency": 0.95, "early_sign": True},
                {"name": "Peripheral edema", "frequency": 0.80, "early_sign": True},
                {"name": "Fatigue", "frequency": 0.75, "early_sign": False},
                {"name": "Orthopnea", "frequency": 0.60, "early_sign": False},
                {"name": "Weight gain", "frequency": 0.50, "early_sign": False},
            ],
            "first_line_drugs": ["Lisinopril", "Metoprolol", "Spironolactone"],
            "second_line_drugs": ["Digoxin", "Furosemide", "Hydralazine"],
            "comorbidities": ["Coronary Artery Disease", "Atrial Fibrillation", "Chronic Kidney Disease"],
        },
        {
            "id": "DIS006", "name": "Chronic Kidney Disease",
            "icd_code": "N18", "category": "Renal", "chronic": True,
            "symptoms": [
                {"name": "Fatigue", "frequency": 0.70, "early_sign": False},
                {"name": "Peripheral edema", "frequency": 0.60, "early_sign": False},
                {"name": "Nausea", "frequency": 0.45, "early_sign": False},
                {"name": "Decreased urine output", "frequency": 0.40, "early_sign": True},
                {"name": "Muscle cramps", "frequency": 0.35, "early_sign": False},
            ],
            "first_line_drugs": ["Lisinopril", "Amlodipine"],
            "second_line_drugs": ["Erythropoietin", "Sodium bicarbonate"],
            "comorbidities": ["Type 2 Diabetes Mellitus", "Hypertension", "Heart Failure"],
        },
        {
            "id": "DIS007", "name": "Major Depressive Disorder",
            "icd_code": "F33", "category": "Psychiatric", "chronic": True,
            "symptoms": [
                {"name": "Depressed mood", "frequency": 0.95, "early_sign": True},
                {"name": "Anhedonia", "frequency": 0.85, "early_sign": True},
                {"name": "Insomnia", "frequency": 0.70, "early_sign": False},
                {"name": "Fatigue", "frequency": 0.65, "early_sign": False},
                {"name": "Appetite changes", "frequency": 0.55, "early_sign": False},
                {"name": "Difficulty concentrating", "frequency": 0.50, "early_sign": False},
            ],
            "first_line_drugs": ["Fluoxetine", "Sertraline"],
            "second_line_drugs": ["Venlafaxine", "Bupropion", "Mirtazapine"],
            "comorbidities": ["Generalized Anxiety Disorder", "Chronic Pain", "Type 2 Diabetes Mellitus"],
        },
        {
            "id": "DIS008", "name": "Epilepsy",
            "icd_code": "G40", "category": "Neurological", "chronic": True,
            "symptoms": [
                {"name": "Seizures", "frequency": 1.0, "early_sign": True},
                {"name": "Loss of consciousness", "frequency": 0.70, "early_sign": False},
                {"name": "Confusion", "frequency": 0.60, "early_sign": False},
                {"name": "Muscle rigidity", "frequency": 0.40, "early_sign": False},
            ],
            "first_line_drugs": ["Carbamazepine", "Phenytoin", "Valproic acid"],
            "second_line_drugs": ["Levetiracetam", "Lamotrigine"],
            "comorbidities": ["Major Depressive Disorder", "Anxiety"],
        },
        {
            "id": "DIS009", "name": "GERD",
            "icd_code": "K21", "category": "Gastrointestinal", "chronic": True,
            "symptoms": [
                {"name": "Heartburn", "frequency": 0.90, "early_sign": True},
                {"name": "Regurgitation", "frequency": 0.75, "early_sign": True},
                {"name": "Dysphagia", "frequency": 0.30, "early_sign": False},
                {"name": "Chest pain", "frequency": 0.25, "early_sign": False},
            ],
            "first_line_drugs": ["Omeprazole"],
            "second_line_drugs": ["Ranitidine", "Esomeprazole"],
            "comorbidities": ["Peptic Ulcer Disease", "Bronchial Asthma"],
        },
        {
            "id": "DIS010", "name": "Rheumatoid Arthritis",
            "icd_code": "M06", "category": "Rheumatological", "chronic": True,
            "symptoms": [
                {"name": "Joint pain", "frequency": 0.95, "early_sign": True},
                {"name": "Joint stiffness", "frequency": 0.90, "early_sign": True},
                {"name": "Joint swelling", "frequency": 0.85, "early_sign": True},
                {"name": "Fatigue", "frequency": 0.60, "early_sign": False},
            ],
            "first_line_drugs": ["Methotrexate", "Ibuprofen"],
            "second_line_drugs": ["Hydroxychloroquine", "Sulfasalazine", "Prednisone"],
            "comorbidities": ["Osteoporosis", "Cardiovascular Disease"],
        },
        {
            "id": "DIS011", "name": "Chronic Pain Syndrome",
            "icd_code": "G89", "category": "Pain", "chronic": True,
            "symptoms": [
                {"name": "Persistent pain", "frequency": 1.0, "early_sign": True},
                {"name": "Fatigue", "frequency": 0.70, "early_sign": False},
                {"name": "Insomnia", "frequency": 0.65, "early_sign": False},
                {"name": "Depression", "frequency": 0.55, "early_sign": False},
            ],
            "first_line_drugs": ["Ibuprofen", "Tramadol"],
            "second_line_drugs": ["Gabapentin", "Duloxetine", "Amitriptyline"],
            "comorbidities": ["Major Depressive Disorder", "Generalized Anxiety Disorder"],
        },
        {
            "id": "DIS012", "name": "Deep Vein Thrombosis",
            "icd_code": "I82", "category": "Vascular", "chronic": False,
            "symptoms": [
                {"name": "Leg swelling", "frequency": 0.85, "early_sign": True},
                {"name": "Leg pain", "frequency": 0.80, "early_sign": True},
                {"name": "Warmth over affected area", "frequency": 0.50, "early_sign": False},
                {"name": "Skin discoloration", "frequency": 0.40, "early_sign": False},
            ],
            "first_line_drugs": ["Warfarin", "Heparin"],
            "second_line_drugs": ["Rivaroxaban", "Apixaban"],
            "comorbidities": ["Pulmonary Embolism", "Atrial Fibrillation"],
        },
    ]

    # Build text summaries
    records = []
    for d in diseases:
        symptom_list = ", ".join([s["name"] for s in d["symptoms"]])
        drug_list = ", ".join(d["first_line_drugs"] + d["second_line_drugs"])
        comorbidity_list = ", ".join(d["comorbidities"])

        text = (
            f"{d['name']} (ICD: {d['icd_code']}) is a {'chronic' if d['chronic'] else 'acute'} "
            f"{d['category'].lower()} condition. "
            f"Common symptoms include: {symptom_list}. "
            f"Treatment options: {drug_list}. "
            f"Common comorbidities: {comorbidity_list}."
        )

        records.append({
            **d,
            "text": text,
            "source": "disease_symptom_dataset"
        })

    return records


def save_disease_data():
    """Generate and save disease-symptom data."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    diseases = generate_disease_symptom_data()
    output_path = os.path.join(OUTPUT_DIR, "disease_symptoms.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(diseases, f, indent=2)

    print(f"[OK] Saved {len(diseases)} disease records to {output_path}")
    return diseases


if __name__ == "__main__":
    save_disease_data()
