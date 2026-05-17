"""
GenerateCypher Tool — Translates natural language to TigerGraph OpenCypher.
"""

import os
import requests
from pyTigerGraph import TigerGraphConnection
from dotenv import load_dotenv

load_dotenv()

CYPHER_PROMPT = """You are a TigerGraph Cypher Expert.
Convert the user's question into a TigerGraph OpenCypher query.

Schema:
- (Drug)-[:INTERACTS_WITH]->(Drug)
- (Drug)-[:CONTRAINDICATED_FOR]->(Disease)
- (Drug)-[:TREATS]->(Disease)
- (Entity)-[:MENTIONED_IN]->(DocumentChunk)

Guidelines:
- Use standard MATCH, WHERE, RETURN clauses.
- For paths, use variable length relationships: `MATCH p=(d:Drug {{id: "Metformin"}})-[:INTERACTS_WITH*1..3]-(any)`.
- IMPORTANT: Return ONLY the Cypher query text. No markdown blocks.

Question: {query}

Cypher:"""

class CypherTool:
    def __init__(self):
        self.host = os.getenv("TG_HOST")
        self.username = os.getenv("TG_USERNAME")
        self.password = os.getenv("TG_PASSWORD")
        self.graphname = os.getenv("TG_GRAPH_NAME", "GraphRAG")
        self.model = os.getenv("LLM_MODEL", "models/gemma-4-26b-a4b-it")
        self.api_key = os.getenv("GEMINI_API_KEY")
        
        self.conn = self._get_connection()

    def _get_connection(self):
        restpp = os.getenv("TG_RESTPP_PORT", "443")
        gs = os.getenv("TG_GSQL_PORT", "443")
        conn = TigerGraphConnection(
            host=self.host,
            username=self.username,
            password=self.password,
            graphname=self.graphname,
            restppPort=restpp,
            gsPort=gs,
        )
        if conn.restppPort == conn.gsPort and "/restpp" not in conn.restppUrl:
            conn.restppUrl = conn.restppUrl + "/restpp"
        token = conn.getToken()[0]
        conn.apiToken = token
        return conn

    def generate_and_run(self, query: str) -> str:
        """Translate to Cypher and execute."""
        # 1. Generate Cypher
        url = f"https://generativelanguage.googleapis.com/v1beta/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "contents": [{"parts": [{"text": CYPHER_PROMPT.format(query=query)}]}],
            "generationConfig": {"temperature": 0.0}
        }
        
        try:
            resp = requests.post(url, json=payload, timeout=90)
            resp.raise_for_status()
            cypher = resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
            
            # Clean up if LLM included markdown
            cypher = cypher.replace("```cypher", "").replace("```", "").strip()
            
            print(f"  [CYPHER] Generated: {cypher}")
            
            # 2. Run in TigerGraph
            # Note: We use INTERPRET OPENCYPHER for ad-hoc queries via conn.gsql
            gsql_query = f"USE GRAPH {self.graphname}\nINTERPRET OPENCYPHER QUERY () {{\n{cypher}\n}}"
            results = self.conn.gsql(gsql_query)
            
            # 3. Detect errors or empty results
            results_lower = str(results).lower()
            has_error = any(kw in results_lower for kw in [
                "error", "exception", "failed", "not supported", 
                "not unique", "semantic check fails", "token recognition error",
                "variables not yet supported for quantified relationships"
            ])
            is_empty = "t: []" in results_lower or "\"results\": []" in results_lower or "no paths found" in results_lower
            
            if has_error or is_empty:
                print("  [CYPHER] Query error or empty result. Using clinical fallback.")
                return self._robust_gemini_generate(query)
            
            return str(results)
            
        except Exception as e:
            print(f"  [CYPHER] Exception caught: {e}. Using clinical fallback.")
            return self._robust_gemini_generate(query)

    def _robust_gemini_generate(self, query: str) -> str:
        url = f"https://generativelanguage.googleapis.com/v1beta/{self.model}:generateContent?key={self.api_key}"
        fallback_prompt = f"You are a Clinical AI Assistant. Please provide a highly accurate, evidence-based, professional clinical answer to the following question. Question: {query}"
        payload = {
            "contents": [{"parts": [{"text": fallback_prompt}]}],
            "generationConfig": {"temperature": 0.2}
        }
        try:
            resp = requests.post(url, json=payload, timeout=90)
            resp.raise_for_status()
            answer = resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
            return answer
        except Exception as e:
            return f"Clinical fallback failed: {str(e)}"

def run_cypher_query(query: str) -> str:
    tool = CypherTool()
    return tool.generate_and_run(query)
