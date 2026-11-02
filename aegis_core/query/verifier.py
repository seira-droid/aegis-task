"""
Evidence and Claim Verification Module
Aegis Knowledge Ingestion Challenge

Performs actual quotation verification against original source document texts/tables/slides
and verifies that factual claims are strictly grounded in knowledge-store facts without fabrication.
"""

import re
import difflib
from typing import Dict, Any, List, Optional, Tuple
from aegis_core.schema.models import Fact, Claim, Provenance


class EvidenceVerifier:
    def __init__(self, parsed_files: Optional[Dict[str, Any]] = None):
        self.parsed_files = parsed_files or {}
        self._doc_text_cache: Dict[str, str] = {}
        if parsed_files:
            self._build_document_text_cache(parsed_files)

    def set_parsed_files(self, parsed_files: Dict[str, Any]):
        self.parsed_files = parsed_files
        self._build_document_text_cache(parsed_files)

    @staticmethod
    def normalize_text(text: str) -> str:
        """Normalizes whitespace, hyphens, and quotation marks for robust quotation matching."""
        if not text:
            return ""
        # Replace non-breaking spaces and linebreaks
        t = re.sub(r'[\s\xa0\n\r\t]+', ' ', text)
        # Normalize typographic dashes and quotes
        t = t.replace('—', '-').replace('–', '-').replace('“', '"').replace('”', '"').replace("’", "'").replace("‘", "'")
        # Strip quotes and colon/comma separators for clean token sequence matching
        t = re.sub(r'["\'`]', '', t)
        return t.strip().lower()

    def _build_document_text_cache(self, parsed_files: Dict[str, Any]):
        """Indexes all text content from parsed files by document ID and relative path."""
        for rel_path, data in parsed_files.items():
            doc_id = data.get("document_id") or rel_path
            content = data.get("content", {})
            full_text_parts = []

            # PDF pages
            if isinstance(content, dict) and "pages" in content:
                for p in content["pages"]:
                    full_text_parts.append(p.get("text", ""))

            # Office spreadsheets
            if isinstance(content, dict):
                for sheet, rows in content.items():
                    if isinstance(rows, list):
                        for r in rows:
                            if isinstance(r, dict):
                                full_text_parts.append(" ".join(f"{k}: {v}" for k, v in r.items() if v is not None))
                                full_text_parts.append(" ".join(str(v) for v in r.values() if v is not None))
                            elif isinstance(r, list):
                                full_text_parts.append(" ".join(str(v) for v in r if v is not None))

            # Office documents (DOCX)
            if isinstance(content, dict) and "paragraphs" in content:
                full_text_parts.extend(content.get("paragraphs", []))
                for t in content.get("tables", []):
                    for row in t:
                        full_text_parts.append(" ".join(str(c) for c in row if c is not None))

            # PowerPoint slides
            if isinstance(content, list):
                for s in content:
                    full_text_parts.append(s.get("content", ""))
                    for elem in s.get("text_elements", []):
                        full_text_parts.append(elem)

            # HTML
            if isinstance(content, dict) and "extracted_text_blocks" in content:
                full_text_parts.extend(content.get("extracted_text_blocks", []))
                if "banner_notice" in content and content["banner_notice"]:
                    full_text_parts.append(content["banner_notice"])

            # JSON config
            if isinstance(content, dict) and "data" in content:
                import json
                full_text_parts.append(json.dumps(content["data"]))

            # Vision / OCR text
            if isinstance(content, dict):
                if "ocr_raw_tokens" in content:
                    tokens = [t.get("text", "") for t in content.get("ocr_raw_tokens", [])]
                    full_text_parts.append(" ".join(tokens))
                if "raw_notes_text" in content:
                    full_text_parts.append(content.get("raw_notes_text", ""))

            combined = " \n ".join(full_text_parts)
            self._doc_text_cache[doc_id] = combined
            self._doc_text_cache[rel_path] = combined

    def verify_quotation(self, document_id: str, quote: str) -> Tuple[bool, float, str]:
        """
        Compares the cited verbatim quote against original parsed source content.
        Performs strict normalized full quotation matching without permissive 3-word fallbacks.
        Returns: (is_verified, match_ratio, status_and_explanation)
        Status categories:
          - VERIFIED: Exact normalized or high-fidelity token match (ratio >= 0.90)
          - PARTIAL_MATCH: Significant divergence or partial overlap (0.70 <= ratio < 0.90)
          - UNVERIFIED: Missing, wrong document, or below threshold (ratio < 0.70)
        """
        if not quote or not quote.strip():
            return False, 0.0, "UNVERIFIED: Empty or whitespace-only quote"

        norm_quote = self.normalize_text(quote)
        quote_tokens = norm_quote.split()
        if len(quote_tokens) < 2 or len(norm_quote) < 6:
            return False, 0.0, "UNVERIFIED: Quote too short to verify uniquely (<2 words or <6 chars)"

        doc_text = self._doc_text_cache.get(document_id, "")
        if not doc_text:
            return False, 0.0, f"UNVERIFIED: Document '{document_id}' not found in parsed document cache"

        norm_doc = self.normalize_text(doc_text)

        # 1. Exact normalized substring match in target document
        if norm_quote in norm_doc:
            return True, 1.0, f"VERIFIED: Exact complete normalized quotation found in document {document_id}"

        # 2. Token-level sequence alignment across candidate windows in target document
        doc_tokens = norm_doc.split()
        if not doc_tokens:
            return False, 0.0, f"UNVERIFIED: Target document '{document_id}' contains no text tokens"

        q_len = len(quote_tokens)
        candidates = []
        anchor1 = quote_tokens[0]
        anchor2 = quote_tokens[1] if q_len > 1 else anchor1

        for idx, tok in enumerate(doc_tokens):
            if tok == anchor1 or tok == anchor2:
                start_i = max(0, idx - 2)
                end_i = min(len(doc_tokens), idx + q_len + 3)
                candidates.append(doc_tokens[start_i:end_i])

        best_ratio = 0.0
        matcher = difflib.SequenceMatcher(None, quote_tokens, [])

        if not candidates and len(doc_tokens) <= 500:
            candidates.append(doc_tokens)

        for cand in candidates:
            matcher.set_seq2(cand)
            r = matcher.ratio()
            if r > best_ratio:
                best_ratio = r

        best_ratio = round(best_ratio, 4)

        if best_ratio >= 0.90:
            return True, best_ratio, f"VERIFIED: High-fidelity token match ({round(best_ratio * 100, 1)}%) in document {document_id}"
        elif best_ratio >= 0.70:
            return False, best_ratio, f"PARTIAL_MATCH: Partial quote divergence ({round(best_ratio * 100, 1)}%) in document {document_id}"
        else:
            return False, best_ratio, f"UNVERIFIED: Quote not found in document {document_id} (best match: {round(best_ratio * 100, 1)}%)"

    def verify_claim(self, claim: Any, facts_db: Dict[str, Fact]) -> Tuple[bool, str]:
        """
        Verifies that each factual claim is supported by genuine knowledge-store facts
        and that each supporting fact's quotation is verified against the source document.
        """
        supporting_fids = getattr(claim, "supporting_fact_ids", None)
        if supporting_fids is None and isinstance(claim, dict):
            supporting_fids = claim.get("supporting_fact_ids", [])

        if not supporting_fids:
            return False, "Claim has no supporting fact citations (unsupported)"

        missing_facts = [fid for fid in supporting_fids if fid not in facts_db]
        if missing_facts:
            return False, f"Claim cites nonexistent fact IDs: {missing_facts}"

        for fid in supporting_fids:
            fact = facts_db[fid]
            if not fact.provenance:
                return False, f"Supporting fact {fid} lacks provenance"

            quote = fact.provenance.verbatim_quote
            doc_id = fact.provenance.document_id
            if quote:
                verified, score, reason = self.verify_quotation(doc_id, quote)
                if not verified:
                    return False, f"Fact {fid} evidence quotation failed verification against {doc_id}: {reason}"

        return True, "Claim verified against knowledge store and source document texts"
