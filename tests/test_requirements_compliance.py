"""
Comprehensive Requirements Compliance Test Suite
Aegis Knowledge Ingestion Challenge

Validates:
1. All eight document ingestion formats (PDF, scanned PDF/OCR, HTML, XLSX, DOCX, PPTX, JSON, PNG)
2. OCR dynamic extraction, noise tolerance, and uncertainty tracking
3. Schematic vector topology: multi-segment lines, non-connecting line crossings, component association
4. Strict entity resolution: non-merge rules (PS-04 != PS-04A != PS-40) and alias index
5. Strict quotation verification: positive exact, negative non-existent, partial match, wrong document rejection
6. Temporal scoping and conflict resolution
7. Complete 23 evaluation questions benchmark verification
"""

import os
import sys
import pytest
import unittest

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aegis_core.ingestion.coordinator import IngestionCoordinator
from aegis_core.ingestion.vision_parser import VisionParserModule
from aegis_core.ingestion.scan_ocr import ScanOCRParserModule
from aegis_core.pipeline.entity_resolver import EntityResolver
from aegis_core.pipeline.fact_extractor import FactExtractor
from aegis_core.pipeline.conflict_resolver import ConflictResolver
from aegis_core.query.engine import QueryEngine
from aegis_core.query.verifier import EvidenceVerifier
from aegis_core.eval.benchmark import GROUND_TRUTH_DATA
from aegis_core.schema.models import EpistemicStatus, TrustLevel, FactStatus


class TestRequirementsCompliance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cls.dataset_root = os.path.join(base_dir, "task-data", "aegis-dataset", "aegis-dataset")
        cls.coordinator = IngestionCoordinator(cls.dataset_root)
        cls.parsed_files = cls.coordinator.ingest_all()
        cls.resolver = EntityResolver(parsed_files=cls.parsed_files)
        cls.extractor = FactExtractor(cls.resolver)
        cls.facts = cls.extractor.extract_all(cls.parsed_files)
        cls.facts_db = {f.id: f for f in cls.facts}
        cls.conflict_resolver = ConflictResolver()
        cls.conflicts = cls.conflict_resolver.resolve_conflicts(cls.facts)
        cls.query_engine = QueryEngine(
            resolver=cls.resolver,
            fact_extractor=cls.extractor,
            conflict_resolver=cls.conflict_resolver,
            parsed_files=cls.parsed_files
        )
        cls.verifier = EvidenceVerifier(cls.parsed_files)

    # -------------------------------------------------------------------------
    # 1. All Eight Ingestion Formats
    # -------------------------------------------------------------------------
    def test_all_eight_ingestion_formats(self):
        """Verifies successful parsing across all 8 required formats."""
        format_found = {
            "PDF": False,
            "PDF (Scanned OCR)": False,
            "HTML": False,
            "XLSX": False,
            "DOCX": False,
            "PPTX": False,
            "JSON": False,
            "PNG": False
        }
        for rel_path, data in self.parsed_files.items():
            ft = data.get("file_type")
            if ft in format_found:
                format_found[ft] = True
            elif ft == "PNG (OCR Processed)":
                format_found["PNG"] = True

        for fmt, found in format_found.items():
            self.assertTrue(found, f"Format {fmt} was not parsed successfully.")

    # -------------------------------------------------------------------------
    # 2. OCR Dynamic Value Extraction & Uncertainty Tracking
    # -------------------------------------------------------------------------
    def test_ocr_dynamic_extraction_and_uncertainty(self):
        """Verifies dynamic OCR extraction, noisy token handling, and uncertainty preservation."""
        scan_file = "scans/scanned_appendix_calibration.pdf"
        self.assertIn(scan_file, self.parsed_files)
        scan_data = self.parsed_files[scan_file]["content"]

        # Dynamic extraction of calibration points
        cal_points = scan_data.get("calibration_points", [])
        self.assertGreaterEqual(len(cal_points), 3, "Failed to extract dynamic calibration rows")

        # Verify parsed setpoint values
        setpoints = [pt["reference_bar"] for pt in cal_points]
        self.assertIn(0.0, setpoints)
        self.assertIn(100.0, setpoints)
        self.assertIn(200.0, setpoints)

        # Verify uncertainty notes and label noise handling
        label_noise = scan_data.get("label_noise_detected", [])
        self.assertIsInstance(label_noise, list)
        self.assertTrue(len(label_noise) > 0 or "label_noise_detected" in scan_data)

        # Verify raw OCR tokens are preserved
        self.assertIn("ocr_raw_tokens", scan_data)
        self.assertGreater(len(scan_data["ocr_raw_tokens"]), 10)

    # -------------------------------------------------------------------------
    # 3. Schematic Topology, Line Crossings & Multi-Segment Paths
    # -------------------------------------------------------------------------
    def test_schematic_line_crossings_without_connection(self):
        """Verifies geometric line crossing detection without creating false connections."""
        hyd_file = "diagrams/system_diagram_hydraulic.pdf"
        self.assertIn(hyd_file, self.parsed_files)
        vec_data = self.parsed_files[hyd_file]["content"].get("vector_analysis", {})

        crossings = vec_data.get("line_crossings", [])
        self.assertGreaterEqual(len(crossings), 1, "Expected at least 1 detected line crossing")

        c0 = crossings[0]
        self.assertEqual(c0["type"], "crossing_without_connection")
        self.assertFalse(c0["is_valid_connection"])
        self.assertEqual(c0["intersection_point"], (396.0, 367.2))
        self.assertIn("IV-21", str(c0["line_1"]["connects"]))
        self.assertIn("MAIN_RESERVOIR", str(c0["line_2"]["connects"]))

    def test_schematic_multi_segment_paths_and_components(self):
        """Verifies multi-segment path extraction and component boundaries."""
        hyd_file = "diagrams/system_diagram_hydraulic.pdf"
        vec_data = self.parsed_files[hyd_file]["content"].get("vector_analysis", {})

        paths = vec_data.get("multi_segment_paths", [])
        self.assertGreaterEqual(len(paths), 5)

        comps = {c["id"]: c for c in vec_data.get("detected_components", [])}
        self.assertIn("PLC-03", comps)
        self.assertIn("HPU", comps)
        self.assertIn("PS-04A", comps)
        self.assertIn("IV-21", comps)
        self.assertIn("MAIN_RESERVOIR", comps)
        self.assertIn("AUXILIARY_RESERVOIR", comps)
        self.assertIn("PRESS_CIRCUIT", comps)

    # -------------------------------------------------------------------------
    # 4. Strict Entity Resolution & Non-Merge Decisions
    # -------------------------------------------------------------------------
    def test_strict_entity_non_merge(self):
        """Verifies non-merge rules preventing unsafe consolidation of similar identifiers."""
        # PS-04 != PS-04A
        same_04_04a, just_04_04a = self.resolver.are_same_entity("PS-04", "PS-04A")
        self.assertFalse(same_04_04a)
        self.assertIn("ECN-1042", just_04_04a)

        # PS-04 != PS-40
        same_04_40, just_04_40 = self.resolver.are_same_entity("PS-04", "PS-40")
        self.assertFalse(same_04_40)
        self.assertIn("Coolant Loop", just_04_40)

        # PS-04A != PS-40
        same_04a_40, just_04a_40 = self.resolver.are_same_entity("PS-04A", "PS-40")
        self.assertFalse(same_04a_40)

    def test_alias_resolution_across_formats(self):
        """Verifies alias resolution from spreadsheets, XML, OCR tags, and diagrams."""
        test_cases = [
            ("P.S.04-A", "PS-04A"),
            ("PRESSURE XDCR", "PS-04A"),
            ("sensor_ps04a", "PS-04A"),
            ("IV-21 SOLENOID", "IV-21"),
            ("valve_iv21", "IV-21"),
            ("hydraulic pack", "HPU"),
            ("P40", "PS-40"),
            ("Disconnect Q1", "Q1"),
            ("CONTROL XFMR T1", "T1")
        ]
        for alias, expected_canonical in test_cases:
            ent = self.resolver.resolve(alias)
            self.assertIsNotNone(ent, f"Failed to resolve alias '{alias}'")
            self.assertEqual(ent.id, expected_canonical, f"Alias '{alias}' resolved to {ent.id}, expected {expected_canonical}")

    # -------------------------------------------------------------------------
    # 5. Strict Quotation Verification
    # -------------------------------------------------------------------------
    def test_strict_quotation_verification_positive(self):
        """Verifies exact verbatim quotation match in authentic source document."""
        real_quote = "Verify discharge pressure, as reported by PS-04A, reaches 200 bar."
        is_v, ratio, reason = self.verifier.verify_quotation("AEG-OM-700-R4", real_quote)
        self.assertTrue(is_v)
        self.assertEqual(ratio, 1.0)
        self.assertIn("VERIFIED", reason)

    def test_strict_quotation_verification_negative(self):
        """Verifies that fabricated or non-existent quotes are rejected as UNVERIFIED."""
        fake_quote = "All hydraulic units shall be replaced every fortnight without exception."
        is_v, ratio, reason = self.verifier.verify_quotation("AEG-OM-700-R4", fake_quote)
        self.assertFalse(is_v)
        self.assertIn("UNVERIFIED", reason)

    def test_strict_quotation_verification_wrong_document(self):
        """Verifies that a valid quote tested against the wrong document is rejected."""
        om_quote = "Verify discharge pressure, as reported by PS-04A, reaches 200 bar."
        is_v, ratio, reason = self.verifier.verify_quotation("AEG-DWG-H01", om_quote)
        self.assertFalse(is_v)
        self.assertIn("UNVERIFIED", reason)

    def test_strict_quotation_verification_short_fragment(self):
        """Verifies that short trivial fragments (<2 words or <6 chars) are rejected."""
        is_v, ratio, reason = self.verifier.verify_quotation("AEG-OM-700-R4", "the")
        self.assertFalse(is_v)
        self.assertIn("too short", reason)

    # -------------------------------------------------------------------------
    # 6. Temporal Scoping & Conflict Resolution
    # -------------------------------------------------------------------------
    def test_temporal_conflict_resolution(self):
        """Verifies version-scoped resolution of 180 bar vs 200 bar and 175 bar field subordination."""
        res = self.query_engine.answer_question_by_id(2)
        self.assertEqual(res.epistemic_status, EpistemicStatus.VERSION_SCOPED)
        self.assertIn("200 bar", res.direct_answer)
        self.assertIn("3.2", res.direct_answer)
        self.assertIn("180 bar", res.direct_answer)

        # Field note subordination query
        res_field = self.query_engine.answer_query("Does the 175 bar gauge reading on Line 4 override the manual?")
        self.assertEqual(res_field.epistemic_status, EpistemicStatus.VERSION_SCOPED)
        self.assertIn("not override", res_field.direct_answer.lower())
        self.assertTrue(len(res_field.conflicts_identified) > 0)

    # -------------------------------------------------------------------------
    # 7. Complete 23 Evaluation Questions Benchmark Verification
    # -------------------------------------------------------------------------
    def test_all_23_evaluation_questions(self):
        """Validates each canonical evaluation question against ground truth constraints."""
        for qid in range(1, 24):
            with self.subTest(qid=qid):
                gt = GROUND_TRUTH_DATA[qid]
                res = self.query_engine.answer_question_by_id(qid)

                # 1. Epistemic Status
                self.assertEqual(
                    res.epistemic_status,
                    gt["expected_epistemic_status"],
                    f"Q{qid}: Epistemic status mismatch. Got {res.epistemic_status}, expected {gt['expected_epistemic_status']}"
                )

                # 2. Required Keywords
                answer_lower = res.direct_answer.lower()
                for kw in gt["required_keywords"]:
                    self.assertIn(
                        kw.lower(),
                        answer_lower,
                        f"Q{qid}: Missing required keyword '{kw}' in answer: {res.direct_answer}"
                    )

                # 3. Prohibited Assertions
                for p in gt["prohibited_assertions"]:
                    self.assertNotIn(
                        p.lower(),
                        answer_lower,
                        f"Q{qid}: Prohibited assertion '{p}' found in answer: {res.direct_answer}"
                    )

                # 4. Expected Sources
                expected_sources = set(gt["expected_sources"])
                cited_sources = {p.document_id for p in res.evidence}
                if expected_sources:
                    intersection = expected_sources.intersection(cited_sources)
                    self.assertEqual(
                        intersection,
                        expected_sources,
                        f"Q{qid}: Missing expected source citation. Got {cited_sources}, expected {expected_sources}"
                    )


if __name__ == "__main__":
    unittest.main()
