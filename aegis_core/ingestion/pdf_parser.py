"""
PDF Document Ingestion Module
Handles born-digital PDF extraction with page-level provenance and structural chunking.
"""

import os
from typing import List, Dict, Any
import pypdf


class PDFParser:
    @staticmethod
    def parse_pdf(file_path: str) -> Dict[str, Any]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        reader = pypdf.PdfReader(file_path)
        pages_data = []

        for idx, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            pages_data.append({
                "page_number": idx + 1,
                "text": text,
                "line_count": len(text.splitlines()),
                "char_count": len(text)
            })

        return {
            "file_path": file_path,
            "filename": os.path.basename(file_path),
            "page_count": len(reader.pages),
            "pages": pages_data
        }

