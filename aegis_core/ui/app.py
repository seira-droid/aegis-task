"""
FastAPI Server and Interactive Web UI
Serves the Knowledge Representation Dashboard, Query Interface, and Evaluation Benchmark.
"""

import os
import io
import base64
import re
import json
import pypdf
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

entity_resolver = EntityResolver(parsed_files)
fact_extractor = FactExtractor(entity_resolver)
facts = fact_extractor.extract_all(parsed_files)

conflict_resolver = ConflictResolver()
conflicts = conflict_resolver.resolve_conflicts(facts)

query_engine = QueryEngine(entity_resolver, fact_extractor, conflict_resolver, parsed_files=parsed_files)
benchmark_harness = BenchmarkHarness(query_engine, facts_db={f.id: f for f in facts}, parsed_files=parsed_files, output_dir=EVAL_OUT_DIR)


class QueryRequest(BaseModel):
    query_id: Optional[int] = None
    query_text: Optional[str] = None


class QuestionUploadRequest(BaseModel):
    filename: Optional[str] = None
    content_base64: Optional[str] = None
    raw_text: Optional[str] = None
    questions_list: Optional[List[str]] = None


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
    if req.query_text:
        res = query_engine.answer_query(req.query_text, query_id=req.query_id)
        return res.model_dump()
    if req.query_id:
        if 1 <= req.query_id <= 23:
            res = query_engine.answer_question_by_id(req.query_id)
            return res.model_dump()
        raise HTTPException(status_code=400, detail="query_id must be between 1 and 23")
    return query_engine.answer_question_by_id(1).model_dump()


@app.post("/api/upload-questions")
def upload_questions(req: QuestionUploadRequest):
    extracted_questions = []

    # 1. Direct list
    if req.questions_list:
        extracted_questions = [q.strip() for q in req.questions_list if q.strip()]

    # 2. Base64 encoded file (PDF, JSON, TXT)
    elif req.content_base64:
        try:
            decoded = base64.b64decode(req.content_base64)
            filename = (req.filename or "").lower()

            if filename.endswith(".pdf"):
                reader = pypdf.PdfReader(io.BytesIO(decoded))
                text = "\n".join([p.extract_text() or "" for p in reader.pages])
                lines = [l.strip() for l in text.splitlines() if l.strip()]
                current_q = ""
                for line in lines:
                    m = re.match(r"^(\d+)[\.\)]\s*(.+)", line)
                    if m:
                        if current_q:
                            extracted_questions.append(current_q)
                        current_q = m.group(2)
                    elif current_q and not line.lower().startswith("evaluation questions"):
                        current_q += " " + line
                if current_q:
                    extracted_questions.append(current_q)

            elif filename.endswith(".json"):
                data = json.loads(decoded.decode("utf-8", errors="ignore"))
                if isinstance(data, list):
                    extracted_questions = [str(x) for x in data]
                elif isinstance(data, dict):
                    extracted_questions = data.get("questions", list(data.values()))

            else:
                text = decoded.decode("utf-8", errors="ignore")
                extracted_questions = _parse_text_questions(text)

        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to parse uploaded file: {str(e)}")

    # 3. Raw text paste
    elif req.raw_text:
        extracted_questions = _parse_text_questions(req.raw_text)

    if not extracted_questions:
        raise HTTPException(status_code=400, detail="No questions could be extracted from input.")

    # Evaluate each question through QueryEngine
    evaluated_results = []
    for idx, q_text in enumerate(extracted_questions):
        q_id = idx + 1
        res = query_engine.answer_query(q_text, query_id=q_id)
        evaluated_results.append(res.model_dump())

    return {
        "status": "success",
        "total_questions": len(evaluated_results),
        "results": evaluated_results
    }


def _parse_text_questions(text: str) -> List[str]:
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    questions = []
    current_q = ""
    for line in lines:
        m = re.match(r"^(\d+)[\.\)]\s*(.+)", line)
        if m:
            if current_q:
                questions.append(current_q)
            current_q = m.group(2)
        else:
            if current_q:
                current_q += " " + line
            elif len(line) > 5:
                questions.append(line)
    if current_q:
        questions.append(current_q)
    return questions


@app.get("/api/benchmark")
def run_benchmark():
    metrics = benchmark_harness.run_full_benchmark()
    return metrics


@app.get("/", response_class=HTMLResponse)
def get_index():
    html_path = os.path.join(os.path.dirname(__file__), "static", "index.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Aegis Knowledge Ingestion System</h1>"

