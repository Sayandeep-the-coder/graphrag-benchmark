import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

for m in genai.list_models():
    if 'gemma' in m.name.lower():
        print(f"Name: {m.name}")
        print(f"Methods: {m.supported_generation_methods}")
        print("-" * 20)
