# Pipeline Implementation Guide

Detailed implementation reference for all three inference pipelines.

---

## Pipeline 1 — LLM Only

**Purpose:** Worst-case token baseline. No retrieval. LLM answers from training memory alone.

**Token profile:** Low prompt tokens, high risk of hallucination.

```python
# pipelines/pipeline1_llm_only.py
import google.generativeai as genai
import time
from utils.metrics import PipelineMetrics
from utils.retry import with_retry

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

def run(query: str) -> dict:
    metrics = PipelineMetrics("LLM-Only")
    prompt = f"Answer the following question accurately.\n\nQuestion: {query}\n\nAnswer:"

    start = time.time()
    response = with_retry(lambda: model.generate_content(prompt))
    answer = response.text
    metrics.record(prompt, answer, start)

    return {"answer": answer, "metrics": metrics.to_dict()}
```

**When to use P1 results:** Show as ceiling for token cost + floor for accuracy. Every other pipeline should beat it on accuracy. GraphRAG should beat it on tokens.

---

## Pipeline 2 — Basic RAG (Pinecone)

**Purpose:** Industry-standard baseline. Vector similarity retrieval + LLM synthesis.

**Token profile:** High prompt tokens (5 chunks × ~200 tokens each = ~1000 extra tokens per query).

### Ingest

```python
# pipelines/pipeline2_basic_rag/ingest.py
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer
from langchain.text_splitter import RecursiveCharacterTextSplitter
import glob, os
from tqdm import tqdm

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index(os.getenv("PINECONE_INDEX_NAME"))
embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

CHUNK_SIZE = 512    # tune: smaller = more precise = fewer tokens
CHUNK_OVERLAP = 64
BATCH_SIZE = 100    # Pinecone upsert batch size

def ingest_documents(docs_folder: str):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )

    all_chunks, all_ids, all_metadata = [], [], []

    for filepath in tqdm(glob.glob(f"{docs_folder}/**/*.txt", recursive=True)):
        with open(filepath, encoding="utf-8") as f:
            text = f.read()

        chunks = splitter.split_text(text)
        for i, chunk in enumerate(chunks):
            chunk_id = f"{os.path.basename(filepath)}_chunk_{i}"
            all_chunks.append(chunk)
            all_ids.append(chunk_id)
            all_metadata.append({"source": filepath, "chunk_index": i, "text": chunk})

    print(f"Total chunks: {len(all_chunks)}")

    # Batch embed + upsert
    for i in range(0, len(all_chunks), BATCH_SIZE):
        batch_texts = all_chunks[i:i+BATCH_SIZE]
        batch_ids = all_ids[i:i+BATCH_SIZE]
        batch_meta = all_metadata[i:i+BATCH_SIZE]

        embeddings = embedder.encode(batch_texts).tolist()
        vectors = list(zip(batch_ids, embeddings, batch_meta))
        index.upsert(vectors=vectors, namespace="wikipedia-2025")

    print("Pinecone ingest complete.")

if __name__ == "__main__":
    ingest_documents("./data/wikipedia")
```

### Query

```python
# pipelines/pipeline2_basic_rag/query.py
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer
import google.generativeai as genai
import time, os
from utils.metrics import PipelineMetrics
from utils.retry import with_retry

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index(os.getenv("PINECONE_INDEX_NAME"))
embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

TOP_K = 5  # tune: higher = more context = more tokens

def run(query: str, top_k: int = TOP_K) -> dict:
    metrics = PipelineMetrics("Basic-RAG")

    # Step 1: embed query
    query_embedding = embedder.encode(query).tolist()

    # Step 2: Pinecone similarity search
    results = index.query(
        vector=query_embedding,
        top_k=top_k,
        namespace="wikipedia-2025",
        include_metadata=True
    )

    chunks = [match["metadata"]["text"] for match in results["matches"]]
    context = "\n\n---\n\n".join(chunks)

    # Step 3: build prompt + call Gemini
    prompt = f"""You are a helpful assistant. Use ONLY the context below to answer.

Context:
{context}

Question: {query}

Answer:"""

    start = time.time()
    response = with_retry(lambda: model.generate_content(prompt))
    answer = response.text
    metrics.record(prompt, answer, start)

    return {
        "answer": answer,
        "metrics": metrics.to_dict(),
        "chunks_retrieved": len(chunks),
        "similarity_scores": [m["score"] for m in results["matches"]]
    }
```

### Tuning Guide (Pipeline 2)

| Parameter | Default | Lower → | Higher → |
|-----------|---------|---------|---------|
| `chunk_size` | 512 | More precise, less context | More context, more tokens |
| `chunk_overlap` | 64 | Risk missing context | Redundancy |
| `top_k` | 5 | Fewer tokens, less coverage | More tokens, better recall |

---

## Pipeline 3 — GraphRAG (TigerGraph)

**Purpose:** Graph-powered retrieval. Multi-hop entity traversal = precise, minimal context.

**Token profile:** Lowest prompt tokens — graph returns only relevant entity facts.

### Ingest

```python
# pipelines/pipeline3_graphrag/ingest.py
import requests, glob, os
from tqdm import tqdm

GRAPHRAG_URL = os.getenv("GRAPHRAG_SERVICE_URL", "http://localhost:8000")
BATCH_SIZE = 10

def ingest_documents(docs_folder: str):
    filepaths = glob.glob(f"{docs_folder}/**/*.txt", recursive=True)
    print(f"Ingesting {len(filepaths)} documents into TigerGraph...")

    for i in tqdm(range(0, len(filepaths), BATCH_SIZE)):
        batch = filepaths[i:i+BATCH_SIZE]
        batch_docs = []

        for filepath in batch:
            with open(filepath, encoding="utf-8") as f:
                text = f.read()
            batch_docs.append({
                "content": text,
                "filename": os.path.basename(filepath),
                "source": "wikipedia"
            })

        resp = requests.post(
            f"{GRAPHRAG_URL}/documents/batch",
            json={"documents": batch_docs},
            timeout=120
        )

        if resp.status_code != 200:
            print(f"Batch {i} failed: {resp.text}")

    print("TigerGraph GraphRAG ingest complete.")
    print("Entity extraction and relationship mapping done by service automatically.")

if __name__ == "__main__":
    ingest_documents("./data/wikipedia")
```

### Query

```python
# pipelines/pipeline3_graphrag/query.py
import requests, time, os
from utils.metrics import PipelineMetrics

GRAPHRAG_URL = os.getenv("GRAPHRAG_SERVICE_URL", "http://localhost:8000")

def run(
    query: str,
    retriever: str = "hybrid",   # "hybrid" | "community" | "sibling"
    hop_depth: int = 2           # tune: 1=fast/cheap, 3=deep/expensive
) -> dict:
    metrics = PipelineMetrics("GraphRAG")

    payload = {
        "query": query,
        "retriever": retriever,
        "hop_depth": hop_depth,
    }

    start = time.time()
    resp = requests.post(
        f"{GRAPHRAG_URL}/query",
        json=payload,
        timeout=60
    )
    data = resp.json()

    answer = data.get("answer", "")
    metrics.latency_ms = (time.time() - start) * 1000
    metrics.prompt_tokens = data.get("prompt_tokens", 0)
    metrics.completion_tokens = data.get("completion_tokens", 0)
    metrics.cost_usd = (
        metrics.prompt_tokens + metrics.completion_tokens
    ) / 1e6 * 0.075

    return {
        "answer": answer,
        "metrics": metrics.to_dict(),
        "entities_retrieved": data.get("entities", []),
        "hop_depth": hop_depth,
        "retriever": retriever,
    }
```

### Retriever Modes

| Retriever | Best For | Token Cost |
|-----------|---------|-----------|
| `hybrid` | General queries — balances precision + recall | Medium |
| `community` | Topic-level questions — returns community summaries | Low |
| `sibling` | Document-adjacent chunks — preserves narrative flow | Medium |

### Tuning Guide (Pipeline 3)

| Parameter | Default | Effect |
|-----------|---------|--------|
| `hop_depth` | 2 | 1=fewer tokens, 3=more complete answer |
| `retriever` | hybrid | Switch per query type |
| `chunk_size` (in graphrag/.env) | 512 | Same as P2 — tune together |

---

## Metrics Utility (Shared)

```python
# utils/metrics.py
import time, tiktoken

enc = tiktoken.get_encoding("cl100k_base")

class PipelineMetrics:
    def __init__(self, name: str):
        self.name = name
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.latency_ms = 0.0
        self.cost_usd = 0.0

    def record(self, prompt: str, response: str, start_time: float):
        self.prompt_tokens = len(enc.encode(prompt))
        self.completion_tokens = len(enc.encode(response))
        self.latency_ms = (time.time() - start_time) * 1000
        total = self.prompt_tokens + self.completion_tokens
        self.cost_usd = total / 1_000_000 * 0.075  # Gemini 1.5 Flash pricing

    def to_dict(self) -> dict:
        return {
            "pipeline": self.name,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.prompt_tokens + self.completion_tokens,
            "latency_ms": round(self.latency_ms, 2),
            "cost_usd": round(self.cost_usd, 8),
        }
```

## Retry Utility (Shared)

```python
# utils/retry.py
import time, functools

def with_retry(fn, max_retries=3, base_delay=2.0):
    for attempt in range(max_retries):
        try:
            return fn()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            delay = base_delay * (2 ** attempt)
            print(f"Retry {attempt+1}/{max_retries} after {delay}s: {e}")
            time.sleep(delay)
```
