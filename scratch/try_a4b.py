import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

try:
    print(genai.get_model('models/gemma-3-2b-a4b-it'))
except Exception as e:
    print(e)
