import pandas as pd
import os

def prepare_data():
    base_path = "data/medical"
    output_path = os.path.join(base_path, "knowledge_base.txt")
    
    print("Loading datasets...")
    # Load Description
    desc_df = pd.read_csv(os.path.join(base_path, "symptom_Description.csv"), header=None, names=["Disease", "Description"])
    desc_df["Disease"] = desc_df["Disease"].str.strip()
    
    # Load Precautions
    pre_df = pd.read_csv(os.path.join(base_path, "symptom_precaution.csv"), header=None, names=["Disease", "P1", "P2", "P3", "P4"])
    pre_df["Disease"] = pre_df["Disease"].str.strip()
    
    # Load Dataset (Symptoms)
    # The dataset has varying numbers of symptoms, we'll take the first column as disease and the rest as symptoms
    dataset_df = pd.read_csv(os.path.join(base_path, "dataset.csv"), header=None)
    dataset_df = dataset_df.rename(columns={0: "Disease"})
    dataset_df["Disease"] = dataset_df["Disease"].str.strip()
    
    # Group symptoms by disease (since there are multiple entries per disease)
    print("Aggregating symptoms...")
    disease_symptoms = {}
    for _, row in dataset_df.iterrows():
        disease = row["Disease"]
        if pd.isna(disease): continue
        
        symptoms = row.iloc[1:].dropna().tolist()
        symptoms = [s.strip().replace("_", " ") for s in symptoms if str(s).strip()]
        
        if disease not in disease_symptoms:
            disease_symptoms[disease] = set()
        disease_symptoms[disease].update(symptoms)
    
    # Load Symptom Severity
    sev_df = pd.read_csv(os.path.join(base_path, "Symptom_severity.csv"), header=None, names=["Symptom", "Weight"])
    sev_df["Symptom"] = sev_df["Symptom"].str.strip().str.replace("_", " ")
    symptom_weights = dict(zip(sev_df["Symptom"], sev_df["Weight"]))
    
    # Merge all into a final knowledge base
    print("Merging data...")
    with open(output_path, "w", encoding="utf-8") as f:
        # We'll use the description list as our primary disease list
        for _, row in desc_df.iterrows():
            disease = row["Disease"]
            description = row["Description"]
            
            # Get precautions
            prec_row = pre_df[pre_df["Disease"] == disease]
            precautions = []
            if not prec_row.empty:
                precautions = prec_row.iloc[0, 1:].dropna().tolist()
                precautions = [p.strip() for p in precautions if str(p).strip()]
            
            # Get symptoms with weights
            symptoms_list = sorted(list(disease_symptoms.get(disease, [])))
            symptoms_with_severity = []
            for s in symptoms_list:
                weight = symptom_weights.get(s, "unknown")
                symptoms_with_severity.append(f"{s} (severity: {weight})")
            
            # Format output
            f.write(f"Disease: {disease}\n")
            f.write(f"Description: {description}\n")
            if symptoms_with_severity:
                f.write(f"Symptoms: {', '.join(symptoms_with_severity)}\n")
            if precautions:
                f.write(f"Precautions: {', '.join(precautions)}\n")
            f.write("-" * 50 + "\n\n")
            
    print(f"Successfully created {output_path}")

if __name__ == "__main__":
    prepare_data()
