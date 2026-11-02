"""
Evaluation Benchmark Runner
Executes comprehensive evaluation against both the canonical 23 questions from
evaluation_questions.pdf and an independent suite of 10 held-out rephrased questions.
Validates epistemic status, semantic assertions, claim verification, location citations,
and evidence quote fidelity.
"""

import os
import json
from typing import Dict, Any, List
from aegis_core.schema.models import EpistemicStatus
from aegis_core.query.engine import QueryEngine
from aegis_core.eval.metrics import EvaluationMetrics


# Ground Truth independently derived from authoritative source documents
GROUND_TRUTH_DATA: Dict[int, Dict[str, Any]] = {
    1: {
        "expected_epistemic_status": EpistemicStatus.DEFINITIVE,
        "required_keywords": ["fluid", "iv-21", "emergency stop", "access panel"],
        "expected_sources": ["AEG-OM-700-R4", "CFG-EXPORT-01"],
        "required_factual_assertions": [
            {"patterns": ["fluid level is within", "fluid", "sight glass"]},
            {"patterns": ["isolation valve iv-21 is open", "iv-21 is open", "valve_iv21"]},
            {"patterns": ["emergency stop circuit is reset", "estop", "e-stop"]},
            {"patterns": ["maintenance access panel is installed", "panel is closed", "maintenance access panel"]}
        ],
        "prohibited_assertions": ["panel removed is permitted", "iv-21 is closed"],
        "is_gap": False
    },
    2: {
        "expected_epistemic_status": EpistemicStatus.VERSION_SCOPED,
        "required_keywords": ["200 bar", "3.2", "180 bar"],
        "expected_sources": ["AEG-OM-700-R4", "ECN-1042"],
        "required_factual_assertions": [
            {"patterns": ["200 bar"]},
            {"patterns": ["software revision 3.2", "firmware 3.2", "rev 3.2"]},
            {"patterns": ["180 bar", "prior to 3.2", "legacy"]}
        ],
        "prohibited_assertions": ["200 bar applies to all units unconditionally", "180 bar on current firmware"],
        "is_gap": False
    },
    3: {
        "expected_epistemic_status": EpistemicStatus.DEFINITIVE,
        "required_keywords": ["hydraulic pressure low", "150 bar", "iv-21", "fluid"],
        "expected_sources": ["AEG-AL-700-R5", "AEG-MM-700-R3"],
        "required_factual_assertions": [
            {"patterns": ["hydraulic pressure low", "pressure below 150 bar"]},
            {"patterns": ["iv-21 closed", "partially closed"]},
            {"patterns": ["fluid level is low", "low hydraulic fluid"]},
            {"patterns": ["sensor", "drift", "out of calibration", "signal invalid"]}
        ],
        "prohibited_assertions": ["alarm a17 is normal", "pressure high"],
        "is_gap": False
    },
    4: {
        "expected_epistemic_status": EpistemicStatus.DEFINITIVE,
        "required_keywords": ["not the same", "ecn-1042", "signal drift"],
        "expected_sources": ["ECN-1042"],
        "required_factual_assertions": [
            {"patterns": ["not the same component", "not the same", "not a form-fit-function"]},
            {"patterns": ["ecn-1042"]},
            {"patterns": ["signal drift", "drift", "18-month"]}
        ],
        "prohibited_assertions": ["ps-04 is identical to ps-04a", "direct drop-in replacement"],
        "is_gap": False
    },
    5: {
        "expected_epistemic_status": EpistemicStatus.DEFINITIVE,
        "required_keywords": ["ecn-1042", "engineering change notice"],
        "expected_sources": ["ECN-1042"],
        "required_factual_assertions": [
            {"patterns": ["ecn-1042", "engineering change notice 1042"]}
        ],
        "prohibited_assertions": ["ecn-1058 introduced the sensor change"],
        "is_gap": False
    },
    6: {
        # Verified from vector stream: only PS-04A and IV-21 connect via purple control lines; HPU line is grey fluid line
        "expected_epistemic_status": EpistemicStatus.DEFINITIVE,
        "required_keywords": ["ps-04a", "iv-21", "purple", "grey"],
        "expected_sources": ["AEG-DWG-H01"],
        "required_factual_assertions": [
            {"patterns": ["ps-04a"]},
            {"patterns": ["iv-21"]},
            {"patterns": ["purple", "control/signal"]},
            {"patterns": ["grey", "fluid path", "hydraulic fluid"]}
        ],
        "prohibited_assertions": ["hpu connects via purple control line", "plc-03 does not connect to iv-21"],
        "is_gap": False
    },
    7: {
        "expected_epistemic_status": EpistemicStatus.DEFINITIVE,
        "required_keywords": ["shutdown procedure 4.7", "10 seconds", "iv-21"],
        "expected_sources": ["AEG-MM-700-R3", "CFG-EXPORT-01"],
        "required_factual_assertions": [
            {"patterns": ["shutdown procedure 4.7"]},
            {"patterns": ["10 seconds"]},
            {"patterns": ["close iv-21", "iv-21"]}
        ],
        "prohibited_assertions": ["silence the alarm and continue", "ignore if running"],
        "is_gap": False
    },
    8: {
        "expected_epistemic_status": EpistemicStatus.DEFINITIVE,
        "required_keywords": ["50 bar", "uncommanded", "iv-21"],
        "expected_sources": ["AEG-OM-700-R4", "AEG-MM-700-R3"],
        "required_factual_assertions": [
            {"patterns": ["50 bar", "above 50 bar"]},
            {"patterns": ["uncommanded", "valve transition", "actuation"]},
            {"patterns": ["iv-21", "isolation valve"]}
        ],
        "prohibited_assertions": ["safe to reset at 200 bar", "reset at any pressure"],
        "is_gap": False
    },
    9: {
        "expected_epistemic_status": EpistemicStatus.DEFINITIVE,
        "required_keywords": ["180 bar", "ecn-1042"],
        "expected_sources": ["ECN-1042", "AEG-OM-700-R4"],
        "required_factual_assertions": [
            {"patterns": ["180 bar"]},
            {"patterns": ["ecn-1042", "engineering change notice 1042"]},
            {"patterns": ["200 bar", "3.2"]}
        ],
        "prohibited_assertions": ["220 bar before 3.2", "150 bar was normal"],
        "is_gap": False
    },
    10: {
        "expected_epistemic_status": EpistemicStatus.DEFINITIVE,
        "required_keywords": ["a17", "hydraulic pressure low"],
        "expected_sources": ["AEG-AL-700-R5"],
        "required_factual_assertions": [
            {"patterns": ["a17", "alarm a17"]},
            {"patterns": ["hydraulic pressure low"]}
        ],
        "prohibited_assertions": ["alarm a18", "alarm a19"],
        "is_gap": False
    },
    11: {
        "expected_epistemic_status": EpistemicStatus.DEFINITIVE,
        "required_keywords": ["hydraulic module", "components"],
        "expected_sources": ["AEG-CR-700"],
        "required_factual_assertions": [
            {"patterns": ["hydraulic module"]}
        ],
        "prohibited_assertions": ["skid b", "control cabinet 1"],
        "is_gap": False
    },
    12: {
        "expected_epistemic_status": EpistemicStatus.DEFINITIVE,
        "required_keywords": ["auxiliary reservoir", "not covered in the standard operator manual"],
        "expected_sources": ["TRN-HPU-01"],
        "required_factual_assertions": [
            {"patterns": ["auxiliary reservoir"]},
            {"patterns": ["not covered in the standard operator manual", "line 4/5"]},
            {"patterns": ["no new alarms", "no novel alarms", "does not introduce any new alarm"]}
        ],
        "prohibited_assertions": ["introduces alarm a20", "no novel components"],
        "is_gap": False
    },
    13: {
        "expected_epistemic_status": EpistemicStatus.DEFINITIVE,
        "required_keywords": ["p.s.04-a", "ps-04a"],
        "expected_sources": ["HMI-SCREEN-03"],
        "required_factual_assertions": [
            {"patterns": ["p.s.04-a"]},
            {"patterns": ["ps-04a", "matches"]}
        ],
        "prohibited_assertions": ["does not match any component", "matches ps-40"],
        "is_gap": False
    },
    14: {
        "expected_epistemic_status": EpistemicStatus.DEFINITIVE,
        "required_keywords": ["2025-09-30", "ps-04a", "200 bar"],
        "expected_sources": ["REV-HIST-700"],
        "required_factual_assertions": [
            {"patterns": ["2025-09-30", "september 30, 2025"]},
            {"patterns": ["ps-04", "ps-04a", "replaced"]},
            {"patterns": ["180 bar", "200 bar"]}
        ],
        "prohibited_assertions": ["effective 2024", "no pressure change"],
        "is_gap": False
    },
    15: {
        "expected_epistemic_status": EpistemicStatus.DEFINITIVE,
        "required_keywords": ["normal operating pressure"],
        "expected_sources": ["CFG-EXPORT-01", "AEG-OM-700-R4"],
        "required_factual_assertions": [
            {"patterns": ["normal operating pressure", "normal discharge pressure"]},
            {"patterns": ["200 bar"]}
        ],
        "prohibited_assertions": ["alarm threshold", "maximum burst pressure"],
        "is_gap": False
    },
    16: {
        "expected_epistemic_status": EpistemicStatus.VERSION_SCOPED,
        "required_keywords": ["only", "3.2", "180 bar"],
        "expected_sources": ["AEG-OM-700-R4", "ECN-1042"],
        "required_factual_assertions": [
            {"patterns": ["only some", "only to some units", "units running software revision 3.2"]},
            {"patterns": ["180 bar", "prior to 3.2", "legacy"]}
        ],
        "prohibited_assertions": ["applies to all units unconditionally"],
        "is_gap": False
    },
    17: {
        "expected_epistemic_status": EpistemicStatus.DEFINITIVE,
        "required_keywords": ["not the same", "coolant loop", "skid b"],
        "expected_sources": ["AEG-CR-700"],
        "required_factual_assertions": [
            {"patterns": ["not the same", "not the same as ps-40"]},
            {"patterns": ["coolant loop", "skid b"]},
            {"patterns": ["hpu discharge", "hydraulic circuit"]}
        ],
        "prohibited_assertions": ["ps-04 is the same as ps-40"],
        "is_gap": False
    },
    18: {
        "expected_epistemic_status": EpistemicStatus.DEFINITIVE,
        "required_keywords": ["180 bar"],
        "expected_sources": ["AEG-OM-700-R1", "AEG-OM-700-R4"],
        "required_factual_assertions": [
            {"patterns": ["180 bar"]}
        ],
        "prohibited_assertions": ["200 bar before revision 3.2"],
        "is_gap": False
    },
    19: {
        "expected_epistemic_status": EpistemicStatus.UNANSWERABLE_GAP,
        "required_keywords": ["cannot be determined", "epistemic gap"],
        "expected_sources": [],
        "required_factual_assertions": [
            {"patterns": ["cannot be determined", "omitted", "epistemic gap", "not specified"]}
        ],
        "prohibited_assertions": ["85°c", "100°c", "operating temperature is 70"],
        "is_gap": True,
        "is_false_premise": False
    },
    20: {
        "expected_epistemic_status": EpistemicStatus.FALSE_PREMISE,
        "required_keywords": ["false premise", "no voltage sensor", "cannot be determined"],
        "expected_sources": [],
        "required_factual_assertions": [
            {"patterns": ["false premise", "no voltage sensor", "contains no voltage sensor"]}
        ],
        "prohibited_assertions": ["calibrate every 12 months", "calibration interval is 1 year"],
        "is_gap": False,
        "is_false_premise": True
    },
    21: {
        "expected_epistemic_status": EpistemicStatus.UNANSWERABLE_GAP,
        "required_keywords": ["cannot be determined", "released", "author"],
        "expected_sources": [],
        "required_factual_assertions": [
            {"patterns": ["cannot be determined", "omits", "does not list an author", "not stated"]}
        ],
        "prohibited_assertions": ["approved by john doe", "approved by j. torres"],
        "is_gap": True,
        "is_false_premise": False
    },
    22: {
        "expected_epistemic_status": EpistemicStatus.UNANSWERABLE_GAP,
        "required_keywords": ["cannot be determined", "mtbf", "not specified"],
        "expected_sources": [],
        "required_factual_assertions": [
            {"patterns": ["cannot be determined", "not specified", "omitted", "no mtbf"]}
        ],
        "prohibited_assertions": ["50,000 hours", "10,000 hours", "mtbf is 2 years"],
        "is_gap": True,
        "is_false_premise": False
    },
    23: {
        "expected_epistemic_status": EpistemicStatus.UNANSWERABLE_GAP,
        "required_keywords": ["not stated", "480v", "cannot be confirmed"],
        "expected_sources": ["AEG-CR-700"],
        "required_factual_assertions": [
            {"patterns": ["cannot be determined", "not stated", "cannot be confirmed"]},
            {"patterns": ["480v"]}
        ],
        "prohibited_assertions": ["fully compatible with 400v", "yes, it is compatible"],
        "is_gap": True,
        "is_false_premise": False
    }
}

# 10 Held-out Rephrasings for Generalization Testing
HELD_OUT_TEST_SUITE = [
    {
        "id": 101,
        "query": "What conditions must an operator check prior to powering on the hydraulic unit?",
        "expected_epistemic_status": EpistemicStatus.DEFINITIVE,
        "required_keywords": ["fluid", "iv-21", "emergency stop", "access panel"]
    },
    {
        "id": 102,
        "query": "Under software v3.2, what is the specified operating pressure of the HPU?",
        "expected_epistemic_status": EpistemicStatus.VERSION_SCOPED,
        "required_keywords": ["200 bar", "3.2"]
    },
    {
        "id": 104,
        "query": "Can PS-04 be swapped with PS-04A as a direct drop-in replacement?",
        "expected_epistemic_status": EpistemicStatus.DEFINITIVE,
        "required_keywords": ["not", "same", "ecn-1042"]
    },
    {
        "id": 106,
        "query": "Looking at drawing AEG-DWG-H01, what field devices have purple signal cables to PLC-03?",
        "expected_epistemic_status": EpistemicStatus.DEFINITIVE,
        "required_keywords": ["ps-04a", "iv-21"]
    },
    {
        "id": 107,
        "query": "What procedure should be initiated if the low pressure alarm does not clear within 10 seconds?",
        "expected_epistemic_status": EpistemicStatus.DEFINITIVE,
        "required_keywords": ["shutdown procedure 4.7", "iv-21"]
    },
    {
        "id": 108,
        "query": "Why is resetting PLC-03 dangerous when pressure exceeds 50 bar?",
        "expected_epistemic_status": EpistemicStatus.DEFINITIVE,
        "required_keywords": ["50 bar", "uncommanded", "iv-21"]
    },
    {
        "id": 117,
        "query": "Is there any connection between the coolant loop sensor PS-40 and the HPU pressure sensor?",
        "expected_epistemic_status": EpistemicStatus.DEFINITIVE,
        "required_keywords": ["not", "coolant", "skid b"]
    },
    {
        "id": 119,
        "query": "Does the manufacturer documentation state the maximum operating temperature for PS-04A?",
        "expected_epistemic_status": EpistemicStatus.UNANSWERABLE_GAP,
        "required_keywords": ["cannot be determined", "gap"]
    },
    {
        "id": 120,
        "query": "Where can I find the calibration interval for the voltmeter or voltage sensor in the electrical schematic?",
        "expected_epistemic_status": EpistemicStatus.FALSE_PREMISE,
        "required_keywords": ["false premise", "no voltage sensor"]
    },
    {
        "id": 123,
        "query": "Can the Aegis Series-7 run directly on a 400V 3-phase European industrial mains?",
        "expected_epistemic_status": EpistemicStatus.UNANSWERABLE_GAP,
        "required_keywords": ["not stated", "480v"]
    }
]


class BenchmarkHarness:
    def __init__(self, query_engine: QueryEngine, output_dir: str):
        self.engine = query_engine
        self.output_dir = output_dir

    def run_benchmark(self) -> Dict[str, Any]:
        os.makedirs(self.output_dir, exist_ok=True)

        # 1. Primary 23-Question Evaluation
        primary_results = []
        for q_id in range(1, 24):
            res = self.engine.answer_question_by_id(q_id)
            primary_results.append(res)

        primary_metrics = EvaluationMetrics.calculate_metrics(
            primary_results,
            GROUND_TRUTH_DATA,
            facts_db=self.engine._fact_index
        )

        # 2. Held-out Generalization Evaluation
        held_out_results = []
        held_out_matches = 0
        for item in HELD_OUT_TEST_SUITE:
            res = self.engine.answer_query(item["query"], query_id=item["id"])
            held_out_results.append(res)

            ans_lower = res.direct_answer.lower()
            kw_match = all(kw in ans_lower for kw in item["required_keywords"])
            status_match = res.epistemic_status == item["expected_epistemic_status"]
            if kw_match and status_match:
                held_out_matches += 1

        held_out_accuracy = round((held_out_matches / len(HELD_OUT_TEST_SUITE)) * 100.0, 2)

        combined_report = {
            "primary_benchmark": primary_metrics,
            "held_out_generalization": {
                "total_held_out": len(HELD_OUT_TEST_SUITE),
                "held_out_passed": held_out_matches,
                "generalization_accuracy_pct": held_out_accuracy,
                "test_cases": [
                    {
                        "id": t["id"],
                        "query": t["query"],
                        "epistemic_status": r.epistemic_status.value,
                        "expected_status": t["expected_epistemic_status"].value,
                        "passed": all(kw in r.direct_answer.lower() for kw in t["required_keywords"]) and r.epistemic_status == t["expected_epistemic_status"],
                        "answer_preview": r.direct_answer[:120] + "..."
                    }
                    for t, r in zip(HELD_OUT_TEST_SUITE, held_out_results)
                ]
            },
            "results": [r.model_dump() for r in primary_results]
        }

        # Write reports
        report_path = os.path.join(self.output_dir, "evaluation_report.json")
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(combined_report, f, indent=2)

        summary_path = os.path.join(self.output_dir, "evaluation_summary.md")
        self._write_markdown_summary(summary_path, primary_metrics, primary_results, held_out_accuracy, len(HELD_OUT_TEST_SUITE))

        return primary_metrics

    def _write_markdown_summary(
        self,
        path: str,
        metrics: Dict[str, Any],
        results: List[Any],
        held_out_acc: float,
        held_out_count: int
    ):
        lines = [
            "# Aegis Knowledge Ingestion Challenge — Evaluation Results\n",
            f"**Primary Questions Evaluated:** {metrics['total_questions']}",
            f"**Primary Answer Accuracy:** {metrics['overall_accuracy_pct']}%",
            f"**Epistemic Calibration Score:** {metrics['epistemic_calibration_pct']}%",
            f"**Gap Detection Recall:** {metrics['gap_detection_recall_pct']}%",
            f"**False Premise Accuracy:** {metrics['false_premise_accuracy_pct']}%",
            f"**Provenance Citation Recall:** {metrics['provenance_recall_pct']}%",
            f"**Location Validity:** {metrics['provenance_location_validity_pct']}%",
            f"**Evidence Quotation Fidelity:** {metrics['evidence_quotation_fidelity_pct']}%",
            f"**Claim Verification Rate:** {metrics['claim_verification_pct']}%",
            f"**Hallucination Rate:** {metrics['hallucination_rate_pct']}%\n",
            f"**Held-out Generalization Suite:** {held_out_count} rephrased queries",
            f"**Held-out Generalization Accuracy:** {held_out_acc}%\n",
            "## Primary Evaluation Scorecard (23 Questions)\n",
            "| # | Question | Epistemic Status | Result | Sources Cited |",
            "|---|---|---|:---:|---|"
        ]

        for r, detail in zip(results, metrics["detailed_evaluations"]):
            status_badge = f"`{r.epistemic_status.value}`"
            res_badge = "PASS" if detail["is_correct"] else "FAIL"
            sources = ", ".join(detail["cited_sources"]) if detail["cited_sources"] else "*None (Epistemic Gap)*"
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
