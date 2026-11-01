"""
Ingestion Coordinator
Dispatches all 20 files across 8 formats to dedicated parsers and stamps initial trust levels.
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


class IngestionCoordinator:
    def __init__(self, dataset_root: str):
        self.dataset_root = dataset_root
        self.parsed_files: Dict[str, Any] = {}
        self.source_documents: Dict[str, SourceDocument] = {}

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
        # 1. Determine Trust Level and file type
        trust_level = TrustLevel.OFFICIAL_MANUAL
        if 'engineering_bulletins' in rel_path or 'revision_history' in rel_path or 'configuration' in rel_path:
            trust_level = TrustLevel.ENGINEERING_BULLETIN
        elif 'low_trust' in rel_path or 'scans' in rel_path:
            trust_level = TrustLevel.FIELD_RECORD_LOW_TRUST
        elif 'noise' in rel_path:
            trust_level = TrustLevel.NOISE_EXTERNAL

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

        self.parsed_files[rel_path] = {
            "rel_path": rel_path,
            "full_path": full_path,
            "trust_level": trust_level,
            "content": parsed_data
        }

