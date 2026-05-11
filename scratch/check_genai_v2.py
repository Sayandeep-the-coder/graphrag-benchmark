from google import genai
import os
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))

print("Searching for models with google.genai...")
try:
    for m in client.models.list():
        print(f"Found: {m.name}")
except Exception as e:
    print(f"Error listing models: {e}")

print("\nTrying to generate content with gemma-3-2b-it...")
try:
    response = client.models.generate_content(
        model='gemma-3-2b-it',
        contents="Say hello in one word"
    )
    print(f"Success! Response: {response.text}")
except Exception as e:
    print(f"Failed: {e}")
