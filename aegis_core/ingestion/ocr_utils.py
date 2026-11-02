"""
Shared OCR Engine and Spatial Caching Utility
Provides singleton RapidOCR engine and disk-backed perceptual cache
for rapid, deterministic visual extraction and confidence preservation.
"""

import os
import json
import hashlib
from typing import List, Tuple, Dict, Any, Optional
from PIL import Image
import numpy as np
from rapidocr_onnxruntime import RapidOCR


class OCRManager:
    _instance: Optional[RapidOCR] = None
    _cache_file: Optional[str] = None
    _memory_cache: Dict[str, Any] = {}

    @classmethod
    def get_engine(cls) -> RapidOCR:
        if cls._instance is None:
            cls._instance = RapidOCR(det_limit_side_len=736)
        return cls._instance

    @classmethod
    def set_cache_path(cls, cache_path: str):
        cls._cache_file = cache_path
        if os.path.exists(cache_path):
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    cls._memory_cache = json.load(f)
            except Exception:
                cls._memory_cache = {}

    @classmethod
    def _save_cache(cls):
        if cls._cache_file:
            os.makedirs(os.path.dirname(os.path.abspath(cls._cache_file)), exist_ok=True)
            try:
                with open(cls._cache_file, "w", encoding="utf-8") as f:
                    json.dump(cls._memory_cache, f, indent=2)
            except Exception:
                pass

    @classmethod
    def run_ocr(cls, img: Image.Image, cache_key: Optional[str] = None, max_dim: int = 800) -> List[Tuple[List[List[float]], str, float]]:
        """
        Runs RapidOCR with bounding-box preservation and confidence extraction.
        Returns list of (box, text, confidence).
        """
        if cache_key and cache_key in cls._memory_cache:
            raw = cls._memory_cache[cache_key]
            return [(item["box"], item["text"], float(item["confidence"])) for item in raw]

        w, h = img.size
        if max(w, h) > max_dim:
            scale = max_dim / max(w, h)
            img_ocr = img.resize((int(w * scale), int(h * scale)))
        else:
            img_ocr = img

        arr = np.array(img_ocr.convert('RGB'))
        ocr = cls.get_engine()
        try:
            results, _ = ocr(arr)
            results = results or []
        except Exception:
            results = []

        parsed = []
        cache_items = []
        for res in results:
            box = [[float(coord) for coord in pt] for pt in res[0]]
            text = str(res[1])
            conf = float(res[2])
            parsed.append((box, text, conf))
            cache_items.append({"box": box, "text": text, "confidence": round(conf, 4)})

        if cache_key:
            cls._memory_cache[cache_key] = cache_items
            cls._save_cache()

        return parsed

    @classmethod
    def get_file_cache_key(cls, file_path: str) -> str:
        try:
            with open(file_path, "rb") as f:
                return hashlib.sha256(f.read()).hexdigest()[:16]
        except Exception:
            return os.path.basename(file_path)

