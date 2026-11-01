"""
Office Document Ingestion Module (XLSX, DOCX, PPTX)
Uses standard library OpenXML extraction for deterministic zero-dependency execution.
"""

import os
import zipfile
import xml.etree.ElementTree as ET
from typing import List, Dict, Any


class OfficeParser:
    @staticmethod
    def parse_xlsx(file_path: str) -> Dict[str, List[Dict[str, str]]]:
        """Parses OpenXML spreadsheet into list of row dictionaries per sheet."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        result = {}
        with zipfile.ZipFile(file_path, 'r') as z:
            # 1. Read shared strings
            shared_strings = []
            if 'xl/sharedStrings.xml' in z.namelist():
                tree = ET.fromstring(z.read('xl/sharedStrings.xml'))
                for si in tree.findall('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}si'):
                    text = ''.join(node.text for node in si.iter() if node.tag.endswith('}t') and node.text)
                    shared_strings.append(text)

            # 2. Read sheet names mapping from workbook.xml
            sheet_name_map = {}
            if 'xl/workbook.xml' in z.namelist():
                wb_tree = ET.fromstring(z.read('xl/workbook.xml'))
                for s in wb_tree.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}sheet'):
                    s_name = s.attrib.get('name')
                    s_id = s.attrib.get('sheetId')
                    if s_name and s_id:
                        sheet_name_map[f"sheet{s_id}"] = s_name

            # 3. Read worksheets
            sheet_files = [f for f in z.namelist() if f.startswith('xl/worksheets/sheet') and f.endswith('.xml')]
            ns = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'

            for sfile in sheet_files:
                tree = ET.fromstring(z.read(sfile))
                rows_data = []
                headers = []

                for row_idx, row in enumerate(tree.findall(f'.//{ns}row')):
                    cell_vals = []
                    for c in row.findall(f'{ns}c'):
                        val = ""
                        v = c.find(f'{ns}v')
                        t = c.attrib.get('t')
                        if v is not None and v.text is not None:
                            if t == 's':
                                str_idx = int(v.text)
                                val = shared_strings[str_idx] if str_idx < len(shared_strings) else ""
                            else:
                                val = v.text
                        elif c.find(f'{ns}is/{ns}t') is not None:
                            val = c.find(f'{ns}is/{ns}t').text or ""
                        cell_vals.append(val.strip())

                    if row_idx == 0:
                        headers = cell_vals
                    else:
                        # Pad row if shorter than headers
                        while len(cell_vals) < len(headers):
                            cell_vals.append("")
                        row_dict = {headers[i]: cell_vals[i] for i in range(len(headers))}
                        rows_data.append(row_dict)

                raw_sheet_id = os.path.basename(sfile).replace('.xml', '')
                final_sheet_name = sheet_name_map.get(raw_sheet_id, raw_sheet_id)
                result[final_sheet_name] = rows_data

        return result

    @staticmethod
    def parse_docx(file_path: str) -> Dict[str, Any]:
        """Parses OpenXML Word document into paragraphs and tables."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        paragraphs = []
        tables = []

        with zipfile.ZipFile(file_path, 'r') as z:
            if 'word/document.xml' not in z.namelist():
                return {"paragraphs": [], "tables": []}

            tree = ET.fromstring(z.read('word/document.xml'))
            ns_w = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'

            # Extract body elements in order
            body = tree.find(f'{ns_w}body')
            if body is not None:
                for child in body:
                    if child.tag == f'{ns_w}p':
                        p_text = ''.join(node.text for node in child.iter() if node.tag == f'{ns_w}t' and node.text)
                        if p_text.strip():
                            paragraphs.append(p_text.strip())
                    elif child.tag == f'{ns_w}tbl':
                        tbl_data = []
                        for tr in child.findall(f'{ns_w}tr'):
                            row = []
                            for tc in tr.findall(f'{ns_w}tc'):
                                cell_text = ''.join(node.text for node in tc.iter() if node.tag == f'{ns_w}t' and node.text)
                                row.append(cell_text.strip())
                            if any(row):
                                tbl_data.append(row)
                        if tbl_data:
                            tables.append(tbl_data)

        return {
            "file_path": file_path,
            "paragraphs": paragraphs,
            "tables": tables
        }

    @staticmethod
    def parse_pptx(file_path: str) -> List[Dict[str, Any]]:
        """Parses OpenXML PowerPoint deck into slide texts and notes."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        slides = []
        with zipfile.ZipFile(file_path, 'r') as z:
            slide_names = sorted(
                [f for f in z.namelist() if f.startswith('ppt/slides/slide') and f.endswith('.xml')],
                key=lambda x: int(''.join(filter(str.isdigit, os.path.basename(x)))) if any(c.isdigit() for c in x) else 0
            )

            for s_idx, sname in enumerate(slide_names):
                tree = ET.fromstring(z.read(sname))
                text_runs = []
                for node in tree.iter():
                    if node.tag.endswith('}t') and node.text:
                        text_runs.append(node.text.strip())

                slides.append({
                    "slide_number": s_idx + 1,
                    "slide_file": sname,
                    "content": " ".join([t for t in text_runs if t]),
                    "text_elements": [t for t in text_runs if t]
                })

        return slides

