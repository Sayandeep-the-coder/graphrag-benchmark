import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

print("Searching for Gemma models...")
try:
    for m in genai.list_models():
        if 'gemma' in m.name.lower():
            print(f"Found: {m.name}")
except Exception as e:
    print(f"Error listing models: {e}")

print("\nTrying to get gemma-3-2b-it specifically...")
try:
    model = genai.get_model('models/gemma-3-2b-it')
    print(f"Successfully found gemma-3-2b-it: {model.name}")
except Exception as e:
    print(f"Failed to find gemma-3-2b-it: {e}")
