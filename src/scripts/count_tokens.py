"""
Count tokens using the Google GenAI SDK (most accurate for Gemma).

Usage: python scripts/count_tokens.py --path data/medical/knowledge_base.txt
"""

import argparse
import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

def count_tokens(path: str, model_id: str = "models/gemini-2.5-flash"):
    """
    Count tokens in a file or directory using the GenAI SDK.
    """
    if not os.path.exists(path):
        print(f"Error: Path {path} does not exist.")
        return

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    
    # Collect text
    if os.path.isdir(path):
        import glob
        filepaths = glob.glob(f"{path}/**/*.txt", recursive=True)
        text = ""
        for fp in filepaths:
            with open(fp, encoding="utf-8") as f:
                text += f.read() + "\n"
    else:
        with open(path, encoding="utf-8") as f:
            text = f.read()

    print(f"Counting tokens for: {path} ...")
    
    try:
        response = client.models.count_tokens(
            model=model_id,
            contents=text
        )
        total_tokens = response.total_tokens
        
        print(f"{'='*50}")
        print(f"  Token Count Results (Model: {model_id})")
        print(f"{'='*50}")
        print(f"  Path          : {path}")
        print(f"  Total tokens  : {total_tokens:,}")
        
        # Estimate cost (approximate; for display only)
        embed_cost = total_tokens / 1000 * 0.0001
        print(f"  Est. embed cost: ${embed_cost:.4f}")
        print(f"{'='*50}")
        
    except Exception as e:
        print(f"Error calling GenAI API: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Count tokens using Google GenAI SDK.")
    parser.add_argument("--path", type=str, default="data/medical/knowledge_base.txt", help="Path to file or folder.")
    parser.add_argument("--model", type=str, default="models/gemini-2.5-flash", help="Model ID to use for tokenization.")
    
    args = parser.parse_args()
    count_tokens(args.path, args.model)
