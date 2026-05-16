"""
TigerGraph Agent Router — Advanced schema-aware query classification.
Routes medical queries to the optimal retriever or dynamic Cypher generation.
"""

import os
import re
import requests
from dotenv import load_dotenv
from typing import Dict, Any

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "models/gemma-4-26b-a4b-it")

# Schema-aware Prompt
AGENT_ROUTER_PROMPT = """You are the TigerGraph Agent Router.
Your goal is to route the user's medical query to the most efficient retrieval strategy based on the Graph Schema.

Graph Schema:
- Vertex Types:
  - Drug: Pharmaceutical substances (e.g., Metformin, Lisinopril)
  - Disease: Medical conditions (e.g., Diabetes, Hypertension)
  - Guideline: Clinical recommendations and protocols
  - DocumentChunk: Raw text segments from medical literature
- Edge Types:
  - INTERACTS_WITH: Connection between two Drugs (has severity: moderate/severe)
  - CONTRAINDICATED_FOR: Drug to Disease link indicating safety risk
  - TREATS: Drug to Disease link for therapeutic indication
  - MENTIONED_IN: Entity to DocumentChunk link

Routing Categories:
1. INTERACTION: Analysis of drug-drug or drug-disease interactions. (Retriever: hybrid)
2. DIAGNOSIS: Symptom-to-disease mapping or differential diagnosis. (Retriever: sibling)
3. CONTRADICTION: Conflicting guidelines or expert disagreements. (Retriever: community)
4. GENERATE_CYPHER: Questions requiring structural graph traversal, paths, or complex joins (e.g., "Find all paths from Drug A to Disease B").
5. GENERAL_RAG: General medical knowledge or simple entity lookup. (Retriever: hybrid)

Query: {query}

Instructions:
- Return ONLY a JSON object with "category" and "reasoning".
- Reasoning should be 1 sentence.

Response:"""

class TigerGraphAgentRouter:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model_name = os.getenv("LLM_MODEL", "models/gemma-4-26b-a4b-it")

    def route(self, query: str) -> Dict[str, Any]:
        """Route query using LLM with schema context."""
        from google import genai
        import json
        
        client = genai.Client(api_key=self.api_key)
        prompt = AGENT_ROUTER_PROMPT.format(query=query)

        try:
            response = client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config={
                    "temperature": 0.0,
                    "max_output_tokens": 200,
                    "response_mime_type": "application/json"
                }
            )
            
            raw_text = response.text.strip() if response.text else "{}"
            
            # Handle potential JSON wrapping in markdown
            json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = json.loads(raw_text)
            
            category = result.get("category", "GENERAL_RAG").upper()
            reasoning = result.get("reasoning", "LLM classified")
            
            return self._map_category_to_config(category, reasoning)
            
        except Exception as e:
            print(f"  [ROUTER] LLM routing failed, falling back to keyword: {e}")
            return self._fallback_route(query)

    def _map_category_to_config(self, category: str, reasoning: str) -> Dict[str, Any]:
        mapping = {
            "INTERACTION": {"retriever": "hybrid", "hop_depth": 3},
            "DIAGNOSIS":   {"retriever": "sibling", "hop_depth": 2},
            "CONTRADICTION": {"retriever": "community", "hop_depth": 2},
            "GENERATE_CYPHER": {"retriever": "cypher", "hop_depth": 0}, # Cypher handles hops
            "GENERAL_RAG": {"retriever": "hybrid", "hop_depth": 2},
        }
        
        config = mapping.get(category, mapping["GENERAL_RAG"])
        return {
            "category": category,
            "retriever": config["retriever"],
            "hop_depth": config["hop_depth"],
            "reasoning": reasoning,
            "confidence": "llm"
        }

    def _fallback_route(self, query: str) -> Dict[str, Any]:
        """Simple keyword fallback."""
        query_lower = query.lower()
        if any(w in query_lower for w in ["interact", "safe", "side effect"]):
            category = "INTERACTION"
        elif any(w in query_lower for w in ["diagnos", "symptom", "cause"]):
            category = "DIAGNOSIS"
        elif any(w in query_lower for w in ["path", "connect", "step", "how is"]):
            category = "GENERATE_CYPHER"
        else:
            category = "GENERAL_RAG"
            
        return self._map_category_to_config(category, "Fallback keyword match")

# Maintain backward compatibility with function-based calls if needed
def route_query(query: str, use_llm: bool = True) -> Dict[str, Any]:
    router = TigerGraphAgentRouter()
    return router.route(query)
