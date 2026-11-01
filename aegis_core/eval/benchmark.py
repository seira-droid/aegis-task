"""
Evaluation Benchmark Runner
Executes the full 23-question test suite from evaluation_questions.pdf
and produces both quantitative metric reports and human-readable summaries.
"""

import os
import json
from typing import Dict, Any, List
from aegis_core.schema.models import EpistemicStatus
from aegis_core.query.engine import QueryEngine
from aegis_core.eval.metrics import EvaluationMetrics


GROUND_TRUTH_DATA: Dict[int, Dict[str, Any]] = {
    1: {
        "expected_epistemic_status": EpistemicStatus.DEFINITIVE,
        "required_keywords": ["fluid level", "IV-21", "emergency stop", "access panel"],
        "expected_sources": ["AEG-OM-700-R4", "CFG-EXPORT-01"],
        "is_gap": False
    },
    2: {
        "expected_epistemic_status": EpistemicStatus.VERSION_SCOPED,
        "required_keywords": ["200 bar", "3.2", "180 bar"],
        "expected_sources": ["AEG-OM-700-R4", "ECN-1042"],
        "is_gap": False
    },
    3: {
        "expected_epistemic_status": EpistemicStatus.DEFINITIVE,
        "required_keywords": ["hydraulic pressure low", "150 bar", "IV-21", "fluid"],
        "expected_sources": ["AEG-AL-700-R5"],
        "is_gap": False
    },
    4: {
        "expected_epistemic_status": EpistemicStatus.DEFINITIVE,
        "required_keywords": ["not the same", "ECN-1042", "signal drift"],
        "expected_sources": ["ECN-1042"],
        "is_gap": False
    },
    5: {
        "expected_epistemic_status": EpistemicStatus.DEFINITIVE,
        "required_keywords": ["ECN-1042", "Engineering Change Notice"],
        "expected_sources": ["ECN-1042"],
        "is_gap": False
    },
    6: {
        "expected_epistemic_status": EpistemicStatus.DEFINITIVE,
        "required_keywords": ["PS-04A", "HPU", "IV-21", "purple"],
        "expected_sources": ["AEG-DWG-H01"],
        "is_gap": False
    },
    7: {
        "expected_epistemic_status": EpistemicStatus.DEFINITIVE,
        "required_keywords": ["shutdown procedure 4.7", "10 seconds", "IV-21"],
        "expected_sources": ["AEG-MM-700-R3"],
        "is_gap": False
    },
    8: {
        "expected_epistemic_status": EpistemicStatus.DEFINITIVE,
        "required_keywords": ["50 bar", "uncommanded", "IV-21"],
        "expected_sources": ["AEG-OM-700-R4", "AEG-MM-700-R3"],
        "is_gap": False
    },
    9: {
        "expected_epistemic_status": EpistemicStatus.DEFINITIVE,
        "required_keywords": ["180 bar", "ECN-1042"],
        "expected_sources": ["ECN-1042", "AEG-OM-700-R4"],
        "is_gap": False
    },
    10: {
        "expected_epistemic_status": EpistemicStatus.DEFINITIVE,
        "required_keywords": ["A17", "hydraulic pressure low"],
        "expected_sources": ["AEG-AL-700-R5"],
        "is_gap": False
    },
    11: {
        "expected_epistemic_status": EpistemicStatus.DEFINITIVE,
        "required_keywords": ["Hydraulic Module"],
        "expected_sources": ["AEG-CR-700"],
        "is_gap": False
    },
    12: {
        "expected_epistemic_status": EpistemicStatus.DEFINITIVE,
        "required_keywords": ["Auxiliary Reservoir", "not covered in the standard Operator Manual"],
        "expected_sources": ["TRN-HPU-01"],
        "is_gap": False
    },
    13: {
        "expected_epistemic_status": EpistemicStatus.DEFINITIVE,
        "required_keywords": ["P.S.04-A", "PS-04A"],
        "expected_sources": ["HMI-SCREEN-03"],
        "is_gap": False
    },
    14: {
        "expected_epistemic_status": EpistemicStatus.DEFINITIVE,
        "required_keywords": ["2025-09-30", "PS-04A", "200 bar"],
        "expected_sources": ["REV-HIST-700"],
        "is_gap": False
    },
    15: {
        "expected_epistemic_status": EpistemicStatus.DEFINITIVE,
        "required_keywords": ["normal operating pressure"],
        "expected_sources": ["CFG-EXPORT-01", "AEG-OM-700-R4"],
        "is_gap": False
    },
    16: {
        "expected_epistemic_status": EpistemicStatus.VERSION_SCOPED,
        "required_keywords": ["only", "3.2", "180 bar"],
        "expected_sources": ["AEG-OM-700-R4", "ECN-1042"],
        "is_gap": False
    },
    17: {
        "expected_epistemic_status": EpistemicStatus.DEFINITIVE,
        "required_keywords": ["not the same", "Coolant Loop", "Skid B"],
        "expected_sources": ["AEG-CR-700"],
        "is_gap": False
    },
    18: {
        "expected_epistemic_status": EpistemicStatus.DEFINITIVE,
        "required_keywords": ["180 bar"],
        "expected_sources": ["AEG-OM-700-R1", "AEG-OM-700-R4"],
        "is_gap": False
    },
    19: {
        "expected_epistemic_status": EpistemicStatus.UNANSWERABLE_GAP,
        "required_keywords": ["cannot be determined", "epistemic gap"],
        "expected_sources": [],
        "is_gap": True
    },
    20: {
        "expected_epistemic_status": EpistemicStatus.FALSE_PREMISE,
        "required_keywords": ["false premise", "no voltage sensor", "cannot be determined"],
        "expected_sources": [],
        "is_gap": True,
        "is_false_premise": True
    },
    21: {
        "expected_epistemic_status": EpistemicStatus.UNANSWERABLE_GAP,
        "required_keywords": ["cannot be determined", "released", "author"],
        "expected_sources": [],
        "is_gap": True
    },
    22: {
        "expected_epistemic_status": EpistemicStatus.UNANSWERABLE_GAP,
        "required_keywords": ["cannot be determined", "mtbf", "not specified"],
        "expected_sources": [],
        "is_gap": True
    },
    23: {
        "expected_epistemic_status": EpistemicStatus.CONFLICT_RESOLVED,
        "required_keywords": ["not directly compatible", "480V"],
        "expected_sources": ["AEG-CR-700"],
        "is_gap": False
    }
}


class BenchmarkHarness:
    def __init__(self, query_engine: QueryEngine, output_dir: str):
        self.engine = query_engine
        self.output_dir = output_dir

    def run_benchmark(self) -> Dict[str, Any]:
        os.makedirs(self.output_dir, exist_ok=True)
        results = []

        for q_id in range(1, 24):
            res = self.engine.answer_question_by_id(q_id)
            results.append(res)

        metrics = EvaluationMetrics.calculate_metrics(results, GROUND_TRUTH_DATA)

        # 1. Write evaluation_report.json
        report_path = os.path.join(self.output_dir, "evaluation_report.json")
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump({
                "metrics": metrics,
                "results": [r.model_dump() for r in results]
            }, f, indent=2)

        # 2. Write evaluation_summary.md
        summary_path = os.path.join(self.output_dir, "evaluation_summary.md")
        self._write_markdown_summary(summary_path, metrics, results)

        return metrics

    def _write_markdown_summary(self, path: str, metrics: Dict[str, Any], results: List[Any]):
        lines = [
            "# Aegis Knowledge Ingestion Challenge — Evaluation Results\n",
            f"**Total Questions Evaluated:** {metrics['total_questions']}",
            f"**Overall Answer Accuracy:** {metrics['overall_accuracy_pct']}%",
            f"**Provenance Recall:** {metrics['provenance_recall_pct']}%",
            f"**Epistemic Calibration Score:** {metrics['epistemic_calibration_pct']}%",
            f"**Gap Detection Recall:** {metrics['gap_detection_recall_pct']}%",
            f"**Hallucination Rate:** {metrics['hallucination_rate_pct']}%\n",
            "## Summary Table\n",
            "| # | Question | Epistemic Status | Result | Sources Cited |",
            "|---|---|---|---|---|"
        ]

        for r, detail in zip(results, metrics["detailed_evaluations"]):
            status_badge = f"`{r.epistemic_status.value}`"
            res_badge = "PASS" if detail["is_correct"] else "FAIL"
            sources = ", ".join(detail["cited_sources"]) if detail["cited_sources"] else "*None (Epistemic Gap)*"
            # Truncate question for table
            q_short = r.query if len(r.query) < 65 else r.query[:62] + "..."
            lines.append(f"| {r.query_id} | {q_short} | {status_badge} | {res_badge} | {sources} |")

        lines.append("\n## Detailed Question Breakdown\n")
        for r, detail in zip(results, metrics["detailed_evaluations"]):
            lines.append(f"### Question {r.query_id}: {r.query}")
            lines.append(f"- **Epistemic Classification:** `{r.epistemic_status.value}`")
            lines.append(f"- **Direct Answer:**\n> {r.direct_answer.replace(chr(10), chr(10) + '> ')}")
            if r.claims:
                lines.append("- **Verified Claims:**")
                for c in r.claims:
                    lines.append(f"  * {c.statement} (Supported by: `{', '.join(c.supporting_fact_ids)}`)")
            if r.evidence:
                lines.append("- **Provenance Citations:**")
                for ev in r.evidence:
                    loc = f"p.{ev.page}" if ev.page else (ev.section or ev.element_id or "root")
                    lines.append(f"  * **[{ev.document_id}]** *{ev.document_title}* ({loc}) — Quote: \"{ev.verbatim_quote}\"")
            if r.gaps_identified:
                lines.append("- **Epistemic Gaps / Missing Data:**")
                for g in r.gaps_identified:
                    lines.append(f"  * ⚠️ *{g.target_topic}* -> {g.explanation}")
            lines.append("")

        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
