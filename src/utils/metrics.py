"""
Token counting and pipeline metrics using tiktoken (cl100k_base).
All token counts come from tiktoken — never from provider-reported counts.
"""

import time
import tiktoken

enc = tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str) -> int:
    """Count tokens in a string using tiktoken cl100k_base encoding."""
    return len(enc.encode(text))


class PipelineMetrics:
    """Track prompt tokens, completion tokens, latency, and cost for a pipeline run."""

    def __init__(self, name: str):
        self.name = name
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.latency_ms = 0.0
        self.cost_usd = 0.0

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens

    def record(self, prompt: str, response: str, start_time: float):
        """Record metrics for a completed LLM call."""
        self.prompt_tokens = len(enc.encode(prompt))
        self.completion_tokens = len(enc.encode(response))
        self.latency_ms = (time.time() - start_time) * 1000
        total = self.prompt_tokens + self.completion_tokens
        self.cost_usd = total / 1_000_000 * 0.075  # approximate blended rate for comparison

    def to_dict(self) -> dict:
        """Return metrics as a dictionary with standardized keys."""
        return {
            "pipeline": self.name,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.prompt_tokens + self.completion_tokens,
            "latency_ms": round(self.latency_ms, 2),
            "cost_usd": round(self.cost_usd, 8),
        }
