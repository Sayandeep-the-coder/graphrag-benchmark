
import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

print("Listing embedding models...")
for model in client.models.list():
    if "embed" in model.name:
        print(f"Name: {model.name}, Actions: {model.supported_actions}")
