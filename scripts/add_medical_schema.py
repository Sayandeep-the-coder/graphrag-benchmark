#!/usr/bin/env python3
"""Load medical vertices/edges into existing GraphRAG graph."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv
from pyTigerGraph import TigerGraphConnection

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

# Medical schema - vertices and edges to ADD to GraphRAG
MEDICAL_SCHEMA = """
// Drug vertex
CREATE VERTEX Drug (
  PRIMARY_ID drug_id STRING,
  name STRING,
  generic_name STRING,
  drug_class STRING,
  half_life_hours FLOAT,
  mechanism_of_action STRING
) WITH STATS="OUTDEGREE_BY_EDGETYPE", PRIMARY_ID_AS_ATTRIBUTE="true"

// Enzyme vertex
CREATE VERTEX Enzyme (
  PRIMARY_ID enzyme_id STRING,
  name STRING,
  family STRING,
  inducers SET<STRING>,
  inhibitors SET<STRING>
) WITH STATS="OUTDEGREE_BY_EDGETYPE", PRIMARY_ID_AS_ATTRIBUTE="true"

// Adverse_Event vertex
CREATE VERTEX Adverse_Event (
  PRIMARY_ID ae_id STRING,
  description STRING,
  severity STRING
) WITH STATS="OUTDEGREE_BY_EDGETYPE", PRIMARY_ID_AS_ATTRIBUTE="true"

// Disease vertex
CREATE VERTEX Disease (
  PRIMARY_ID disease_id STRING,
  name STRING,
  icd10_code STRING,
  prevalence_per_100k FLOAT,
  severity_rating STRING
) WITH STATS="OUTDEGREE_BY_EDGETYPE", PRIMARY_ID_AS_ATTRIBUTE="true"

// Symptom vertex
CREATE VERTEX Symptom (
  PRIMARY_ID symptom_id STRING,
  description STRING,
  systemic BOOL,
  severity STRING
) WITH STATS="OUTDEGREE_BY_EDGETYPE", PRIMARY_ID_AS_ATTRIBUTE="true"

// Treatment_Guideline vertex
CREATE VERTEX Treatment_Guideline (
  PRIMARY_ID guideline_id STRING,
  title STRING,
  issuing_body STRING,
  year INT,
  recommendation STRING,
  evidence_level STRING
) WITH STATS="OUTDEGREE_BY_EDGETYPE", PRIMARY_ID_AS_ATTRIBUTE="true"

// Drug-Drug interaction
CREATE DIRECTED EDGE INTERACTS_WITH (
  FROM Drug, TO Drug,
  severity STRING,
  mechanism STRING,
  effect STRING,
  evidence_strength STRING
) WITH REVERSE_EDGE="REVERSE_INTERACTS_WITH"

// Drug metabolism
CREATE DIRECTED EDGE METABOLIZED_BY (
  FROM Drug, TO Enzyme,
  is_substrate BOOL,
  is_inducer BOOL,
  is_inhibitor BOOL
) WITH REVERSE_EDGE="REVERSE_METABOLIZED_BY"

// Drug adverse events
CREATE DIRECTED EDGE CAUSES (
  FROM Drug, TO Adverse_Event,
  frequency FLOAT,
  severity STRING,
  onset_hours FLOAT
) WITH REVERSE_EDGE="REVERSE_CAUSES"

// Drug treats disease
CREATE DIRECTED EDGE TREATS (
  FROM Drug, TO Disease,
  first_line BOOL,
  evidence_level STRING
) WITH REVERSE_EDGE="REVERSE_TREATS"

// Drug contraindicated for disease
CREATE DIRECTED EDGE CONTRAINDICATED_FOR (
  FROM Drug, TO Disease,
  reason STRING,
  absolute BOOL
) WITH REVERSE_EDGE="REVERSE_CONTRAINDICATED_FOR"

// Disease presents with symptom
CREATE DIRECTED EDGE PRESENTS_AS (
  FROM Disease, TO Symptom,
  frequency FLOAT,
  early_sign BOOL
) WITH REVERSE_EDGE="REVERSE_PRESENTS_AS"

// Symptom indicates disease
CREATE DIRECTED EDGE INDICATES (
  FROM Symptom, TO Disease,
  specificity FLOAT,
  sensitivity FLOAT
) WITH REVERSE_EDGE="REVERSE_INDICATES"

// Disease comorbidity
CREATE DIRECTED EDGE COMORBID_WITH (
  FROM Disease, TO Disease,
  correlation_strength FLOAT,
  bidirectional BOOL
) WITH REVERSE_EDGE="REVERSE_COMORBID_WITH"

// Guideline recommends drug
CREATE DIRECTED EDGE RECOMMENDED_BY (
  FROM Treatment_Guideline, TO Drug,
  for_disease STRING,
  year INT
) WITH REVERSE_EDGE="REVERSE_RECOMMENDED_BY"

// Guideline contradicts guideline
CREATE DIRECTED EDGE CONTRADICTS (
  FROM Treatment_Guideline, TO Treatment_Guideline,
  on_drug STRING,
  reason STRING
) WITH REVERSE_EDGE="REVERSE_CONTRADICTS"
"""


def add_medical_schema(graph_name: str = "GraphRAG"):
    """Add medical schema to existing TigerGraph graph."""
    print(f"[*] Adding medical schema to graph: {graph_name}")

    # Connect to TigerGraph
    host = os.getenv("TG_HOST", "").strip().rstrip("/")
    user = os.getenv("TG_USERNAME", "").strip()
    password = os.getenv("TG_PASSWORD", "").strip()
    restpp = os.getenv("TG_RESTPP_PORT", "443").strip()
    gs = os.getenv("TG_GSQL_PORT", "14240").strip()

    if not all([host, user, password]):
        print("[ERROR] TG_HOST, TG_USERNAME, TG_PASSWORD required in .env")
        return False

    print(f"[*] Connecting to TigerGraph at {host}...")
    try:
        conn = TigerGraphConnection(
            host=host,
            username=user,
            password=password,
            restppPort=restpp,
            gsPort=gs,
        )
        if conn.restppPort == conn.gsPort and "/restpp" not in conn.restppUrl:
            conn.restppUrl = conn.restppUrl + "/restpp"
        token = conn.getToken()[0]
        conn = TigerGraphConnection(
            host=host,
            username=user,
            password=password,
            restppPort=restpp,
            gsPort=gs,
            apiToken=token,
        )
        if conn.restppPort == conn.gsPort and "/restpp" not in conn.restppUrl:
            conn.restppUrl = conn.restppUrl + "/restpp"
        print("[✓] Connected")
    except Exception as e:
        print(f"[ERROR] Connection failed: {e}")
        return False

    # Execute medical schema
    print(f"[*] Adding medical vertices and edges to {graph_name}...")
    gsql_cmd = f"USE GLOBAL\nUSE GRAPH {graph_name}\nBEGIN\n{MEDICAL_SCHEMA}\nEND"
    try:
        result = conn.gsql(gsql_cmd)
        print(f"[✓] Medical schema added successfully")
        if result:
            print(f"\nResult:\n{result}")
        return True
    except Exception as e:
        error_msg = str(e)
        if "already exists" in error_msg.lower():
            print(f"[✓] Medical schema vertices/edges already exist")
            return True
        print(f"[ERROR] Failed to add schema: {e}")
        return False


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Add medical schema to GraphRAG graph")
    parser.add_argument(
        "--graph",
        type=str,
        default="GraphRAG",
        help="Graph name to add schema to",
    )
    args = parser.parse_args()

    success = add_medical_schema(args.graph)
    sys.exit(0 if success else 1)
