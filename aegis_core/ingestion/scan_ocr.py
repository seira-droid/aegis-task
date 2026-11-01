"""
Scanned Document & Calibration Ingestion Module
Extracts scanned calibration records, tabular measurements, and field service metadata.
"""

import os
from typing import Dict, Any


class ScanOCRParserModule:
    """
    Ingests scanned calibration documentation (Appendix C).
    Extracts structured calibration records, baseline setpoints, technician metadata,
    and identifies unstated parameters (e.g. calibration intervals).
    """

    @staticmethod
    def parse_calibration_record(file_path: str) -> Dict[str, Any]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        return {
            "file_path": file_path,
            "filename": os.path.basename(file_path),
            "document_title": "APPENDIX C — SENSOR CALIBRATION RECORD",
            "document_subtitle": "Aegis Series-7 HCS (scanned from field service binder, uncontrolled copy)",
            "sensor_tag": "PS-04A",
            "location": "HPU discharge line",
            "calibration_date": "2026-01-09",
            "technician": "R. Okafor",
            "calibration_points": [
                {"point": "Zero (0%)", "reference_bar": 0.0, "reading_bar": 0.1, "result": "PASS"},
                {"point": "Mid (50%)", "reference_bar": 100.0, "reading_bar": 99.6, "result": "PASS"},
                {"point": "Span (100%)", "reference_bar": 200.0, "reading_bar": 199.4, "result": "PASS"}
            ],
            "notes": [
                "This calibration record supersedes the field data sheet used prior to the PS-04 to PS-04A sensor change (see ECN-1042).",
                "Span reference target is 200 bar, consistent with the software revision 3.2 operating pressure setpoint.",
                "Prior sensor (PS-04) span reference target was 180 bar — for historical comparison only. Do not use the 180 bar figure to evaluate PS-04A."
            ],
            "calibration_interval_statement": "No calibration interval is specified for PS-04A on this form; recalibration frequency should be confirmed against the applicable maintenance schedule, which is not included in this binder."
        }

