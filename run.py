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
    parser.add_argument("--questions-file", type=str, help="Path to external question file (.pdf, .json, .txt) to evaluate")
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
    ing_summary = coordinator.get_ingestion_summary()
    print(f"    -> Successfully ingested {ing_summary['total_files_processed']} of {ing_summary['total_files_discovered']} files.")
    print(f"    -> Format distribution: {ing_summary['file_type_distribution']}")
    print(f"    -> Trust tier distribution: {ing_summary['trust_tier_distribution']}")
    if ing_summary['failed_files']:
        print(f"    -> Parser Failures: {ing_summary['failed_files']}")

    # 2. Entity Resolution
    print("[*] Initializing canonical entity resolution & alias indexing...")
    resolver = EntityResolver(parsed_files)
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
    query_engine = QueryEngine(resolver, extractor, conflict_resolver, parsed_files=parsed_files)

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

    # Custom question file action
    if args.questions_file:
        q_path = os.path.abspath(args.questions_file)
        if not os.path.exists(q_path):
            print(f"Error: Questions file not found at: {q_path}")
            return

        print(f"\n[*] Parsing and evaluating questions from: {q_path}")
        questions = []
        if q_path.lower().endswith(".pdf"):
            import pypdf, re
            reader = pypdf.PdfReader(q_path)
            full_text = "\n".join([p.extract_text() or "" for p in reader.pages])
            current_q = ""
            for line in [l.strip() for l in full_text.splitlines() if l.strip()]:
                m = re.match(r"^(\d+)[\.\)]\s*(.+)", line)
                if m:
                    if current_q: questions.append(current_q)
                    current_q = m.group(2)
                elif current_q and not line.lower().startswith("evaluation questions"):
                    current_q += " " + line
            if current_q: questions.append(current_q)
        elif q_path.lower().endswith(".json"):
            with open(q_path, "r", encoding="utf-8") as jf:
                data = json.load(jf)
                questions = data if isinstance(data, list) else data.get("questions", list(data.values()))
        else:
            with open(q_path, "r", encoding="utf-8") as tf:
                questions = [l.strip() for l in tf.read().splitlines() if len(l.strip()) > 5]

        print(f"    -> Extracted {len(questions)} questions.")
        evaluated = []
        for idx, q_text in enumerate(questions):
            res = query_engine.answer_query(q_text, query_id=idx + 1)
            evaluated.append(res)
            print(f"[{res.epistemic_status.value:18}] Q{idx + 1}: {q_text[:60]}...")

        out_summary = os.path.join(eval_dir, "custom_questions_summary.md")
        with open(out_summary, "w", encoding="utf-8") as f:
            f.write(f"# Evaluated Question Set: {os.path.basename(q_path)}\n\n")
            for r in evaluated:
                f.write(f"### Q{r.query_id}: {r.query}\n")
                f.write(f"- **Epistemic Status:** `{r.epistemic_status.value}`\n")
                f.write(f"- **Answer:** {r.direct_answer}\n\n")
        print(f"\n[+] Results written to: {out_summary}")
        return

    # Benchmark evaluation action
    if args.eval or not (args.serve or args.export):
        print("\n" + "=" * 70)
        print(" Running Full Evaluation Benchmark (23 Questions + 10 Held-out Queries)")
        print("=" * 70)
        harness = BenchmarkHarness(query_engine, facts_db={f.id: f for f in facts}, parsed_files=parsed_files, output_dir=eval_dir)
        metrics = harness.run_full_benchmark()

        print(f"Total Questions Evaluated:    {metrics['total_questions']}")
        print(f"Overall Answer Accuracy:      {metrics['overall_accuracy_pct']}%")
        print(f"Epistemic Calibration Score:  {metrics['epistemic_calibration_pct']}%")
        print(f"Gap Detection (P / R / F1):   {metrics['gap_detection']['precision_pct']}% / {metrics['gap_detection']['recall_pct']}% / {metrics['gap_detection']['f1_score']}")
        print(f"False Premise (P / R / F1):   {metrics['false_premise_detection']['precision_pct']}% / {metrics['false_premise_detection']['recall_pct']}% / {metrics['false_premise_detection']['f1_score']}")
        print(f"Provenance Citation Recall:   {metrics['provenance_recall_pct']}%")
        print(f"Provenance Location Validity: {metrics['provenance_location_validity_pct']}%")
        print(f"Evidence Quotation Fidelity:  {metrics['evidence_quotation_fidelity_pct']}%")
        print(f"Claim-Level Evidence Support: {metrics['claim_level_evidence_support_pct']}%")
        print(f"Hallucination Rate:           {metrics['hallucination_rate_pct']}%")
        print(f"Confidence Calibration:       {metrics['confidence_calibration_pct']}% (Brier: {metrics['brier_score']})")

        rep_path = os.path.join(eval_dir, "evaluation_report.json")
        if os.path.exists(rep_path):
            with open(rep_path, "r", encoding="utf-8") as rf:
                rep = json.load(rf)
                held = rep.get("held_out_generalization", {})
                print(f"Held-out Generalization:      {held.get('held_out_passed', 0)}/{held.get('total_held_out', 10)} ({held.get('generalization_accuracy_pct', 100.0)}%)")

        print(f"\nDetailed evaluation report saved to: {os.path.join(eval_dir, 'evaluation_summary.md')}")

    # Serve action
    if args.serve:
        import uvicorn
        print(f"\n[+] Starting FastAPI server at http://127.0.0.1:{args.port}")
        uvicorn.run("aegis_core.ui.app:app", host="127.0.0.1", port=args.port, reload=False)


if __name__ == "__main__":
    main()

