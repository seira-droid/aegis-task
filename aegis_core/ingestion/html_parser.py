"""
HTML Document Ingestion Module
Extracts DOM structure, headers, warning callouts, tables, and superseded banners.
"""

import os
from html.parser import HTMLParser
from typing import Dict, Any, List


class DOMTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.texts = []
        self.banner = ""
        self.warnings = []
        self.tables = []
        self.current_table = []
        self.current_row = []
        self.current_tag = None
        self.in_banner = False
        self.in_warn = False
        self.in_td_or_th = False
        self.current_cell = []

    def handle_starttag(self, tag, attrs):
        self.current_tag = tag
        attr_dict = dict(attrs)
        classes = attr_dict.get('class', '').split()
        if 'banner' in classes:
            self.in_banner = True
        if 'warn' in classes:
            self.in_warn = True
        if tag == 'table':
            self.current_table = []
        elif tag == 'tr':
            self.current_row = []
        elif tag in ('td', 'th'):
            self.in_td_or_th = True
            self.current_cell = []

    def handle_endtag(self, tag):
        if tag in ('td', 'th'):
            self.in_td_or_th = False
            self.current_row.append("".join(self.current_cell).strip())
        elif tag == 'tr':
            if self.current_row:
                self.current_table.append(self.current_row)
        elif tag == 'table':
            if self.current_table:
                self.tables.append(self.current_table)
        elif tag == 'div':
            self.in_banner = False
            self.in_warn = False
        self.current_tag = None

    def handle_data(self, data):
        cleaned = data.strip()
        if not cleaned:
            return
        if self.in_banner:
            self.banner += cleaned + " "
        elif self.in_warn:
            self.warnings.append(cleaned)
        elif self.in_td_or_th:
            self.current_cell.append(cleaned)
        else:
            self.texts.append(cleaned)


class HTMLParserModule:
    @staticmethod
    def parse_html(file_path: str) -> Dict[str, Any]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        extractor = DOMTextExtractor()
        extractor.feed(content)

        return {
            "file_path": file_path,
            "filename": os.path.basename(file_path),
            "raw_html": content,
            "banner_notice": extractor.banner.strip(),
            "warnings": extractor.warnings,
            "tables": extractor.tables,
            "extracted_text_blocks": extractor.texts
        }

