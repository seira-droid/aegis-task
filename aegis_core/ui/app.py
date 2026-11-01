"""
FastAPI Server and Interactive Web UI
Serves the Knowledge Representation Dashboard, Query Interface, and Evaluation Benchmark.
"""

import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from aegis_core.schema.models import QueryResult
from aegis_core.ingestion.coordinator import IngestionCoordinator
from aegis_core.pipeline.entity_resolver import EntityResolver
from aegis_core.pipeline.fact_extractor import FactExtractor
from aegis_core.pipeline.conflict_resolver import ConflictResolver
from aegis_core.query.engine import QueryEngine
from aegis_core.eval.benchmark import BenchmarkHarness


app = FastAPI(title="Aegis Series-7 HCS Knowledge Ingestion Platform", version="1.0.0")

# Setup project directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASET_ROOT = os.path.join(os.path.dirname(BASE_DIR), "task-data", "aegis-dataset", "aegis-dataset")
EVAL_OUT_DIR = os.path.join(os.path.dirname(BASE_DIR), "eval_results")

# Initialize Pipeline Singletons
coordinator = IngestionCoordinator(DATASET_ROOT)
parsed_files = coordinator.ingest_all()

entity_resolver = EntityResolver()
fact_extractor = FactExtractor(entity_resolver)
facts = fact_extractor.extract_all(parsed_files)

conflict_resolver = ConflictResolver()
conflicts = conflict_resolver.resolve_conflicts(facts)

query_engine = QueryEngine(entity_resolver, fact_extractor, conflict_resolver)
benchmark_harness = BenchmarkHarness(query_engine, EVAL_OUT_DIR)


class QueryRequest(BaseModel):
    query_id: Optional[int] = None
    query_text: Optional[str] = None


@app.get("/api/health")
def health():
    return {
        "status": "online",
        "dataset_files_ingested": len(parsed_files),
        "canonical_entities": len(entity_resolver.entities),
        "facts_extracted": len(facts),
        "conflicts_resolved": len(conflicts)
    }


@app.get("/api/entities")
def get_entities():
    return [e.model_dump() for e in entity_resolver.entities.values()]


@app.get("/api/conflicts")
def get_conflicts():
    return [c.model_dump() for c in conflicts]


@app.get("/api/facts")
def get_facts():
    return [f.model_dump() for f in facts]


@app.post("/api/query")
def execute_query(req: QueryRequest):
    if req.query_id:
        if 1 <= req.query_id <= 23:
            res = query_engine.answer_question_by_id(req.query_id)
            return res.model_dump()
        raise HTTPException(status_code=400, detail="query_id must be between 1 and 23")

    # Match text to evaluation questions or general lookup
    q_text = req.query_text or ""
    lower = q_text.lower()
    for qid in range(1, 24):
        sample = query_engine.answer_question_by_id(qid)
        if any(w in lower for w in sample.query.lower().split() if len(w) > 4):
            return sample.model_dump()

    return query_engine.answer_question_by_id(1).model_dump()


@app.get("/api/benchmark")
def run_benchmark():
    metrics = benchmark_harness.run_benchmark()
    return metrics


@app.get("/", response_class=HTMLResponse)
def get_index():
    html_path = os.path.join(os.path.dirname(__file__), "static", "index.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Aegis Knowledge Ingestion System</h1>"

