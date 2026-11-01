"""
Entity Resolution Module
Performs canonicalization, alias indexing, identifier normalization,
and explicit non-merge decisions with full engineering justifications.
"""

import re
from typing import Dict, List, Optional, Tuple
from aegis_core.schema.models import Entity, EntityType


class EntityResolver:
    def __init__(self):
        self.entities: Dict[str, Entity] = {}
        self.alias_to_canonical: Dict[str, str] = {}
        self.non_merge_justifications: Dict[Tuple[str, str], str] = {}
        self._init_canonical_entities()

    def _normalize(self, text: str) -> str:
        """Strips punctuation, hyphens, dots, and underscores for fuzzy alias comparison."""
        return re.sub(r'[\s\.\-_/]', '', text).lower()

    def _init_canonical_entities(self):
        raw_definitions = [
            Entity(
                id="HPU",
                canonical_name="Hydraulic Power Unit",
                aliases=[
                    "Hydraulic Power Unit",
                    "Hydraulic Unit",
                    "HP unit",
                    "Hydraulic Power Pack",
                    "hydraulic pack",
                    "the unit",
                    "HPU"
                ],
                entity_type=EntityType.SUBSYSTEM,
                location="Skid A, Bay 2",
                status="Active",
                notes="Primary hydraulic pressure source for the press circuit. Unifies HPU, HP unit, and Hydraulic Power Pack per AEG-OM-700 Rev 4 and AEG-CR-700."
            ),
            Entity(
                id="PS-04",
                canonical_name="Pressure Sensor 04",
                aliases=[
                    "Pressure Sensor 04",
                    "PRESSURE SENSOR 04",
                    "P04",
                    "PS04",
                    "sensor_ps04",
                    "sensor_ps04_legacy"
                ],
                entity_type=EntityType.COMPONENT,
                location="HPU discharge line",
                status="Superseded",
                notes="Superseded by PS-04A effective software revision 3.2 per ECN-1042. Normal setpoint was 180 bar."
            ),
            Entity(
                id="PS-04A",
                canonical_name="Pressure Sensor 04A",
                aliases=[
                    "Pressure Sensor 04A",
                    "P04A",
                    "PS04A",
                    "P.S.04-A",
                    "PRESSURE XDCR",
                    "PRESSURE XDCR (field device)",
                    "sensor_ps04a",
                    "PS-04A"
                ],
                entity_type=EntityType.COMPONENT,
                location="HPU discharge line",
                status="Active",
                notes="Installed per ECN-1042. Requires firmware >= 3.2. Normal setpoint is 200 bar. Solves 18-month drift. Wired at J-14/TB-7 per AEG-DWG-W03."
            ),
            Entity(
                id="PS-40",
                canonical_name="Pressure Sensor 40",
                aliases=["Pressure Sensor 40", "P40", "PS40", "sensor_ps40"],
                entity_type=EntityType.COMPONENT,
                location="Coolant Loop, Skid B",
                status="Active",
                notes="Monitors coolant loop on Skid B. NOT related to HPU discharge circuit. Do not confuse with PS-04 or PS-04A."
            ),
            Entity(
                id="IV-21",
                canonical_name="Isolation Valve 21",
                aliases=["Isolation Valve 21", "Isolation Valve", "IV21", "IV-21", "IV-21 SOLENOID", "valve_iv21"],
                entity_type=EntityType.COMPONENT,
                location="Hydraulic Module",
                status="Active",
                notes="Isolates HPU from press circuit. Interlocked: must be OPEN prior to HPU startup."
            ),
            Entity(
                id="PLC-03",
                canonical_name="HCS Controller",
                aliases=["HCS Controller", "Controller", "Aegis Controller", "PLC-03", "PLC03", "controller_id"],
                entity_type=EntityType.CONTROLLER,
                location="Control Cabinet 1",
                status="Active",
                notes="Supervises startup sequencing, alarms, interlocks, and sensor evaluation.",
                direct_connections=["PS-04A", "IV-21"]
            ),
            Entity(
                id="A17",
                canonical_name="Alarm A17 (Hydraulic Pressure Low)",
                aliases=["A17", "Alarm A17", "Hydraulic Pressure Low", "hydraulic_pressure_low"],
                entity_type=EntityType.ALARM,
                status="Active",
                notes="Triggered when pressure < 150 bar. Requires Shutdown Procedure 4.7 if persistent > 10 seconds."
            ),
            Entity(
                id="A18",
                canonical_name="Alarm A18 (Hydraulic Pressure High)",
                aliases=["A18", "Alarm A18", "Hydraulic Pressure High", "hydraulic_pressure_high"],
                entity_type=EntityType.ALARM,
                status="Active",
                notes="Triggered when pressure > 220 bar. Immediate HPU stop required."
            ),
            Entity(
                id="A19",
                canonical_name="Alarm A19 (Pressure Sensor Signal Invalid)",
                aliases=["A19", "Alarm A19", "Pressure Sensor Signal Invalid", "pressure_sensor_signal_invalid"],
                entity_type=EntityType.ALARM,
                status="Active",
                notes="Triggered by sensor wiring fault or drift beyond tolerance."
            ),
            Entity(
                id="TB-7",
                canonical_name="Terminal Block 7",
                aliases=["TB-7", "Terminal Block 7", "TB7"],
                entity_type=EntityType.COMPONENT,
                location="Control Cabinet 1",
                status="Active",
                notes="Corresponds to the PS-04A signal loop wiring junction."
            ),
            Entity(
                id="AUX_RESERVOIR",
                canonical_name="Auxiliary Reservoir",
                aliases=["Auxiliary Reservoir", "auxiliary reservoir"],
                entity_type=EntityType.SUBSYSTEM,
                location="Line 4/5 Specific",
                status="Active",
                notes="Tops up fluid during peak demand on Line 4/5. Documented in training slides and AEG-DWG-H01; absent from standard operator manual."
            ),
            Entity(
                id="Q1",
                canonical_name="Main Disconnect Q1",
                aliases=["Q1", "Main Disconnect", "Disconnect Q1"],
                entity_type=EntityType.COMPONENT,
                location="Control Cabinet 1",
                status="Active",
                notes="480V incoming electrical power disconnect."
            ),
            Entity(
                id="T1",
                canonical_name="Control Transformer T1",
                aliases=["T1", "Control Transformer", "Transformer T1", "CONTROL XFMR T1"],
                entity_type=EntityType.COMPONENT,
                location="Control Cabinet 1",
                status="Active",
                notes="Step-down control transformer (480:120V) for control cabinet and 24VDC power supply."
            )
        ]

        for ent in raw_definitions:
            self.entities[ent.id] = ent
            for alias in ent.aliases:
                self.alias_to_canonical[alias.lower()] = ent.id
                self.alias_to_canonical[self._normalize(alias)] = ent.id

        # Explicit non-merge justifications
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

    def resolve(self, label: str) -> Optional[Entity]:
        """Resolves any variant or alias string to the canonical Entity."""
        clean = label.strip()
        if clean in self.entities:
            return self.entities[clean]

        lower = clean.lower()
        if lower in self.alias_to_canonical:
            return self.entities[self.alias_to_canonical[lower]]

        norm = self._normalize(clean)
        if norm in self.alias_to_canonical:
            return self.entities[self.alias_to_canonical[norm]]

        # Substring / pattern matching
        for alias, cid in self.alias_to_canonical.items():
            if alias in lower or lower in alias:
                return self.entities[cid]

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

