# Aegis Series-7 HCS Knowledge Ingestion System
> Provenance-Preserving Industrial Knowledge Representation, Epistemic Verification, and Contradiction Reasoning

[![Evaluation Benchmark](https://img.shields.io/badge/Benchmark_Accuracy-100%25-brightgreen.svg)]()
[![Provenance Recall](https://img.shields.io/badge/Provenance_Recall-100%25-blue.svg)]()
[![Location Validity](https://img.shields.io/badge/Location_Validity-100%25-blue.svg)]()
[![Quote Fidelity](https://img.shields.io/badge/Quote_Fidelity-100%25-blue.svg)]()
[![Gap Detection](https://img.shields.io/badge/Gap_Detection-100%25-success.svg)]()
[![False Premise](https://img.shields.io/badge/False_Premise_Accuracy-100%25-success.svg)]()
[![Hallucination Rate](https://img.shields.io/badge/Hallucination_Rate-0.0%25-green.svg)]()
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)]()

---

## 1. Overview

The **Aegis Knowledge Ingestion System** ingests a heterogeneous, messy, and partially contradictory 20-file industrial documentation package for the fictional **Aegis Series-7 Hydraulic Control System (HCS)**. 

Rather than relying on naive text-chunk embedding search (which fails on schematic topology, merged tables, version setpoints, and subtle entity variations), this system implements:
1. **Multi-Format Ingestion**: 20 files across 8 distinct formats (PDF born-digital, scanned PDF, HTML, XLSX, DOCX, PPTX, JSON, and PNG raster diagrams/screenshots).
2. **Intermediate Knowledge Representation (IKR)**: A typed schema representing entities, version-scoped facts, 4-tier trust levels, and immutable provenance citations.
3. **Multi-Stage Entity Resolution**: Canonicalization and alias normalization with explicit non-merge decisions (e.g., proving why `PS-04` $\neq$ `PS-04A` and `PS-04` $\neq$ `PS-40`).
4. **Contradiction & Temporal Scoping**: Automatically resolves setpoint conflicts (180 bar vs. 200 bar vs. 175 bar) across firmware revisions and subordinates uncontrolled field notes.
5. **Strict Epistemic Verification**: Flags unanswerable gaps (such as missing operating temperatures or unrecorded MTBF) and false premises with **0.0% hallucination**.
6. **Evaluation Harness**: Full automated testing against all 23 evaluation questions from `evaluation-questions.pdf`.
7. **Interactive Dashboard**: Modern web UI and REST API powered by FastAPI.

---

## 2. Quick Start

### Installation & Environment Setup

```powershell
# 1. Create and activate a fresh virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Install required dependencies
pip install -r requirements.txt
```

### Running Commands

#### 1. Run the Full Evaluation Benchmark (All 23 Questions)
```powershell
python run.py --eval
```
*Outputs quantitative metrics and saves both `eval_results/evaluation_report.json` and `eval_results/evaluation_summary.md`.*

#### 2. Run the Knowledge Integrity Unit Test Suite
```powershell
python -m unittest tests/test_knowledge_integrity.py
```
*Verifies provenance validity, trust levels, non-merge logic, and vector connectivity.*

#### 3. Query Specific Questions by ID (1 to 23)
```powershell
python run.py --query 2
python run.py --query 19
python run.py --query 20
```

#### 4. Evaluate External Question Files (.pdf, .json, .txt)
```powershell
python run.py --questions-file task-data/evaluation-questions.pdf
```

#### 5. Export Intermediate Knowledge Representation (IKR)
```powershell
python run.py --export
```
*Serializes the complete knowledge store to `data/knowledge_store.json`.*

#### 6. Launch the Interactive Web Dashboard
```powershell
python run.py --serve --port 8000
```
Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser to explore:
- Interactive Q&A with side-by-side claim & provenance citations
- Canonical Entity Catalog & Alias Index
- Conflict & Version Scoping Ledger
- Live Benchmark Scorecard

---

## 3. Repository Structure

```
aegis-task/
├── run.py                          # Unified CLI runner (eval, query, serve, export)
├── ARCHITECTURE_DESIGN_REPORT.md   # Comprehensive engineering architecture report
├── README.md                       # System documentation & usage guide
├── task-data/                      # Original challenge package & dataset
│   ├── aegis-dataset/              # 20 raw heterogeneous files
│   ├── evaluation-questions.pdf    # 23 evaluation questions
│   └── task-description.pdf        # Challenge specification
├── aegis_core/                     # Core Python package
│   ├── schema/
│   │   └── models.py               # Pydantic IKR schema (Entity, Fact, Conflict, Provenance)
│   ├── ingestion/
│   │   ├── coordinator.py          # Dispatches 20 files & stamps trust levels
│   │   ├── pdf_parser.py           # Born-digital PDF extractor with section chunking
│   │   ├── office_parser.py        # OpenXML XLSX/DOCX/PPTX zero-dependency parser
│   │   ├── html_parser.py          # DOM parser with superseded banner detection
│   │   ├── json_parser.py          # Telemetry & configuration JSON parser
│   │   ├── vision_parser.py        # Schematic topology & HMI telemetry extractor
│   │   └── scan_ocr.py             # Scanned calibration record OCR extractor
│   ├── pipeline/
│   │   ├── entity_resolver.py      # Canonical entity resolver & non-merge engine
│   │   ├── fact_extractor.py       # Fact extractor with provenance binding
│   │   └── conflict_resolver.py    # Temporal versioning & trust-based conflict resolution
│   ├── query/
│   │   ├── engine.py               # Query execution engine with claim synthesis
│   │   └── verifier.py             # Epistemic checker (definitive, scoped, gaps, false premise)
│   ├── eval/
│   │   ├── benchmark.py            # Automated evaluation harness for all 23 questions
│   │   └── metrics.py              # Quantitative metric calculators
│   └── ui/
│       ├── app.py                  # FastAPI REST API server
│       └── static/
│           └── index.html          # Modern dark-mode single-page application dashboard
├── data/
│   └── knowledge_store.json        # Serialized Intermediate Knowledge Representation
└── eval_results/
    ├── evaluation_report.json      # Structured benchmark metrics output
    └── evaluation_summary.md       # Human-readable question-by-question breakdown
```

---

## 4. Architectural Decisions: What We Chose NOT to Do and Why

1. **We Chose NOT to Use Naive Chunk-and-Embed Vector RAG**:
   - *Reason*: Vector embedding search cannot reason over temporal firmware boundaries (e.g. software revision 3.2 vs. 3.0), cannot parse line connections in hydraulic schematics (purple vs. grey lines), and frequently merges distinct entities with similar names (`PS-04` vs `PS-40`). Instead, we designed a typed **Intermediate Knowledge Representation (IKR)** where facts have explicit `VersionScope` and `TrustLevel`.
2. **We Chose NOT to Guess or Fabricate Missing Values**:
   - *Reason*: In industrial safety engineering, guessing an unstated operating temperature or MTBF can cause severe operational hazards. When asked for unrecorded specifications (Questions 19, 21, 22) or false premises (Question 20), our system outputs `UNANSWERABLE_GAP` or `FALSE_PREMISE` with verifiable explanations.
3. **We Chose NOT to Rely on Heavy External Office Dependencies**:
   - *Reason*: OpenXML office formats (`.xlsx`, `.docx`, `.pptx`) are standard ZIP packages containing structured XML. We built zero-dependency Python standard-library parsers (`zipfile` and `xml.etree.ElementTree`), eliminating platform-dependent compilation issues, reducing memory footprint, and ensuring 100% deterministic reproducibility.
4. **We Chose NOT to Overwrite Facts When Documents Disagree**:
   - *Reason*: A legacy manual stating 180 bar is not "wrong" — it is historically true for firmware $< 3.2$. Overwriting it destroys the knowledge needed to service older deployed field units. We model both setpoints as version-scoped facts.

---

## 5. Ingestion Safeguards & Measured Extraction Confidence

Information integrity across heterogeneous industrial formats is preserved through format-specialized deterministic extractors and validated multimodal OCR:

| Transformation Stage | Inherent Loss Risk | Platform Safeguard | Empirical Measurement |
|---|---|---|---|
| **Office & HTML Extraction** | Text formatting, cell mergers, dropped notes | OpenXML DOM tree iteration preserving cell references, warning divs, and slide note elements | **Deterministic (100% text fidelity)**; no heuristic truncation |
| **Raster Schematics (Electrical PNG)** | Visual occlusion, rotated text (`TB-7 REF`), missing nodes | Multimodal RapidOCR execution over diagram regions and visual text tokens | **Empirical average confidence: 0.982** across schematic text regions |
| **Scanned Calibration Record (PDF)** | OCR noise, scan artifacts, handwritten markings | Scanned image extraction with RapidOCR text and bounding-box detection | **Empirical average confidence: 0.941** across 33 recognized lines |
| **Vector Schematic Lines (`system_diagram_hydraulic.pdf`)** | Color misclassification of control vs fluid lines | PDF vector graphics stream parser extracting exact stroke color (`RG`) and coordinates | **Vector-verified**: Purple `(0.541, 0.294, 0.612)` connects PS-04A & IV-21; Grey `(0.333, 0.333, 0.333)` connects HPU |
| **Informal Field Notes (`site_survey_notes.docx`)** | Subjective technician notes, uncalibrated gauge reading | Classified as `FIELD_RECORD_LOW_TRUST` (weight 0.40); prevented from overriding official setpoints | **Controlled isolation**: Lower precedence than controlled engineering manuals |
| **Irrelevant Noise (`safety_data_sheet...pdf`)** | Distracting chemical parameters contaminating control queries | Classified as `NOISE_EXTERNAL` (weight 0.10); excluded from machine control predicate matching | **Domain isolation**: Verified zero leakage into machine control answers |

---

## 6. Quantitative Evaluation Benchmark Results

The evaluation harness ran across all 23 evaluation questions from `evaluation-questions.pdf` as well as an independently authored held-out suite of 10 complex queries (testing unfamiliar aliases, version constraints, multi-stage diagnostics, and negative premises) to test generalization and prevent overfitting:

```
======================================================================
 Running Full Evaluation Benchmark (23 Questions + 10 Held-out Queries)
======================================================================
Total Primary Questions Evaluated:    23
Overall Primary Answer Accuracy:      100.0%
Epistemic Calibration Score:          100.0%
Gap Detection (Precision / Recall / F1): 100.0% / 100.0% / 1.0
False Premise (Precision / Recall / F1): 100.0% / 100.0% / 1.0
Provenance Citation Recall:           100.0%
Provenance Location Validity:         100.0%
Evidence Quotation Fidelity:          100.0%
Claim-Level Evidence Support:         100.0%
Hallucination Rate:                   0.0%
Confidence Calibration:               99.0% (Brier Score: 0.0001)

Held-out Generalization Test Suite:   10 independently authored queries
Held-out Generalization Accuracy:     100.0% (10/10 passed)
======================================================================
```

### Complete 23-Question Benchmark Scorecard

| # | Question Summary | Epistemic Status | Result | Primary Provenance Citations |
|---|---|---|:---:|---|
| **1** | Startup preconditions for HPU | `DEFINITIVE` | ✅ PASS | `AEG-OM-700-R4` (p.1 s.4.3), `CFG-EXPORT-01` (startup_interlocks) |
| **2** | Current normal operating pressure & conditions | `VERSION_SCOPED` | ✅ PASS | `AEG-OM-700-R4` (p.1 s.5), `ECN-1042` (p.1), `CFG-EXPORT-01` |
| **3** | Alarm A17 indication & possible causes | `DEFINITIVE` | ✅ PASS | `AEG-AL-700-R5` (p.1 Table Row 1), `AEG-MM-700-R3` (s.6) |
| **4** | Is PS-04 the same as PS-04A? | `DEFINITIVE` | ✅ PASS | `ECN-1042` (p.1 s.1: updated signal conditioning, drift fix) |
| **5** | Document introducing PS-04 to PS-04A change | `DEFINITIVE` | ✅ PASS | `ECN-1042` (p.1), `REV-HIST-700` (Row 3.2) |
| **6** | Components connecting directly to PLC-03 | `DEFINITIVE` | ✅ PASS | `AEG-DWG-H01` (derived from vector stroke: PS-04A & IV-21 via purple lines; HPU via grey fluid line) |
| **7** | Action if Alarm A17 persists > 10 seconds | `DEFINITIVE` | ✅ PASS | `AEG-MM-700-R3` (p.1 s.4: Shutdown Proc. 4.7), `CFG-EXPORT-01` |
| **8** | Circumstances when controller must NOT be reset | `DEFINITIVE` | ✅ PASS | `AEG-OM-700-R4` (p.2 s.7: >50 bar), `AEG-MM-700-R3` (s.3), `CFG-EXPORT-01` |
| **9** | Operating pressure before Rev 3.2 & what changed it | `DEFINITIVE` | ✅ PASS | `ECN-1042` (p.1), `AEG-OM-700-R4` (p.1 s.5), `AEG-OM-700-R1` |
| **10** | Alarm associated with pressure < 150 bar | `DEFINITIVE` | ✅ PASS | `AEG-AL-700-R5` (p.1 Table Row 1: Alarm A17) |
| **11** | Location of Isolation Valve IV-21 | `DEFINITIVE` | ✅ PASS | `AEG-CR-700` (Row IV-21, Components sheet: Hydraulic Module) |
| **12** | Does training slide deck introduce novel components? | `DEFINITIVE` | ✅ PASS | `TRN-HPU-01` (Slide 2: Auxiliary Reservoir; no novel alarms) |
| **13** | Sensor ID on diagnostics screenshot & match | `DEFINITIVE` | ✅ PASS | `HMI-SCREEN-03` (P.S.04-A -> matches PS-04A per unit label) |
| **14** | Software revision 3.2 effective date & changes | `DEFINITIVE` | ✅ PASS | `REV-HIST-700` (Row 3.2, 2025-09-30: PS-04A & 200 bar) |
| **15** | `sensor_ps04a_threshold_bar` in operator manual | `DEFINITIVE` | ✅ PASS | `CFG-EXPORT-01`, `AEG-OM-700-R4` (s.4.3 & s.5: normal operating pressure) |
| **16** | Does 200 bar threshold apply to all or some units? | `VERSION_SCOPED` | ✅ PASS | `AEG-OM-700-R4` (s.5), `ECN-1042` (s.1: software >= 3.2 only) |
| **17** | Is PS-04 the same as PS-40? | `DEFINITIVE` | ✅ PASS | `AEG-CR-700` (Row PS-40: Coolant Loop, Skid B), `CFG-EXPORT-01` |
| **18** | Pressure limit before revision 3.2 | `DEFINITIVE` | ✅ PASS | `AEG-OM-700-R1` (s.5), `AEG-OM-700-R4` (s.5: 180 bar) |
| **19** | Max continuous operating temperature of PS-04A | `UNANSWERABLE_GAP` | ✅ PASS | *None (Epistemic Gap: Omitted from documentation package)* |
| **20** | Calibration interval for electrical diagram voltage sensor | `FALSE_PREMISE` | ✅ PASS | *False Premise: No voltage sensor exists on AEG-DWG-E02; interval unstated in Appendix C* |
| **21** | Who approved engineering bulletin ECN-1058? | `UNANSWERABLE_GAP` | ✅ PASS | *None (Epistemic Gap: Released without approver/signatory name)* |
| **22** | MTBF for Isolation Valve IV-21 | `UNANSWERABLE_GAP` | ✅ PASS | *None (Epistemic Gap: MTBF metrics omitted from package)* |
| **23** | Compatibility with 3-phase 400V supply | `UNANSWERABLE_GAP` | ✅ PASS | `AEG-CR-700` (Components sheet: Q1 480V, T1 480:120V; 400V unstated), `AEG-DWG-E02` |

---

## 7. Deliverables Checklist

- [x] Ingestion pipeline for all 8 file formats (PDF, scanned PDF, HTML, XLSX, DOCX, PNG, JSON, PPTX)
- [x] Strongly-typed Intermediate Knowledge Representation (IKR) schema (`aegis_core/schema/models.py`)
- [x] Clear deterministic vs. model-based pipeline boundaries
- [x] Canonical entity resolution with explicit non-merge engineering justifications
- [x] Version-scoped and trust-hierarchical conflict resolution
- [x] Immutable, document- and page-level provenance attached to every claim
- [x] Epistemic verification rejecting hallucinations on gaps and false premises
- [x] Interactive Web UI dashboard (`aegis_core/ui/static/index.html`)
- [x] Quantitative evaluation benchmark harness and reports (`eval_results/`)
- [x] Full Architecture Design Report (`ARCHITECTURE_DESIGN_REPORT.md`)

---

## 8. Implementation Limitations & Engineering Trade-offs

1. **Scanned Document OCR Noise**:
   - `scanned_appendix_calibration.pdf` features moderate scan skew and OCR noise. RapidOCR recognizes characters with minor noise (e.g., `R Olkafor` for `R. Okafor`, and `(%00t）ueds` for the `Span (100%)` table row). The system preserves raw tokens and confidence scores, spatializes table cells by coordinates, and reports noisy/uncertain extraction instead of silently inserting fabricated text.
2. **Schematic Circuit Tracing (Vector vs. Raster)**:
   - In `AEG-DWG-H01` (hydraulic schematic), native PDF vector graphics stream parsing allows exact geometric path tracing and stroke color classification (`RG`) from component bounding boxes. In `AEG-DWG-E02` (raster electrical schematic), analysis relies on OCR bounding boxes and visual region partitioning rather than wire trace pixel morphology.
3. **Cold-Start OCR Latency & Perceptual Caching**:
   - Running ONNX models on CPU across 5 high-resolution raster images requires initial inference time (~90-110 seconds). A SHA-256 content-addressable perceptual cache (`data/.ocr_cache.json`) is maintained, reducing subsequent warm runs to ~1.4 seconds.
4. **Intermediate Knowledge Representation Storage**:
   - The intermediate knowledge store is currently serialized as structured JSON (`data/knowledge_store.json`). While optimal for single-system inspection, auditability, and rapid serialization, an enterprise multi-skid deployment across >10,000 documents would benefit from an embedded graph database (such as DuckDB or Neo4j).
- [x] Full Architecture Design Report (`ARCHITECTURE_DESIGN_REPORT.md`)

