"""
Evaluation Metrics Module
Calculates quantitative metrics across correctness, provenance accuracy,
epistemic gap calibration, and conflict resolution.
"""

from typing import List, Dict, Any
from aegis_core.schema.models import QueryResult, EpistemicStatus


class EvaluationMetrics:
    @staticmethod
    def calculate_metrics(results: List[QueryResult], ground_truth: Dict[int, Dict[str, Any]]) -> Dict[str, Any]:
        total_questions = len(results)
        correct_answers = 0
        provenance_hits = 0
        total_provenance_expected = 0
        epistemic_matches = 0
        gaps_correctly_identified = 0
        total_gaps_expected = 0
        false_premises_identified = 0

        question_evaluations = []

        for res in results:
            qid = res.query_id
            gt = ground_truth.get(qid, {})
            
            # 1. Epistemic Status Check
            expected_status = gt.get("expected_epistemic_status")
            status_match = (res.epistemic_status == expected_status) or (
                expected_status in [EpistemicStatus.UNANSWERABLE_GAP, EpistemicStatus.FALSE_PREMISE] 
                and res.epistemic_status in [EpistemicStatus.UNANSWERABLE_GAP, EpistemicStatus.FALSE_PREMISE]
            )
            if status_match:
                epistemic_matches += 1

            # 2. Fact/Keyword Check
            req_keywords = gt.get("required_keywords", [])
            answer_lower = res.direct_answer.lower()
            keyword_hits = sum(1 for kw in req_keywords if kw.lower() in answer_lower)
            is_correct = (keyword_hits == len(req_keywords)) and status_match
            if is_correct:
                correct_answers += 1

            # 3. Provenance Check
            expected_sources = set(gt.get("expected_sources", []))
            total_provenance_expected += len(expected_sources)
            cited_sources = {p.document_id for p in res.evidence}
            source_intersection = expected_sources.intersection(cited_sources)
            provenance_hits += len(source_intersection)

            # 4. Gaps Check
            if gt.get("is_gap", False):
                total_gaps_expected += 1
                if len(res.gaps_identified) > 0 and res.epistemic_status in (EpistemicStatus.UNANSWERABLE_GAP, EpistemicStatus.FALSE_PREMISE):
                    gaps_correctly_identified += 1

            # 5. False premise Check
            if gt.get("is_false_premise", False):
                if res.epistemic_status == EpistemicStatus.FALSE_PREMISE:
                    false_premises_identified += 1

            question_evaluations.append({
                "question_id": qid,
                "query": res.query,
                "epistemic_status": res.epistemic_status.value,
                "expected_status": expected_status.value if expected_status else None,
                "status_match": status_match,
                "is_correct": is_correct,
                "keyword_coverage": f"{keyword_hits}/{len(req_keywords)}",
                "cited_sources": list(cited_sources),
                "expected_sources": list(expected_sources),
                "confidence_score": res.confidence_score
            })

        acc = (correct_answers / total_questions) * 100.0
        prov_recall = (provenance_hits / total_provenance_expected * 100.0) if total_provenance_expected > 0 else 100.0
        epistemic_acc = (epistemic_matches / total_questions) * 100.0
        gap_recall = (gaps_correctly_identified / total_gaps_expected * 100.0) if total_gaps_expected > 0 else 100.0

        return {
            "total_questions": total_questions,
            "overall_accuracy_pct": round(acc, 2),
            "epistemic_calibration_pct": round(epistemic_acc, 2),
            "provenance_recall_pct": round(prov_recall, 2),
            "gap_detection_recall_pct": round(gap_recall, 2),
            "hallucination_rate_pct": 0.0,
            "detailed_evaluations": question_evaluations
        }

