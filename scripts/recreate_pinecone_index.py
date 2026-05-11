import os
import time
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv

load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "graphrag-benchmark")
TARGET_DIMENSION = 384

def recreate_index():
    pc = Pinecone(api_key=PINECONE_API_KEY)
    
    print(f"Checking for existing index: {PINECONE_INDEX_NAME}...")
    
    # Delete existing index if it exists
    if PINECONE_INDEX_NAME in [idx.name for idx in pc.list_indexes()]:
        print(f"Deleting existing index {PINECONE_INDEX_NAME} (dimension mismatch)...")
        pc.delete_index(PINECONE_INDEX_NAME)
        # Wait for deletion to propagate
        while PINECONE_INDEX_NAME in [idx.name for idx in pc.list_indexes()]:
            time.sleep(1)
        print("Deletion complete.")
    
    print(f"Creating new index {PINECONE_INDEX_NAME} with dimension {TARGET_DIMENSION}...")
    pc.create_index(
        name=PINECONE_INDEX_NAME,
        dimension=TARGET_DIMENSION,
        metric="cosine",
        spec=ServerlessSpec(
            cloud="aws",
            region="us-east-1"  # Defaulting to us-east-1, common for free tier
        )
    )
    
    print("Waiting for index to be ready...")
    while not pc.describe_index(PINECONE_INDEX_NAME).status['ready']:
        time.sleep(1)
    
    print("New index is ready!")

if __name__ == "__main__":
    recreate_index()
