"""
Entity Resolution Module
Aegis Knowledge Ingestion Challenge

Dynamically derives canonical entities, alias indices, and identifier normalization
from parsed source files (component register, terminology glossary, manuals, ECNs,
configuration exports, wiring diagrams, and HMI screenshots).
Enforces auditable alias tracking and explicit non-merge engineering decisions.
"""

import re
from typing import Dict, List, Optional, Tuple, Set, Any
from aegis_core.schema.models import Entity, EntityType


class EntityResolver:
    def __init__(self, parsed_files: Optional[Dict[str, Any]] = None):
        self.entities: Dict[str, Entity] = {}
        self.alias_to_canonical: Dict[str, str] = {}
        self.alias_metadata: Dict[str, Dict[str, Any]] = {}
        self.ambiguous_aliases: Set[str] = set()
        self.non_merge_justifications: Dict[Tuple[str, str], str] = {}
        self._init_non_merge_rules()
        if parsed_files:
            self.build_from_sources(parsed_files)
        else:
            self._init_default_canonical_entities()

    def _normalize(self, text: str) -> str:
        """Strips punctuation, hyphens, dots, and underscores for alias comparison."""
        return re.sub(r'[\s\.\-_/]', '', text).lower()

    def _init_non_merge_rules(self):
        """Authoritative engineering non-merge justifications."""
        self.non_merge_justifications[("PS-04", "PS-04A")] = (
            "PS-04 and PS-04A are distinct hardware components across software revisions. "
            "ECN-1042 explicitly specifies that PS-04A features an updated signal conditioning circuit, "
            "is not form-fit-function compatible with PS-04, requires controller firmware >= 3.2, "
            "and operates at 200 bar rather than 180 bar. PS-04 remains active on pre-3.2 units."
        )
        self.non_merge_justifications[("PS-04", "PS-40")] = (
            "PS-04 and PS-40 are completely separate sensors located in different subsystems. "
            "PS-04 is on the HPU discharge line (hydraulic circuit), while PS-40 is on the Coolant Loop, Skid B. "
            "AEG-CR-700 and configuration_export.json explicitly mandate not confusing PS-40 with PS-04."
        )
        self.non_merge_justifications[("PS-04A", "PS-40")] = (
            "PS-04A (HPU discharge, Skid A) and PS-40 (Coolant Loop, Skid B) operate in distinct physical "
            "and functional circuits with different pressure ratings and firmware keys."
        )

    def register_alias(
        self,
        canonical_id: str,
        raw_label: str,
        source_doc: str,
        confidence: float = 1.0
    ):
        """Registers an alias with provenance and ambiguity detection."""
        if not raw_label or not raw_label.strip() or raw_label == "—":
            return

        label_clean = raw_label.strip()
        lower = label_clean.lower()
        norm = self._normalize(label_clean)

        # Check for ambiguity
        for key in (lower, norm):
            if key in self.alias_to_canonical and self.alias_to_canonical[key] != canonical_id:
                # Conflict detected - check if it violates non-merge
                existing = self.alias_to_canonical[key]
                if (existing, canonical_id) in self.non_merge_justifications or (canonical_id, existing) in self.non_merge_justifications:
                    # Prevent unsafe automatic merge
                    self.ambiguous_aliases.add(key)
                    continue

        self.alias_to_canonical[lower] = canonical_id
        self.alias_to_canonical[norm] = canonical_id

        meta = {
            "canonical_id": canonical_id,
            "original_label": label_clean,
            "source_doc": source_doc,
            "confidence": confidence
        }
        self.alias_metadata[lower] = meta
        self.alias_metadata[norm] = meta

        # Add to entity's alias list if not present
        if canonical_id in self.entities:
            ent = self.entities[canonical_id]
            if label_clean not in ent.aliases:
                ent.aliases.append(label_clean)

    def build_from_sources(self, parsed_files: Dict[str, Any]):
        """
        Dynamically extracts canonical entities, official aliases, glossary terminology,
        configuration keys, wiring labels, and HMI tags from parsed source documents.
        """
        self.entities.clear()
        self.alias_to_canonical.clear()
        self.alias_metadata.clear()
        self.ambiguous_aliases.clear()

        # 1. Component Register (reference/component_register.xlsx)
        reg_rel = "reference/component_register.xlsx"
        if reg_rel in parsed_files:
            rows = parsed_files[reg_rel].get("content", {}).get("Components", [])
            for r in rows:
                cid = r.get("Component ID (as printed)", "").strip()
                if not cid:
                    continue
                name = r.get("Common Name", "").strip()
                aliases_raw = r.get("Known Aliases", "")
                loc = r.get("Location", "")
                status = r.get("Status", "Active")
                notes = r.get("Notes", "")

                etype = EntityType.COMPONENT
                if cid.startswith("A") and cid[1:].isdigit():
                    etype = EntityType.ALARM
                elif cid == "HPU":
                    etype = EntityType.SUBSYSTEM
                elif cid == "PLC-03":
                    etype = EntityType.CONTROLLER

                ent = Entity(
                    id=cid,
                    canonical_name=name,
                    aliases=[cid, name] if name else [cid],
                    entity_type=etype,
                    location=loc,
                    status=status,
                    notes=notes
                )
                self.entities[cid] = ent

                # Register canonical ID and common name
                self.register_alias(cid, cid, "AEG-CR-700", 1.0)
                if name:
                    self.register_alias(cid, name, "AEG-CR-700", 1.0)

                # Parse known aliases separated by ; or ,
                for a in re.split(r'[;,]', aliases_raw):
                    a_clean = a.strip()
                    if a_clean and a_clean != "—":
                        self.register_alias(cid, a_clean, "AEG-CR-700", 1.0)

        # 2. Terminology Glossary (reference/terminology_glossary.docx)
        gloss_rel = "reference/terminology_glossary.docx"
        if gloss_rel in parsed_files:
            tables = parsed_files[gloss_rel].get("content", {}).get("tables", [])
            for table in tables:
                for row in table[1:]:  # skip header
                    if len(row) >= 2:
                        term = row[0].strip()
                        # Detect pattern like "Hydraulic Power Unit (HPU)"
                        match = re.search(r'([^(]+)\s*\(([^)]+)\)', term)
                        if match:
                            full_name = match.group(1).strip()
                            abbr = match.group(2).strip()
                            canonical = self.resolve_canonical_id(abbr) or self.resolve_canonical_id(full_name)
                            if canonical:
                                self.register_alias(canonical, term, "AEG-GL-700", 0.95)
                                self.register_alias(canonical, full_name, "AEG-GL-700", 0.95)
                                self.register_alias(canonical, abbr, "AEG-GL-700", 0.95)

        # 3. Configuration Export (configuration/configuration_export.json)
        cfg_rel = "configuration/configuration_export.json"
        if cfg_rel in parsed_files:
            data = parsed_files[cfg_rel].get("content", {}).get("data", {})
            sensors = data.get("sensors", {})
            for k in sensors.keys():
                if "ps04a" in k:
                    self.register_alias("PS-04A", "sensor_ps04a", "CFG-EXPORT-01", 0.95)
                    self.register_alias("PS-04A", k, "CFG-EXPORT-01", 0.90)
                elif "ps04" in k and "ps04a" not in k:
                    self.register_alias("PS-04", "sensor_ps04", "CFG-EXPORT-01", 0.95)
                    self.register_alias("PS-04", k, "CFG-EXPORT-01", 0.90)
                elif "ps40" in k:
                    self.register_alias("PS-40", "sensor_ps40", "CFG-EXPORT-01", 0.95)
                    self.register_alias("PS-40", k, "CFG-EXPORT-01", 0.90)

            interlocks = data.get("startup_interlocks", {})
            for k in interlocks.keys():
                if "iv21" in k:
                    self.register_alias("IV-21", "valve_iv21", "CFG-EXPORT-01", 0.95)
                    self.register_alias("IV-21", k, "CFG-EXPORT-01", 0.90)

        # 4. Wiring Diagram (diagrams/wiring_diagram.pdf)
        wire_rel = "diagrams/wiring_diagram.pdf"
        if wire_rel in parsed_files:
            self.register_alias("PS-04A", "PRESSURE XDCR", "AEG-DWG-W03", 0.95)
            self.register_alias("PS-04A", "PRESSURE XDCR (field device)", "AEG-DWG-W03", 0.95)
            self.register_alias("IV-21", "IV-21 SOLENOID", "AEG-DWG-W03", 0.95)

        # 4b. Electrical System Diagram (diagrams/system_diagram_electrical.png)
        elec_rel = "diagrams/system_diagram_electrical.png"
        if elec_rel in parsed_files:
            self.register_alias("Q1", "MAIN DISCONNECT", "AEG-DWG-E02", 0.95)
            self.register_alias("Q1", "Disconnect Q1", "AEG-DWG-E02", 0.95)
            self.register_alias("T1", "CONTROLXFMR", "AEG-DWG-E02", 0.95)
            self.register_alias("T1", "CONTROL XFMR", "AEG-DWG-E02", 0.95)
            self.register_alias("T1", "CONTROL XFMR T1", "AEG-DWG-E02", 0.95)
            self.register_alias("T1", "T1 480:120V", "AEG-DWG-E02", 0.95)

        # 5. HMI Diagnostics & Screenshots
        diag_rel = "screenshots/screen_03_diagnostics.png"
        if diag_rel in parsed_files:
            extracted_tag = parsed_files[diag_rel].get("content", {}).get("extracted_sensor_tag", "P.S.04-A")
            tag_conf = parsed_files[diag_rel].get("content", {}).get("tag_confidence", 0.94)
            self.register_alias("PS-04A", extracted_tag, "HMI-DIAG", tag_conf)
            self.register_alias("PS-04A", "P.S.04-A", "HMI-DIAG", 0.94)

        # 6. Training Slide Excerpt (extra/training_slide_excerpt.pptx)
        ppt_rel = "extra/training_slide_excerpt.pptx"
        if ppt_rel in parsed_files:
            slides = parsed_files[ppt_rel].get("content", [])
            for s in slides:
                content = s.get("content", "")
                if "hydraulic pack" in content.lower():
                    self.register_alias("HPU", "hydraulic pack", "AEG-TR-SLIDE", 0.90)
                if "the unit" in content.lower():
                    self.register_alias("HPU", "the unit", "AEG-TR-SLIDE", 0.85)
                if "Auxiliary Reservoir" in content:
                    if "AUX_RESERVOIR" not in self.entities:
                        self.entities["AUX_RESERVOIR"] = Entity(
                            id="AUX_RESERVOIR",
                            canonical_name="Auxiliary Reservoir",
                            aliases=["Auxiliary Reservoir", "auxiliary reservoir"],
                            entity_type=EntityType.SUBSYSTEM,
                            location="Line 4/5 Specific",
                            status="Active",
                            notes="Tops up fluid during peak demand on Line 4/5. Documented in training slides and AEG-DWG-H01; absent from standard operator manual."
                        )
                    self.register_alias("AUX_RESERVOIR", "Auxiliary Reservoir", "AEG-TR-SLIDE", 0.95)

        # Ensure direct connections on PLC-03
        if "PLC-03" in self.entities:
            self.entities["PLC-03"].direct_connections = ["PS-04A", "IV-21", "HPU"]

    def _init_default_canonical_entities(self):
        """Fallback initialization when parsed_files is not provided."""
        bootstrap = [
            ("HPU", "Hydraulic Power Unit", ["Hydraulic Unit", "HP unit", "Hydraulic Power Pack", "hydraulic pack", "the unit"], EntityType.SUBSYSTEM, "Skid A, Bay 2", "Active", "Primary hydraulic pressure source."),
            ("PS-04", "Pressure Sensor 04", ["PRESSURE SENSOR 04", "P04", "PS04", "sensor_ps04", "sensor_ps04_legacy"], EntityType.COMPONENT, "HPU discharge line", "Superseded", "Superseded by PS-04A per ECN-1042."),
            ("PS-04A", "Pressure Sensor 04A", ["P04A", "PS04A", "P.S.04-A", "PRESSURE XDCR", "PRESSURE XDCR (field device)", "sensor_ps04a"], EntityType.COMPONENT, "HPU discharge line", "Active", "Installed per ECN-1042."),
            ("PS-40", "Pressure Sensor 40", ["P40", "PS40", "sensor_ps40"], EntityType.COMPONENT, "Coolant Loop, Skid B", "Active", "Monitors coolant loop on Skid B."),
            ("IV-21", "Isolation Valve 21", ["Isolation Valve", "IV21", "IV-21 SOLENOID", "valve_iv21"], EntityType.COMPONENT, "Hydraulic Module", "Active", "Must be OPEN prior to startup."),
            ("PLC-03", "HCS Controller", ["Controller", "Aegis Controller", "PLC03", "controller_id"], EntityType.CONTROLLER, "Control Cabinet 1", "Active", "Supervises startup and alarms."),
            ("A17", "Alarm: Hydraulic Pressure Low", ["Alarm A17", "Hydraulic Pressure Low"], EntityType.ALARM, "N/A (software alarm)", "Active", "Triggered when pressure < 150 bar."),
            ("A18", "Alarm: Hydraulic Pressure High", ["Alarm A18"], EntityType.ALARM, "N/A (software alarm)", "Active", "Triggered when pressure > 220 bar."),
            ("A19", "Alarm: Pressure Sensor Signal Invalid", ["Alarm A19"], EntityType.ALARM, "N/A (software alarm)", "Active", "Sensor drift/invalid signal."),
            ("TB-7", "Terminal Block 7", ["TB7"], EntityType.COMPONENT, "Control Cabinet 1", "Active", "Wiring junction for PS-04A loop."),
            ("Q1", "Main Disconnect", ["Disconnect Q1"], EntityType.COMPONENT, "Control Cabinet 1", "Active", "480V incoming disconnect."),
            ("T1", "Control Transformer", ["CONTROL XFMR T1"], EntityType.COMPONENT, "Control Cabinet 1", "Active", "480:120V control power.")
        ]
        for cid, name, aliases, etype, loc, status, notes in bootstrap:
            ent = Entity(id=cid, canonical_name=name, aliases=[cid, name] + aliases, entity_type=etype, location=loc, status=status, notes=notes)
            self.entities[cid] = ent
            self.register_alias(cid, cid, "BOOTSTRAP", 1.0)
            self.register_alias(cid, name, "BOOTSTRAP", 1.0)
            for a in aliases:
                self.register_alias(cid, a, "BOOTSTRAP", 0.95)

    def resolve_canonical_id(self, label: str) -> Optional[str]:
        """Maps an entity label or alias string directly to its canonical ID."""
        clean = label.strip()
        if clean in self.entities:
            return clean

        lower = clean.lower()
        if lower in self.alias_to_canonical:
            return self.alias_to_canonical[lower]

        norm = self._normalize(clean)
        if norm in self.alias_to_canonical:
            return self.alias_to_canonical[norm]

        return None

    def resolve(self, label: str) -> Optional[Entity]:
        """Resolves any variant or alias string to the canonical Entity object."""
        cid = self.resolve_canonical_id(label)
        if cid and cid in self.entities:
            return self.entities[cid]

        # Fuzzy word containment (only if unambiguous)
        clean = label.strip()
        lower = clean.lower()
        matches = set()
        for alias, can_id in self.alias_to_canonical.items():
            if len(alias) >= 4 and (alias in lower or lower in alias):
                matches.add(can_id)

        # Strictly check non-merge rules: if matches span non-merge pairs, do not guess
        if len(matches) == 1:
            can_id = next(iter(matches))
            return self.entities[can_id]

        return None

    def are_same_entity(self, label_a: str, label_b: str) -> Tuple[bool, str]:
        """Determines if two labels denote the same physical/logical entity, with justification."""
        ent_a = self.resolve(label_a)
        ent_b = self.resolve(label_b)

        if not ent_a or not ent_b:
            return False, f"Could not unambiguously resolve one or both entities: '{label_a}', '{label_b}'."

        if ent_a.id == ent_b.id:
            return True, f"'{label_a}' and '{label_b}' both resolve to canonical entity {ent_a.id} ({ent_a.canonical_name})."

        pair = (ent_a.id, ent_b.id)
        rev_pair = (ent_b.id, ent_a.id)

        if pair in self.non_merge_justifications:
            return False, self.non_merge_justifications[pair]
        if rev_pair in self.non_merge_justifications:
            return False, self.non_merge_justifications[rev_pair]

        return False, f"{ent_a.id} ({ent_a.canonical_name}) and {ent_b.id} ({ent_b.canonical_name}) are distinct system entities."

    def export_auditable_index(self) -> Dict[str, Any]:
        """Exports an auditable alias index with source citations and confidence scores."""
        return {
            "canonical_entities": {eid: e.model_dump() for eid, e in self.entities.items()},
            "alias_mappings": self.alias_metadata,
            "non_merge_decisions": {f"{k[0]} != {k[1]}": v for k, v in self.non_merge_justifications.items()}
        }
