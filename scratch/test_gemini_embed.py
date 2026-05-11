
import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

def test_gemini_embedding():
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    model = "models/gemini-embedding-2"
    text = "West Bengal is a state in eastern India."
    
    print(f"Testing Gemini embedding with model: {model}")
    try:
        response = client.models.embed_content(
            model=model,
            contents=text
        )
        embedding = response.embeddings[0].values
        print(f"SUCCESS! Embedding length: {len(embedding)}")
        print(f"Sample values: {embedding[:5]}")
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    test_gemini_embedding()
