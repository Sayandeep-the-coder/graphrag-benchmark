"""Shared embedding helpers for Pinecone-backed RAG."""

import os
from pinecone import Pinecone

EMBED_MODEL = os.getenv("PINECONE_EMBED_MODEL", "llama-text-embed-v2")
EMBED_DIMENSION = int(os.getenv("PINECONE_EMBEDDING_DIMENSION", "1024"))


def get_pinecone_client() -> Pinecone:
    return Pinecone(api_key=os.getenv("PINECONE_API_KEY"))


def embed_texts(
    pc: Pinecone,
    texts: list[str],
    *,
    input_type: str,
) -> list[list[float]]:
    """Embed texts using Pinecone's hosted inference API (llama-text-embed-v2)."""
    if not texts:
        return []
    result = pc.inference.embed(
        model=EMBED_MODEL,
        inputs=texts,
        parameters={"input_type": input_type, "truncate": "END"},
    )
    return [vec.values for vec in result.data]
