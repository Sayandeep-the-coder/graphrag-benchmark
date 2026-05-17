# Frontend-to-Backend Ingestion Flow

## Overview
When you click "Initialize Pipeline" for TigerGraph Knowledge Extraction on the frontend, the ingestion process now uses the fixed `tigergraph_ingest.py` with document count validation.

## Flow Chain

### 1. **Frontend Trigger** → `IngestionManager.jsx`
```javascript
// File: src/frontend/src/components/IngestionManager.jsx (Line 32)
const triggerIngest = async (type) => {
  const response = await fetch(`http://localhost:8080/ingest/${type}`, {
    method: 'POST'
  });
  // For GraphRAG: type = 'graphrag'
}
```

### 2. **Backend Endpoint** → `src/server/main.py`
```python
# File: src/server/main.py (Lines 246-252)
def _run_graphrag_ingest():
    from src.graphrag.pipeline.ingest import ingest_documents
    ingest_documents("./data/processed", format="csv")

@app.post("/ingest/graphrag", response_model=IngestStatus)
async def ingest_graphrag(background_tasks: BackgroundTasks):
    background_tasks.add_task(_run_graphrag_ingest)
    return IngestStatus(pipeline="graphrag", status="started", message="Ingest running")
```

### 3. **Pipeline Ingest Wrapper** → `src/graphrag/pipeline/ingest.py`
```python
# File: src/graphrag/pipeline/ingest.py (Lines 21-22)
def ingest_documents(docs_folder: str = "./data/processed", rebuild: bool = True, format: str = "csv"):
    result = ingest_to_savanna(docs_folder, rebuild=rebuild, format=format)
```

### 4. **Fixed Ingest Implementation** → `src/utils/tigergraph_ingest.py`
```python
# File: src/utils/tigergraph_ingest.py (Line 275)
def ingest_to_savanna(
    docs_folder: str = "./data/processed",
    *,
    graphrag_url: str | None = None,
    rebuild: bool = True,
    rebuild_timeout: int = 600,
    format: str = "csv",
    rows_per_file: int = 100,
) -> dict:
```

## Fixed Validation Logic

The `ingest_to_savanna()` function now includes:

1. **Upfront Source Count** (Line 287)
   ```python
   records = _collect_document_records(docs_folder)
   source_document_count = len(records)
   ```

2. **CSV Primary Load** (Lines 297-319)
   - Attempts to load all source records via CSV shards

3. **JSONL Fallback** (Lines 320-331)
   - If CSV under-loads, automatically falls back to JSONL format
   - Retries load with better error handling

4. **Final Validation** (Lines 333-338)
   ```python
   document_count = conn.getVertexCount("Document")
   if document_count < source_document_count:
       raise RuntimeError(
           "Document ingest appears incomplete: expected at least "
           f"{source_document_count} source records but TigerGraph currently has "
           f"{document_count} Document vertices..."
       )
   ```

## Testing the Flow

To test end-to-end ingestion from the frontend:

1. **Start the backend**:
   ```bash
   python src/server/main.py
   ```

2. **Start the frontend** (in separate terminal):
   ```bash
   cd src/frontend
   npm run dev
   ```

3. **Trigger ingestion** from the UI:
   - Navigate to `http://localhost:3000`
   - Click "Initialize Pipeline" under "TigerGraph Knowledge Extraction"
   - Monitor the backend terminal for validation messages

4. **Expected output** on success:
   ```
   Ingesting from ./data/processed into TigerGraph Savanna via CSV...
     Format        : csv
     Load files    : 131
     Documents     : 13168
     Content nodes : 13168
     Doc chunks    : [will be calculated]
     Entities      : [will be extracted]
   
   [SUCCESS] Savanna load complete.
   ```

5. **Error handling** if validation fails:
   - Clear error message showing expected vs. actual document count
   - Logs include shard file paths for manual inspection
   - No silent failures—ingestion must reach 13,168 documents or error

## Key Changes from Previous Implementation

- ✅ Counts source corpus **before** loading (prevents silent failure)
- ✅ Loads CSV **first** (optimized for TigerGraph's CSV parser)
- ✅ Falls back to **JSONL** if CSV under-loads
- ✅ **Validates** final count against source count
- ✅ **Clear error messages** with actionable diagnostics

## Related Files
- Frontend: [src/frontend/src/components/IngestionManager.jsx](src/frontend/src/components/IngestionManager.jsx)
- Backend: [src/server/main.py](src/server/main.py#L246)
- Ingestion: [src/graphrag/pipeline/ingest.py](src/graphrag/pipeline/ingest.py)
- Fixed Core: [src/utils/tigergraph_ingest.py](src/utils/tigergraph_ingest.py#L275)
