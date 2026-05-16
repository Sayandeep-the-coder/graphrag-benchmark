"""
Pydantic v2 models for the FastAPI dashboard backend.
"""

from pydantic import BaseModel


class CompareRequest(BaseModel):
    """Request body for the /compare endpoint."""
    query: str
    ground_truth: str | None = None
    namespace: str = "medical-rag"
    top_k: int = 3


class PipelineResult(BaseModel):
    """Result from a single pipeline run."""
    answer: str
    metrics: dict
    # Pipeline-specific optional fields
    chunks_retrieved: int | None = None
    similarity_scores: list[float] | None = None
    entities_retrieved: list | None = None
    retriever: str | None = None
    hop_depth: int | None = None
    query_category: str | None = None
    route_confidence: str | None = None
    clinical_signals: dict | None = None


class CompareResponse(BaseModel):
    """Response from the /compare endpoint with all 3 pipeline results."""
    llm_only: PipelineResult
    basic_rag: PipelineResult
    graphrag: PipelineResult | None = None
    token_reduction_pct: float | None = None
    accuracy: dict | None = None

class HealthResponse(BaseModel):
    """Response from the /health endpoint."""
    status: str


class IngestStatus(BaseModel):
    """Response from the /ingest/* endpoints."""
    pipeline: str
    status: str
    message: str


class BenchmarkQuery(BaseModel):
    """Model for a single benchmark query."""
    category: str
    question: str
    correct_answer: str
    hop_depth: int | None = None


class BenchmarkSampleRequest(BaseModel):
    """Request body for running a single benchmark sample."""
    index: int
    namespace: str = "medical-rag"
    top_k: int = 3
