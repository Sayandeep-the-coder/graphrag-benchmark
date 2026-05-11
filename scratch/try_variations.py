from google import genai
import os
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))

variations = [
    'gemma-3-2b',
    'gemma-3-2b-it',
    'models/gemma-3-2b',
    'models/gemma-3-2b-it',
    'gemma-2-2b-it',
    'models/gemma-2-2b-it',
    'gemma-2b-it',
    'models/gemma-2b-it'
]

for model_id in variations:
    print(f"Trying {model_id}...")
    try:
        response = client.models.generate_content(
            model=model_id,
            contents="Say hello"
        )
        print(f"  SUCCESS: {model_id}")
        break
    except Exception as e:
        print(f"  FAILED: {model_id}")
