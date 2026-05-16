import os
import time

from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "graphrag-benchmark")
PINECONE_CLOUD = os.getenv("PINECONE_CLOUD", "aws")
PINECONE_REGION = os.getenv("PINECONE_REGION", os.getenv("PINECONE_ENVIRONMENT", "us-east-1"))
TARGET_DIMENSION = int(os.getenv("PINECONE_EMBEDDING_DIMENSION", "1024"))


def get_index_names(pc: Pinecone) -> set[str]:
    return set(pc.list_indexes().names())


def wait_for_index_absence(pc: Pinecone, index_name: str, *, poll_seconds: int = 1) -> None:
    while index_name in get_index_names(pc):
        time.sleep(poll_seconds)


def wait_for_index_ready(pc: Pinecone, index_name: str, *, poll_seconds: int = 1) -> None:
    while not pc.describe_index(index_name).status["ready"]:
        time.sleep(poll_seconds)


def recreate_index() -> None:
    if not PINECONE_API_KEY:
        raise RuntimeError("PINECONE_API_KEY is not set")

    pc = Pinecone(api_key=PINECONE_API_KEY)

    print(f"Checking for existing index: {PINECONE_INDEX_NAME}...")

    if PINECONE_INDEX_NAME in get_index_names(pc):
        print(f"Deleting existing index {PINECONE_INDEX_NAME} (dimension mismatch)...")
        pc.delete_index(PINECONE_INDEX_NAME)
        wait_for_index_absence(pc, PINECONE_INDEX_NAME)
        print("Deletion complete.")

    print(f"Creating new index {PINECONE_INDEX_NAME} with dimension {TARGET_DIMENSION}...")
    pc.create_index(
        name=PINECONE_INDEX_NAME,
        dimension=TARGET_DIMENSION,
        metric="cosine",
        spec=ServerlessSpec(
            cloud=PINECONE_CLOUD,
            region=PINECONE_REGION,
        ),
    )

    print("Waiting for index to be ready...")
    wait_for_index_ready(pc, PINECONE_INDEX_NAME)

    print("New index is ready!")


if __name__ == "__main__":
    recreate_index()
