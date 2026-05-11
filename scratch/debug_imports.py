
import sys
import os

print("Checking imports...")

try:
    import fastapi
    print("OK: fastapi imported")
except Exception as e:
    print(f"FAIL: fastapi failed: {e}")

try:
    from dotenv import load_dotenv
    load_dotenv()
    print("OK: dotenv loaded")
except Exception as e:
    print(f"FAIL: dotenv failed: {e}")

try:
    sys.path.insert(0, os.getcwd())
    print(f"Added {os.getcwd()} to sys.path")
    
    from pipelines import pipeline1_llm_only as p1
    print("OK: pipeline1 imported")
    
    from pipelines.pipeline2_basic_rag import query as p2
    print("OK: pipeline2 imported")
    
    from pipelines.pipeline3_graphrag import query as p3
    print("OK: pipeline3 imported")
    
except Exception as e:
    print(f"FAIL: pipeline import failed: {e}")
    import traceback
    traceback.print_exc()

print("Import check finished.")
