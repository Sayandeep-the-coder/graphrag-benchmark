import os
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec

load_dotenv()
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index_name = os.getenv("PINECONE_INDEX_NAME", "graphrag-benchmark")

# Check if index exists
if index_name not in pc.list_indexes().names():
    print(f"Creating Pinecone index: {index_name}...")
    pc.create_index(
        name=index_name,
        dimension=int(os.getenv("PINECONE_EMBEDDING_DIMENSION", "1024")),
        metric="cosine",
        spec=ServerlessSpec(
            cloud='aws',
            region='us-east-1'
        )
    )
    print("Index created successfully!")
else:
    print(f"Pinecone index '{index_name}' already exists.")
