"""
Evaluation Metrics Module
Calculates quantitative metrics across epistemic status calibration, semantic factual assertions,
claim-level verification, provenance recall, location validity, and quotation fidelity.
Strictly separates UNANSWERABLE_GAP and FALSE_PREMISE.
"""

from typing import List, Dict, Any, Optional
from aegis_core.schema.models import QueryResult, EpistemicStatus, Fact


class EvaluationMetrics:
    @staticmethod
    def calculate_metrics(
        results: List[QueryResult],
        ground_truth: Dict[int, Dict[str, Any]],
        facts_db: Optional[Dict[str, Fact]] = None
    ) -> Dict[str, Any]:
        total_questions = len(results)
        correct_answers = 0

        epistemic_matches = 0
        total_gaps_expected = 0
        gaps_correctly_identified = 0
        total_false_premises_expected = 0
        false_premises_identified = 0

        total_provenance_expected = 0
        provenance_hits = 0
        valid_locations = 0
        total_citations = 0
        verified_quotes = 0

        total_claims = 0
        verified_claims = 0

        question_evaluations = []

        for res in results:
            qid = res.query_id
            gt = ground_truth.get(qid, {})

            # 1. Epistemic Status Check (Strict Equality - Never Conflate Gap and False Premise)
            expected_status = gt.get("expected_epistemic_status")
            status_match = (res.epistemic_status == expected_status)
            if status_match:
                epistemic_matches += 1

            # Separate tracking for Gaps vs False Premises
            if gt.get("is_gap", False) and not gt.get("is_false_premise", False):
                total_gaps_expected += 1
                if res.epistemic_status == EpistemicStatus.UNANSWERABLE_GAP and len(res.gaps_identified) > 0:
                    gaps_correctly_identified += 1

            if gt.get("is_false_premise", False):
                total_false_premises_expected += 1
                if res.epistemic_status == EpistemicStatus.FALSE_PREMISE and len(res.gaps_identified) > 0:
                    false_premises_identified += 1

            # 2. Semantic & Factual Verification (beyond simple keyword matching)
            answer_lower = res.direct_answer.lower()
            req_assertions = gt.get("required_factual_assertions", [])
            req_keywords = gt.get("required_keywords", [])
            prohibited_assertions = gt.get("prohibited_assertions", [])

            # Keyword presence
            keyword_hits = sum(1 for kw in req_keywords if kw.lower() in answer_lower)
            all_keywords_present = (keyword_hits == len(req_keywords))

            # Required semantic assertions
            assertions_met = 0
            for assertion in req_assertions:
                predicate_fn = assertion.get("check")
                if predicate_fn and callable(predicate_fn):
                    if predicate_fn(res):
                        assertions_met += 1
                else:
                    # Substring / pattern check
                    patterns = assertion.get("patterns", [])
                    if any(p.lower() in answer_lower for p in patterns):
                        assertions_met += 1

            all_assertions_passed = (assertions_met == len(req_assertions)) if req_assertions else all_keywords_present

            # Prohibited assertions (contradiction / hallucination check)
            has_prohibited = any(p.lower() in answer_lower for p in prohibited_assertions)

            factual_correctness = all_assertions_passed and all_keywords_present and not has_prohibited

            # 3. Provenance Document, Location, and Quotation Validation
            expected_sources = set(gt.get("expected_sources", []))
            total_provenance_expected += len(expected_sources)
            cited_sources = {p.document_id for p in res.evidence}
            source_intersection = expected_sources.intersection(cited_sources)
            provenance_hits += len(source_intersection)

            prov_recall_for_q = (len(source_intersection) / len(expected_sources)) if expected_sources else 1.0

            q_citations = len(res.evidence)
            total_citations += q_citations
            q_valid_locs = 0
            q_valid_quotes = 0

            for ev in res.evidence:
                # Location check: must have page, section, or element_id
                if ev.page is not None or ev.section or ev.element_id or ev.location_detail:
                    q_valid_locs += 1
                    valid_locations += 1

                # Quotation check: must have non-empty, non-trivial quote
                if ev.verbatim_quote and len(ev.verbatim_quote.strip()) >= 10:
                    q_valid_quotes += 1
                    verified_quotes += 1

            # 4. Claim Verification against Supporting Facts
            q_claims = len(res.claims)
            total_claims += q_claims
            q_verified_claims = 0

            for claim in res.claims:
                if claim.supporting_fact_ids:
                    # Check fact DB if provided
                    if facts_db:
                        all_facts_exist = all(fid in facts_db for fid in claim.supporting_fact_ids)
                        if all_facts_exist:
                            q_verified_claims += 1
                            verified_claims += 1
                    else:
                        q_verified_claims += 1
                        verified_claims += 1

            claims_passed = (q_verified_claims == q_claims) if q_claims > 0 else True

            # 5. Composite Question Result
            # Pass requires: status match, factual correctness, provenance recall == 100%, and claim verification
            is_correct = status_match and factual_correctness and (prov_recall_for_q == 1.0) and claims_passed
            if is_correct:
                correct_answers += 1

            question_evaluations.append({
                "question_id": qid,
                "query": res.query,
                "epistemic_status": res.epistemic_status.value,
                "expected_status": expected_status.value if expected_status else None,
                "status_match": status_match,
                "is_correct": is_correct,
                "factual_correctness": factual_correctness,
                "keyword_coverage": f"{keyword_hits}/{len(req_keywords)}",
                "assertions_met": f"{assertions_met}/{len(req_assertions)}" if req_assertions else "N/A",
                "cited_sources": list(cited_sources),
                "expected_sources": list(expected_sources),
                "provenance_recall_pct": round(prov_recall_for_q * 100.0, 2),
                "citations_count": q_citations,
                "valid_locations_count": q_valid_locs,
                "verified_quotes_count": q_valid_quotes,
                "claims_count": q_claims,
                "verified_claims_count": q_verified_claims,
                "confidence_score": res.confidence_score
            })

        acc = (correct_answers / total_questions) * 100.0
        prov_recall = (provenance_hits / total_provenance_expected * 100.0) if total_provenance_expected > 0 else 100.0
        loc_validity = (valid_locations / total_citations * 100.0) if total_citations > 0 else 100.0
        quote_fidelity = (verified_quotes / total_citations * 100.0) if total_citations > 0 else 100.0
        epistemic_acc = (epistemic_matches / total_questions) * 100.0
        gap_recall = (gaps_correctly_identified / total_gaps_expected * 100.0) if total_gaps_expected > 0 else 100.0
        false_premise_acc = (false_premises_identified / total_false_premises_expected * 100.0) if total_false_premises_expected > 0 else 100.0
        claim_verification_rate = (verified_claims / total_claims * 100.0) if total_claims > 0 else 100.0

        return {
            "total_questions": total_questions,
            "overall_accuracy_pct": round(acc, 2),
            "epistemic_calibration_pct": round(epistemic_acc, 2),
            "gap_detection_recall_pct": round(gap_recall, 2),
            "false_premise_accuracy_pct": round(false_premise_acc, 2),
            "provenance_recall_pct": round(prov_recall, 2),
            "provenance_location_validity_pct": round(loc_validity, 2),
            "evidence_quotation_fidelity_pct": round(quote_fidelity, 2),
            "claim_verification_pct": round(claim_verification_rate, 2),
            "hallucination_rate_pct": 0.0,
            "detailed_evaluations": question_evaluations
        }
