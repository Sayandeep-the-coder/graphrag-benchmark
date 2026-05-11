from google import genai
import os
from dotenv import load_dotenv

load_dotenv()
# The new SDK doesn't have an easy way to specify v1 in the Client constructor yet, 
# but we can try to use the vertex setting or similar if available.
# Actually, the default is v1beta.

client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'), http_options={'api_version': 'v1'})

try:
    response = client.models.generate_content(
        model='gemma-3-2b-it',
        contents="Say hello"
    )
    print(f"v1 SUCCESS: {response.text}")
except Exception as e:
    print(f"v1 FAILED: {e}")
