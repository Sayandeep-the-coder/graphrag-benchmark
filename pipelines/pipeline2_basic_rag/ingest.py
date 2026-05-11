import argparse
import glob
import os

from dotenv import load_dotenv
from google import genai
from langchain.text_splitter import RecursiveCharacterTextSplitter
from pinecone import Pinecone
from tqdm import tqdm
from utils.retry import with_retry

load_dotenv()

# --- Configuration ---
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "graphrag-benchmark")

CHUNK_SIZE = 1000  # Increased for medical data to keep disease info together
CHUNK_OVERLAP = 100
BATCH_SIZE = 100  # Pinecone upsert max batch size
EMBEDDING_MODEL = "models/gemini-embedding-001"

# --- Clients ---
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX_NAME)
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def ingest_documents(input_path: str, namespace: str = "medical-rag"):
    """
    Ingest text from input_path (file or folder) into Pinecone.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )

    if os.path.isdir(input_path):
        filepaths = glob.glob(f"{input_path}/**/*.txt", recursive=True)
        print(f"Found {len(filepaths)} files in {input_path}")
    else:
        filepaths = [input_path]
        print(f"Processing single file: {input_path}")

    all_chunks = []
    all_ids = []
    all_metadata = []

    for filepath in tqdm(filepaths, desc="Chunking files"):
        with open(filepath, encoding="utf-8") as f:
            text = f.read()

        # For the medical knowledge base, we split by the dashed line separator first
        # to avoid splitting diseases across chunks if possible
        if "---" in text and "Disease:" in text:
            # Special handling for medical knowledge base
            raw_docs = [d.strip() for d in text.split("-" * 50) if d.strip()]
            chunks = []
            for doc in raw_docs:
                if len(doc) > CHUNK_SIZE:
                    chunks.extend(splitter.split_text(doc))
                else:
                    chunks.append(doc)
        else:
            chunks = splitter.split_text(text)

        for i, chunk in enumerate(chunks):
            # Unique ID based on filename and chunk index
            fname = os.path.basename(filepath).replace(".", "_")
            chunk_id = f"{fname}_{namespace}_{i}"
            all_chunks.append(chunk)
            all_ids.append(chunk_id)
            all_metadata.append({
                "text": chunk,
                "source": filepath,
                "chunk_index": i,
                "namespace": namespace
            })

    print(f"Total chunks: {len(all_chunks)}")

    # Batch embed + upsert
    upserted = 0
    for i in tqdm(range(0, len(all_chunks), BATCH_SIZE), desc="Embedding & upserting"):
        batch_texts = all_chunks[i : i + BATCH_SIZE]
        batch_ids = all_ids[i : i + BATCH_SIZE]
        batch_meta = all_metadata[i : i + BATCH_SIZE]

        # Call Gemini Embedding API with retry
        response = with_retry(lambda: client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=batch_texts
        ))
        
        if response is None or not hasattr(response, "embeddings") or not response.embeddings:
            print(f"Warning: Gemini embedding API returned an invalid response for batch {i}. Skipping.")
            continue

        embeddings = [e.values for e in response.embeddings]
        
        vectors = list(zip(batch_ids, embeddings, batch_meta))
        index.upsert(vectors=vectors, namespace=namespace)
        upserted += len(vectors)

    print(f"\n[SUCCESS] Pinecone ingest complete.")
    print(f"   Namespace       : {namespace}")
    print(f"   Vectors upserted: {upserted}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest documents into Pinecone for RAG.")
    parser.add_argument("--path", type=str, default="./data/wikipedia", help="Path to file or folder to ingest.")
    parser.add_argument("--namespace", type=str, default="medical-rag", help="Pinecone namespace.")
    
    args = parser.parse_args()
    
    ingest_documents(args.path, args.namespace)
