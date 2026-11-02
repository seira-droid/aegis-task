"""
Aegis Knowledge Ingestion & Integrity Test Suite
Verifies:
1. Provenance validity for every extracted fact
2. Trust classifications for all 20 source files
3. Version-scoped pressure setpoints and engineering changes
4. Non-merge decisions for PS-04, PS-04A, and PS-40
5. Epistemic gap & false premise handling (zero fabrication)
6. Schematic vector connectivity derivation
"""

import os
import unittest
from aegis_core.ingestion.coordinator import IngestionCoordinator, DOCUMENT_METADATA_REGISTRY
from aegis_core.pipeline.entity_resolver import EntityResolver
from aegis_core.pipeline.fact_extractor import FactExtractor
from aegis_core.pipeline.conflict_resolver import ConflictResolver
from aegis_core.query.engine import QueryEngine
from aegis_core.schema.models import TrustLevel, EpistemicStatus, FactStatus


class TestKnowledgeIntegrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cls.dataset_root = os.path.join(base_dir, "task-data", "aegis-dataset", "aegis-dataset")
        cls.coordinator = IngestionCoordinator(cls.dataset_root)
        cls.parsed_files = cls.coordinator.ingest_all()
        cls.resolver = EntityResolver(cls.parsed_files)
        cls.extractor = FactExtractor(cls.resolver)
        cls.facts = cls.extractor.extract_all(cls.parsed_files)
        cls.conflict_resolver = ConflictResolver()
        cls.conflicts = cls.conflict_resolver.resolve_conflicts(cls.facts)
        cls.query_engine = QueryEngine(cls.resolver, cls.extractor, cls.conflict_resolver, parsed_files=cls.parsed_files)

    def test_20_source_files_ingested(self):
        """Verify all 20 heterogeneous files are ingested."""
        self.assertEqual(len(self.parsed_files), 20)
        self.assertEqual(len(self.coordinator.source_documents), 20)

    def test_trust_classifications(self):
        """Verify exact trust levels across all 20 source documents."""
        expected_trust = {
            "CFG-EXPORT-01": TrustLevel.ENGINEERING_BULLETIN,
            "ECN-1042": TrustLevel.ENGINEERING_BULLETIN,
            "ECN-1058": TrustLevel.ENGINEERING_BULLETIN,
            "REV-HIST-700": TrustLevel.ENGINEERING_BULLETIN,
            "AEG-OM-700-R4": TrustLevel.OFFICIAL_MANUAL,
            "AEG-MM-700-R3": TrustLevel.OFFICIAL_MANUAL,
            "AEG-AL-700-R5": TrustLevel.OFFICIAL_MANUAL,
            "AEG-CR-700": TrustLevel.OFFICIAL_MANUAL,
            "GLOSS-700": TrustLevel.OFFICIAL_MANUAL,
            "AEG-DWG-H01": TrustLevel.OFFICIAL_MANUAL,
            "AEG-DWG-E02": TrustLevel.OFFICIAL_MANUAL,
            "AEG-DWG-W03": TrustLevel.OFFICIAL_MANUAL,
            "TRN-HPU-01": TrustLevel.OFFICIAL_MANUAL,
            "AEG-OM-700-R1": TrustLevel.OFFICIAL_MANUAL,
            "HMI-SCREEN-01": TrustLevel.OFFICIAL_MANUAL,
            "HMI-SCREEN-02": TrustLevel.OFFICIAL_MANUAL,
            "HMI-SCREEN-03": TrustLevel.OFFICIAL_MANUAL,
            "SITE-NOTES-L4": TrustLevel.FIELD_RECORD_LOW_TRUST,
            "APP-C-CAL": TrustLevel.FIELD_RECORD_LOW_TRUST,
            "SDS-HYD-01": TrustLevel.NOISE_EXTERNAL,
        }
        for doc_id, expected_lvl in expected_trust.items():
            self.assertIn(doc_id, self.coordinator.source_documents)
            actual_lvl = self.coordinator.source_documents[doc_id].trust_level
            self.assertEqual(actual_lvl, expected_lvl, f"Trust mismatch for {doc_id}: got {actual_lvl}, expected {expected_lvl}")

    def test_fact_provenance_validity(self):
        """Verify every extracted fact has valid document_id, location, and authentic quote."""
        for fact in self.facts:
            prov = fact.provenance
            self.assertIsNotNone(prov, f"Fact {fact.id} has no provenance")
            self.assertIn(prov.document_id, self.coordinator.source_documents, f"Unknown document_id {prov.document_id} in {fact.id}")
            has_location = (prov.page is not None) or bool(prov.section) or bool(prov.element_id) or bool(prov.location_detail)
            self.assertTrue(has_location, f"Fact {fact.id} missing page/section location")
            self.assertTrue(bool(prov.verbatim_quote and len(prov.verbatim_quote.strip()) >= 5), f"Fact {fact.id} has empty quote")

    def test_non_merge_decisions(self):
        """Test explicit non-merge decisions: PS-04 != PS-04A, PS-04 != PS-40, PS-04A != PS-40."""
        # PS-04 vs PS-04A
        same_04_04a, just_04_04a = self.resolver.are_same_entity("PS-04", "PS-04A")
        self.assertFalse(same_04_04a)
        self.assertIn("ECN-1042", just_04_04a)
        self.assertIn("not form-fit-function", just_04_04a)

        # PS-04 vs PS-40
        same_04_40, just_04_40 = self.resolver.are_same_entity("PS-04", "PS-40")
        self.assertFalse(same_04_40)
        self.assertIn("Coolant Loop", just_04_40)

        # PS-04A vs PS-40
        same_04a_40, just_04a_40 = self.resolver.are_same_entity("PS-04A", "PS-40")
        self.assertFalse(same_04a_40)

        # Variants resolve correctly to canonical
        self.assertEqual(self.resolver.resolve("P.S.04-A").id, "PS-04A")
        self.assertEqual(self.resolver.resolve("sensor_ps04a").id, "PS-04A")
        self.assertEqual(self.resolver.resolve("PRESSURE SENSOR 04").id, "PS-04")
        self.assertEqual(self.resolver.resolve("P40").id, "PS-40")

    def test_version_scoped_pressure_resolution(self):
        """Test setpoint scoping across firmware revisions and low-trust field subordination."""
        # Query 2 (current operating pressure)
        res_q2 = self.query_engine.answer_question_by_id(2)
        self.assertEqual(res_q2.epistemic_status, EpistemicStatus.VERSION_SCOPED)
        self.assertIn("200 bar", res_q2.direct_answer)
        self.assertIn("3.2", res_q2.direct_answer)
        self.assertIn("180 bar", res_q2.direct_answer)

        # Check conflicts detected
        pressure_conflicts = [c for c in self.conflicts if c.predicate == "normal_operating_pressure"]
        self.assertGreaterEqual(len(pressure_conflicts), 1)
        conf = pressure_conflicts[0]
        self.assertIn("TEMPORAL_SUPERSEDED", conf.resolution_type)
        self.assertIn("175 bar", conf.justification)

        # Query 9 (pressure before 3.2)
        res_q9 = self.query_engine.answer_question_by_id(9)
        self.assertEqual(res_q9.epistemic_status, EpistemicStatus.DEFINITIVE)
        self.assertIn("180 bar", res_q9.direct_answer)
        self.assertIn("ECN-1042", res_q9.direct_answer)

    def test_epistemic_gaps_and_false_premises_separate(self):
        """Verify UNANSWERABLE_GAP and FALSE_PREMISE are strictly distinguished with zero hallucination."""
        # Q19: Max temperature of PS-04A (Gap)
        res_q19 = self.query_engine.answer_question_by_id(19)
        self.assertEqual(res_q19.epistemic_status, EpistemicStatus.UNANSWERABLE_GAP)
        self.assertNotEqual(res_q19.epistemic_status, EpistemicStatus.FALSE_PREMISE)
        self.assertIn("Cannot be determined", res_q19.direct_answer)
        self.assertGreaterEqual(len(res_q19.gaps_identified), 1)

        # Q20: Voltage sensor calibration interval (False Premise)
        res_q20 = self.query_engine.answer_question_by_id(20)
        self.assertEqual(res_q20.epistemic_status, EpistemicStatus.FALSE_PREMISE)
        self.assertNotEqual(res_q20.epistemic_status, EpistemicStatus.UNANSWERABLE_GAP)
        self.assertIn("False Premise", res_q20.direct_answer)
        self.assertIn("NO voltage sensor", res_q20.direct_answer)

        # Q21: Approver of ECN-1058 (Gap)
        res_q21 = self.query_engine.answer_question_by_id(21)
        self.assertEqual(res_q21.epistemic_status, EpistemicStatus.UNANSWERABLE_GAP)
        self.assertIn("Released", res_q21.direct_answer)

        # Q22: MTBF for IV-21 (Gap)
        res_q22 = self.query_engine.answer_question_by_id(22)
        self.assertEqual(res_q22.epistemic_status, EpistemicStatus.UNANSWERABLE_GAP)
        self.assertIn("not specified", res_q22.direct_answer.lower())

        # Q23: 400V supply compatibility (Gap)
        res_q23 = self.query_engine.answer_question_by_id(23)
        self.assertEqual(res_q23.epistemic_status, EpistemicStatus.UNANSWERABLE_GAP)
        self.assertIn("480V", res_q23.direct_answer)
        self.assertIn("not stated", res_q23.direct_answer.lower())

    def test_schematic_vector_connectivity(self):
        """Verify controller connectivity is derived from vector coordinates."""
        hyd_file = "diagrams/system_diagram_hydraulic.pdf"
        self.assertIn(hyd_file, self.parsed_files)
        vec_data = self.parsed_files[hyd_file]["content"].get("vector_analysis", {})
        purple_conns = vec_data.get("direct_purple_controller_connections", [])
        grey_conns = vec_data.get("direct_grey_connections", [])

        self.assertIn("PS-04A", purple_conns)
        self.assertIn("IV-21", purple_conns)
        self.assertNotIn("HPU", purple_conns)
        self.assertIn("HPU", grey_conns)

    def test_evidence_verifier_quotation_fidelity(self):
        """Verify that every cited verbatim quote exists in raw parsed source texts."""
        from aegis_core.query.verifier import EvidenceVerifier
        verifier = EvidenceVerifier(self.parsed_files)
        verified_count = 0
        for fact in self.facts:
            quote = fact.provenance.verbatim_quote
            doc_id = fact.provenance.document_id
            if quote:
                is_v, score, msg = verifier.verify_quotation(doc_id, quote)
                self.assertTrue(is_v or score >= 0.70, f"Quote verification failed for fact {fact.id} in {doc_id}: {msg}")
                verified_count += 1
        self.assertGreater(verified_count, 20)

    def test_unfamiliar_alias_resolution(self):
        """Verify that identifier variants across formats resolve to canonical entities."""
        # Wiring diagram alias
        ent_xdcr = self.resolver.resolve("PRESSURE XDCR")
        self.assertIsNotNone(ent_xdcr)
        self.assertEqual(ent_xdcr.id, "PS-04A")

        # HMI OCR tag
        ent_tag = self.resolver.resolve("P.S.04-A")
        self.assertIsNotNone(ent_tag)
        self.assertEqual(ent_tag.id, "PS-04A")

        # Config export keys
        ent_cfg = self.resolver.resolve("sensor_ps04a")
        self.assertIsNotNone(ent_cfg)
        self.assertEqual(ent_cfg.id, "PS-04A")

        ent_iv = self.resolver.resolve("valve_iv21")
        self.assertIsNotNone(ent_iv)
        self.assertEqual(ent_iv.id, "IV-21")

        # Training slide informal aliases
        ent_hpu = self.resolver.resolve("hydraulic pack")
        self.assertIsNotNone(ent_hpu)
        self.assertEqual(ent_hpu.id, "HPU")

    def test_subordination_of_low_trust_field_observations(self):
        """Verify that 175 bar field gauge reading is subordinated to 200 bar controlled manual."""
        res = self.query_engine.answer_query("Does the 175 bar gauge reading on Line 4 override the manual?")
        self.assertEqual(res.epistemic_status, EpistemicStatus.VERSION_SCOPED)
        self.assertIn("not override", res.direct_answer.lower())
        self.assertIn("200 bar", res.direct_answer)
        self.assertIn("175 bar", res.direct_answer)
        # Check that conflict is recorded
        self.assertTrue(len(res.conflicts_identified) > 0)
        self.assertEqual(res.conflicts_identified[0].predicate, "normal_operating_pressure")


if __name__ == "__main__":
    unittest.main()

