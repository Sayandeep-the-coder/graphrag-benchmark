from google import genai
import os
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

print("Listing all available models...")
for m in client.models.list():
    if 'gemma' in m.name.lower():
        print(f"Gemma: {m.name}")
    elif 'gemini' in m.name.lower():
        # Just to see what else we have
        pass
    else:
        print(f"Other: {m.name}")
