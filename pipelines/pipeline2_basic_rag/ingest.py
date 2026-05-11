import argparse
import glob
import os
import torch
from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from pinecone import Pinecone
from tqdm import tqdm
from sentence_transformers import SentenceTransformer
from utils.retry import with_retry

load_dotenv()

# --- Configuration ---
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "graphrag-benchmark")

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 100
BATCH_SIZE = 100
# Using a local embedding model to avoid Gemini
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

# --- Clients ---
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX_NAME)
embed_model = SentenceTransformer(EMBEDDING_MODEL_NAME)


def ingest_documents(input_path: str, namespace: str = "medical-rag"):
    """
    Ingest text from input_path into Pinecone using local embeddings.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )

    if os.path.isdir(input_path):
        filepaths = glob.glob(f"{input_path}/**/*.txt", recursive=True)
    else:
        filepaths = [input_path]

    all_chunks = []
    for filepath in tqdm(filepaths, desc="Chunking files"):
        with open(filepath, encoding="utf-8") as f:
            text = f.read()
            chunks = splitter.split_text(text)
            all_chunks.extend(chunks)

    print(f"Total chunks to ingest: {len(all_chunks)}")

    for i in tqdm(range(0, len(all_chunks), BATCH_SIZE), desc="Ingesting to Pinecone"):
        batch_chunks = all_chunks[i : i + BATCH_SIZE]
        
        # Local embedding generation
        embeddings = embed_model.encode(batch_chunks).tolist()
        
        vectors = []
        for j, (chunk, emb) in enumerate(zip(batch_chunks, embeddings)):
            vector_id = f"doc_{i+j}"
            vectors.append({
                "id": vector_id,
                "values": emb,
                "metadata": {"text": chunk}
            })
        
        index.upsert(vectors=vectors, namespace=namespace)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", type=str, default="./data/medical")
    parser.add_argument("--namespace", type=str, default="medical-rag")
    args = parser.parse_args()
    
    ingest_documents(args.path, args.namespace)
