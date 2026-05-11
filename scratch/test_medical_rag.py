import os
from dotenv import load_dotenv
from pipelines.pipeline2_basic_rag import query

load_dotenv()

def test_medical_query():
    # Test query
    q = "What are the symptoms and precautions for Malaria?"
    print(f"Querying: {q}")
    
    result = query.run(q, namespace="medical-rag")
    
    print("\n--- ANSWER ---")
    print(result["answer"])
    print("\n--- METRICS ---")
    print(result["metrics"])

if __name__ == "__main__":
    test_medical_query()
