"""
JSON Configuration Ingestion Module
Ingests structured telemetry exports and machine parameters.
"""

import os
import json
from typing import Dict, Any


class JSONParserModule:
    @staticmethod
    def parse_json(file_path: str) -> Dict[str, Any]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return {
            "file_path": file_path,
            "filename": os.path.basename(file_path),
            "data": data,
            "keys_present": list(data.keys())
        }

