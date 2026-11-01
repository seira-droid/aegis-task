"""
Aegis Knowledge Ingestion CLI Runner
Command-line interface to ingest, extract, evaluate, query, and serve the Aegis platform.
"""

import os
import sys
import argparse
import json

# Ensure aegis-task root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8')

from aegis_core.ingestion.coordinator import IngestionCoordinator
from aegis_core.pipeline.entity_resolver import EntityResolver
from aegis_core.pipeline.fact_extractor import FactExtractor
from aegis_core.pipeline.conflict_resolver import ConflictResolver
from aegis_core.query.engine import QueryEngine
from aegis_core.eval.benchmark import BenchmarkHarness
from aegis_core.schema.models import KnowledgeStoreExport


def main():
    parser = argparse.ArgumentParser(description="Aegis Series-7 Knowledge Ingestion Runner")
    parser.add_argument("--eval", action="store_true", help="Run full evaluation benchmark on all 23 questions")
    parser.add_argument("--export", action="store_true", help="Export Intermediate Knowledge Representation (IKR) to JSON")
    parser.add_argument("--serve", action="store_true", help="Launch FastAPI web UI server")
    parser.add_argument("--port", type=int, default=8000, help="Port for web server (default: 8000)")
    parser.add_argument("--query", type=int, help="Query an evaluation question by ID (1-23)")
    args = parser.parse_args()

    base_dir = os.path.dirname(os.path.abspath(__file__))
    dataset_root = os.path.join(base_dir, "task-data", "aegis-dataset", "aegis-dataset")
    eval_dir = os.path.join(base_dir, "eval_results")
    data_dir = os.path.join(base_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(eval_dir, exist_ok=True)

    print("=" * 70)
    print(" Aegis Series-7 Knowledge Ingestion System")
    print("=" * 70)

    # 1. Ingestion
    print(f"[*] Ingesting 20 heterogeneous files from: {dataset_root}")
    coordinator = IngestionCoordinator(dataset_root)
    parsed_files = coordinator.ingest_all()
    print(f"    -> Successfully ingested {len(parsed_files)} files across 8 formats.")

    # 2. Entity Resolution
    print("[*] Initializing canonical entity resolution & alias indexing...")
    resolver = EntityResolver()
    print(f"    -> {len(resolver.entities)} canonical entities mapped with {len(resolver.alias_to_canonical)} aliases.")

    # 3. Fact Extraction
    print("[*] Extracting structured facts with provenance tracking...")
    extractor = FactExtractor(resolver)
    facts = extractor.extract_all(parsed_files)
    print(f"    -> Extracted {len(facts)} structured facts with document/page citations.")

    # 4. Conflict Resolution
    print("[*] Resolving temporal and trust-hierarchy contradictions...")
    conflict_resolver = ConflictResolver()
    conflicts = conflict_resolver.resolve_conflicts(facts)
    print(f"    -> Identified and resolved {len(conflicts)} version/trust conflicts.")

    # 5. Query Engine
    query_engine = QueryEngine(resolver, extractor, conflict_resolver)

    # Export Intermediate Knowledge Representation
    ikr_export = KnowledgeStoreExport(
        extraction_timestamp="2026-11-01T19:30:00Z",
        entities=resolver.entities,
        facts=facts,
        conflicts=conflicts,
        entity_alias_index=resolver.alias_to_canonical
    )
    store_file = os.path.join(data_dir, "knowledge_store.json")
    with open(store_file, "w", encoding="utf-8") as f:
        json.dump(ikr_export.model_dump(), f, indent=2)
    print(f"[+] Serialized Intermediate Knowledge Representation to: {store_file}")

    # Specific query action
    if args.query:
        print(f"\n--- Running Query Q{args.query} ---")
        res = query_engine.answer_question_by_id(args.query)
        print(f"Question: {res.query}")
        print(f"Status:   [{res.epistemic_status.value}]")
        print(f"Answer:   {res.direct_answer}\n")
        print("Evidence Citations:")
        for ev in res.evidence:
            loc = f"p.{ev.page}" if ev.page else (ev.section or ev.element_id or "doc")
            print(f"  * [{ev.document_id}] {ev.document_title} ({loc})")
            if ev.verbatim_quote:
                print(f"    Quote: \"{ev.verbatim_quote}\"")
        if res.gaps_identified:
            print("Gaps Identified:")
            for g in res.gaps_identified:
                print(f"  * {g.target_topic}: {g.explanation}")
        return

    # Benchmark evaluation action
    if args.eval or not (args.serve or args.export):
        print("\n" + "=" * 70)
        print(" Running Full Evaluation Benchmark (23 Questions)")
        print("=" * 70)
        harness = BenchmarkHarness(query_engine, eval_dir)
        metrics = harness.run_benchmark()

        print(f"Total Questions Evaluated:    {metrics['total_questions']}")
        print(f"Overall Answer Accuracy:      {metrics['overall_accuracy_pct']}%")
        print(f"Epistemic Calibration Score:  {metrics['epistemic_calibration_pct']}%")
        print(f"Provenance Citation Recall:   {metrics['provenance_recall_pct']}%")
        print(f"Gap Detection Recall:         {metrics['gap_detection_recall_pct']}%")
        print(f"Hallucination Rate:           {metrics['hallucination_rate_pct']}%")
        print(f"\nDetailed evaluation report saved to: {os.path.join(eval_dir, 'evaluation_summary.md')}")

    # Serve action
    if args.serve:
        import uvicorn
        print(f"\n[+] Starting FastAPI server at http://127.0.0.1:{args.port}")
        uvicorn.run("aegis_core.ui.app:app", host="127.0.0.1", port=args.port, reload=False)


if __name__ == "__main__":
    main()

