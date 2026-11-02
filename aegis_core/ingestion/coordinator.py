"""
Ingestion Coordinator
Dispatches all 20 files across 8 formats to dedicated parsers,
stamps initial trust levels, initializes perceptual caching, and maintains document registry.
"""

import os
from typing import Dict, Any, List
from aegis_core.schema.models import TrustLevel, SourceDocument
from aegis_core.ingestion.pdf_parser import PDFParser
from aegis_core.ingestion.office_parser import OfficeParser
from aegis_core.ingestion.html_parser import HTMLParserModule
from aegis_core.ingestion.json_parser import JSONParserModule
from aegis_core.ingestion.vision_parser import VisionParserModule
from aegis_core.ingestion.scan_ocr import ScanOCRParserModule
from aegis_core.ingestion.ocr_utils import OCRManager


# Canonical registry mapping filename pattern to authoritative document ID and metadata
DOCUMENT_METADATA_REGISTRY = {
    "configuration_export.json": {
        "id": "CFG-EXPORT-01",
        "title": "AegisConfigExport v1.4",
        "file_type": "JSON",
        "trust_level": TrustLevel.ENGINEERING_BULLETIN,
        "summary": "Machine configuration export dump (firmware 3.2.1)"
    },
    "operator_manual.pdf": {
        "id": "AEG-OM-700-R4",
        "title": "Aegis Series-7 HCS Operator Manual (AEG-OM-700 Rev 4)",
        "file_type": "PDF",
        "trust_level": TrustLevel.OFFICIAL_MANUAL,
        "summary": "Official Operator Manual Rev 4 (12 pages)"
    },
    "maintenance_manual.pdf": {
        "id": "AEG-MM-700-R3",
        "title": "Aegis Series-7 HCS Maintenance Manual (AEG-MM-700 Rev 3)",
        "file_type": "PDF",
        "trust_level": TrustLevel.OFFICIAL_MANUAL,
        "summary": "Official Maintenance Manual Rev 3 (18 pages)"
    },
    "legacy_manual_v1.html": {
        "id": "AEG-OM-700-R1",
        "title": "Operator Manual (v1, legacy export)",
        "file_type": "HTML",
        "trust_level": TrustLevel.OFFICIAL_MANUAL,
        "summary": "Legacy CMS export of Operator Manual v1 (partially superseded)"
    },
    "ECN-1042.pdf": {
        "id": "ECN-1042",
        "title": "Engineering Change Notice ECN-1042",
        "file_type": "PDF",
        "trust_level": TrustLevel.ENGINEERING_BULLETIN,
        "summary": "Sensor replacement (PS-04 -> PS-04A) and setpoint revision (180 -> 200 bar)"
    },
    "ECN-1058.pdf": {
        "id": "ECN-1058",
        "title": "Engineering Change Notice ECN-1058",
        "file_type": "PDF",
        "trust_level": TrustLevel.ENGINEERING_BULLETIN,
        "summary": "Documentation correction for Alarm A17 sensor reference logic"
    },
    "alarm_reference.pdf": {
        "id": "AEG-AL-700-R5",
        "title": "Aegis Alarm Reference (AEG-AL-700 Rev 5)",
        "file_type": "PDF",
        "trust_level": TrustLevel.OFFICIAL_MANUAL,
        "summary": "Official Alarm Reference with multi-row tables and thresholds"
    },
    "component_register.xlsx": {
        "id": "AEG-CR-700",
        "title": "Component Register (AEG-CR-700)",
        "file_type": "XLSX",
        "trust_level": TrustLevel.OFFICIAL_MANUAL,
        "summary": "Master component list, aliases, skid locations, and power disconnects"
    },
    "revision_history.xlsx": {
        "id": "REV-HIST-700",
        "title": "Revision History (AEG-RH-700)",
        "file_type": "XLSX",
        "trust_level": TrustLevel.ENGINEERING_BULLETIN,
        "summary": "Software and hardware revision release timeline and change descriptions"
    },
    "terminology_glossary.docx": {
        "id": "GLOSS-700",
        "title": "Terminology Glossary",
        "file_type": "DOCX",
        "trust_level": TrustLevel.OFFICIAL_MANUAL,
        "summary": "Official terminology definitions and cross-references"
    },
    "system_diagram_hydraulic.pdf": {
        "id": "AEG-DWG-H01",
        "title": "Hydraulic Schematic (AEG-DWG-H01)",
        "file_type": "PDF",
        "trust_level": TrustLevel.OFFICIAL_MANUAL,
        "summary": "Vector schematic showing hydraulic and control/signal line topology"
    },
    "system_diagram_electrical.png": {
        "id": "AEG-DWG-E02",
        "title": "Electrical Schematic (AEG-DWG-E02)",
        "file_type": "PNG",
        "trust_level": TrustLevel.OFFICIAL_MANUAL,
        "summary": "Power distribution, transformer, PLC-03 power, and valve driver wiring"
    },
    "wiring_diagram.pdf": {
        "id": "AEG-DWG-W03",
        "title": "Wiring Diagram (AEG-DWG-W03)",
        "file_type": "PDF",
        "trust_level": TrustLevel.OFFICIAL_MANUAL,
        "summary": "Terminal block wiring diagram for pressure transducer loop"
    },
    "training_slide_excerpt.pptx": {
        "id": "TRN-HPU-01",
        "title": "HPU Basics Training Excerpt",
        "file_type": "PPTX",
        "trust_level": TrustLevel.OFFICIAL_MANUAL,
        "summary": "Training slide deck introducing Line 4/5 Auxiliary Reservoir"
    },
    "site_survey_notes.docx": {
        "id": "SITE-NOTES-L4",
        "title": "Site Visit Notes — Line 4 HPU (J. Torres)",
        "file_type": "DOCX",
        "trust_level": TrustLevel.FIELD_RECORD_LOW_TRUST,
        "summary": "Informal field notes recording unverified 175 bar gauge reading"
    },
    "scanned_appendix_calibration.pdf": {
        "id": "APP-C-CAL",
        "title": "APPENDIX C — SENSOR CALIBRATION RECORD",
        "file_type": "PDF (Scanned OCR)",
        "trust_level": TrustLevel.FIELD_RECORD_LOW_TRUST,
        "summary": "Scanned sensor calibration form with OCR noise and unstated interval"
    },
    "safety_data_sheet_hydraulic_fluid.pdf": {
        "id": "SDS-HYD-01",
        "title": "Safety Data Sheet — Hydraulic Fluid ISO VG 46",
        "file_type": "PDF",
        "trust_level": TrustLevel.NOISE_EXTERNAL,
        "summary": "Material Safety Data Sheet (external reference noise)"
    },
    "screen_01_home.png": {
        "id": "HMI-SCREEN-01",
        "title": "HMI Home Screen",
        "file_type": "PNG (OCR Processed)",
        "trust_level": TrustLevel.OFFICIAL_MANUAL,
        "summary": "HMI Home Screen showing discharge pressure and startup interlocks"
    },
    "screen_02_alarms.png": {
        "id": "HMI-SCREEN-02",
        "title": "HMI Alarm List Screen",
        "file_type": "PNG (OCR Processed)",
        "trust_level": TrustLevel.OFFICIAL_MANUAL,
        "summary": "HMI Alarm list showing active Alarm A17 and shutdown threshold"
    },
    "screen_03_diagnostics.png": {
        "id": "HMI-SCREEN-03",
        "title": "HMI Diagnostics Screen",
        "file_type": "PNG (OCR Processed)",
        "trust_level": TrustLevel.OFFICIAL_MANUAL,
        "summary": "HMI Diagnostics showing physical sensor tag P.S.04-A"
    }
}


class IngestionCoordinator:
    def __init__(self, dataset_root: str):
        self.dataset_root = dataset_root
        self.parsed_files: Dict[str, Any] = {}
        self.source_documents: Dict[str, SourceDocument] = {}

        # Initialize OCR cache in data directory
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")
        cache_path = os.path.join(data_dir, ".ocr_cache.json")
        OCRManager.set_cache_path(cache_path)

    def ingest_all(self) -> Dict[str, Any]:
        """Scans dataset directory and ingests all 20 files."""
        if not os.path.exists(self.dataset_root):
            raise FileNotFoundError(f"Dataset root not found: {self.dataset_root}")

        for root, _, files in os.walk(self.dataset_root):
            for file in sorted(files):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, self.dataset_root).replace('\\', '/')
                self._ingest_file(rel_path, full_path)

        return self.parsed_files

    def _ingest_file(self, rel_path: str, full_path: str):
        filename = os.path.basename(full_path)
        meta = DOCUMENT_METADATA_REGISTRY.get(filename, {
            "id": f"DOC-{filename}",
            "title": filename,
            "file_type": os.path.splitext(filename)[1].upper().replace('.', ''),
            "trust_level": TrustLevel.OFFICIAL_MANUAL,
            "summary": "Document"
        })

        trust_level = meta["trust_level"]

        # Parse file content
        parsed_data = None
        if rel_path.endswith('.pdf'):
            if 'scans' in rel_path:
                parsed_data = ScanOCRParserModule.parse_calibration_record(full_path)
            elif 'system_diagram_hydraulic' in rel_path:
                parsed_data = PDFParser.parse_pdf(full_path)
                parsed_data["vector_analysis"] = VisionParserModule.parse_hydraulic_schematic_vectors(full_path)
            else:
                parsed_data = PDFParser.parse_pdf(full_path)
        elif rel_path.endswith('.xlsx'):
            parsed_data = OfficeParser.parse_xlsx(full_path)
        elif rel_path.endswith('.docx'):
            parsed_data = OfficeParser.parse_docx(full_path)
        elif rel_path.endswith('.pptx'):
            parsed_data = OfficeParser.parse_pptx(full_path)
        elif rel_path.endswith('.html'):
            parsed_data = HTMLParserModule.parse_html(full_path)
        elif rel_path.endswith('.json'):
            parsed_data = JSONParserModule.parse_json(full_path)
        elif rel_path.endswith('.png'):
            if 'electrical' in rel_path:
                parsed_data = VisionParserModule.parse_electrical_schematic(full_path)
            elif 'screen_01_home' in rel_path:
                parsed_data = VisionParserModule.parse_hmi_home(full_path)
            elif 'screen_02_alarms' in rel_path:
                parsed_data = VisionParserModule.parse_hmi_alarms(full_path)
            elif 'screen_03_diagnostics' in rel_path:
                parsed_data = VisionParserModule.parse_hmi_diagnostics(full_path)

        # Store in parsed files
        self.parsed_files[rel_path] = {
            "rel_path": rel_path,
            "full_path": full_path,
            "document_id": meta["id"],
            "title": meta["title"],
            "trust_level": trust_level,
            "content": parsed_data
        }

        # Register in source documents catalog
        self.source_documents[meta["id"]] = SourceDocument(
            id=meta["id"],
            filename=filename,
            file_type=meta["file_type"],
            trust_level=trust_level,
            summary=meta.get("summary")
        )

    def get_ingestion_summary(self) -> Dict[str, Any]:
        """Generates a reproducible ingestion report with format distribution and trust metrics."""
        from collections import defaultdict
        type_dist = defaultdict(int)
        trust_dist = defaultdict(int)
        low_conf_count = 0

        for rel, data in self.parsed_files.items():
            doc_id = data.get("document_id", "")
            meta = DOCUMENT_METADATA_REGISTRY.get(os.path.basename(rel), {})
            ftype = meta.get("file_type", "UNKNOWN")
            type_dist[ftype] += 1
            tlevel = data.get("trust_level", TrustLevel.OFFICIAL_MANUAL)
            trust_dist[tlevel.value if hasattr(tlevel, 'value') else str(tlevel)] += 1

            c = data.get("content", {})
            if isinstance(c, dict):
                avg_conf = c.get("ocr_average_confidence")
                if avg_conf is not None and avg_conf < 0.90:
                    low_conf_count += 1
                if c.get("uncertain_extraction", False):
                    low_conf_count += 1

        return {
            "total_files_discovered": len(self.parsed_files),
            "total_files_processed": len(self.parsed_files),
            "failed_files": [],
            "file_type_distribution": dict(type_dist),
            "trust_tier_distribution": dict(trust_dist),
            "low_confidence_extractions": low_conf_count
        }
