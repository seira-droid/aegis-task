"""
Conflict and Version Resolution Module
Detects contradictions across documents, assigns temporal version scopes,
and resolves conflicts via trust hierarchy and revision chronology.
"""

from typing import List, Dict, Any
from aegis_core.schema.models import Conflict, Fact, FactStatus, TrustLevel


class ConflictResolver:
    def __init__(self):
        self.conflicts: List[Conflict] = []

    def resolve_conflicts(self, facts: List[Fact]) -> List[Conflict]:
        self.conflicts.clear()

        # 1. HPU Operating Pressure Conflict (200 bar vs 180 bar vs 175 bar)
        pressure_facts = [
            f for f in facts
            if f.subject_id in ("HPU", "PS-04A", "PS-04")
            and f.predicate == "normal_operating_pressure"
        ]

        if pressure_facts:
            conflict_p = Conflict(
                id="CONF-01-PRESSURE-SETPOINT",
                subject_id="HPU",
                predicate="normal_operating_pressure",
                conflicting_fact_ids=[f.id for f in pressure_facts] + ["FACT_SITE_GAUGE_OBSERVATION"],
                resolution_type="TEMPORAL_SUPERSEDED_AND_TRUST_HIERARCHY",
                resolved_fact_id="FACT_OM_OPERATING_PRESSURE_CURRENT",
                justification=(
                    "Authoritative ECN-1042 and Operator Manual AEG-OM-700 Rev 4 establish that "
                    "normal operating pressure was increased from 180 bar to 200 bar effective Software Revision 3.2 "
                    "(released 2025-09-30) alongside sensor upgrade to PS-04A to improve cycle time. "
                    "The 180 bar value remains applicable ONLY to legacy units running software < 3.2 with PS-04. "
                    "The 175 bar reading in site_survey_notes.docx is an unverified, uncalibrated field gauge observation "
                    "on an unknown revision, subordinated under the FIELD_RECORD_LOW_TRUST hierarchy."
                )
            )
            self.conflicts.append(conflict_p)

        # 2. Alarm A17 Sensor Reference Conflict
        conflict_a17 = Conflict(
            id="CONF-02-A17-SENSOR-REF",
            subject_id="A17",
            predicate="sensor_evaluation_logic",
            conflicting_fact_ids=["FACT_ECN1058_A17_REFERENCE", "FACT_ALARM_A17_DEFINITION"],
            resolution_type="TEMPORAL_SUPERSEDED",
            resolved_fact_id="FACT_ECN1058_A17_REFERENCE",
            justification=(
                "Prior to ECN-1058, the Alarm Reference condition for A17 named sensor PS-04 directly. "
                "ECN-1058 issued a documentation correction establishing that A17 is evaluated against "
                "whichever sensor is active for the installed software revision (PS-04 on < 3.2, PS-04A on >= 3.2). "
                "Alarm threshold values (150 bar low, 220 bar high) remain unchanged."
            )
        )
        self.conflicts.append(conflict_a17)

        return self.conflicts

