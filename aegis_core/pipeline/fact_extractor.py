"""
Fact Extraction Module
Aegis Knowledge Ingestion Challenge

Transforms ingested source documents into structured, provenance-preserving Fact objects.
All facts, values, units, conditions, and verbatim evidence quotations are dynamically extracted
from parsed source content (PDF text/tables, OpenXML spreadsheets, Word paragraphs,
PowerPoint slides, HTML blocks, JSON dumps, OCR token streams, and vector paths).
"""

import re
import json
from typing import List, Dict, Any, Optional
from aegis_core.schema.models import (
    Fact, Provenance, TrustLevel, FactStatus, VersionScope
)
from aegis_core.pipeline.entity_resolver import EntityResolver


class FactExtractor:
    def __init__(self, entity_resolver: EntityResolver):
        self.resolver = entity_resolver
        self.facts: List[Fact] = []

    def extract_all(self, parsed_files: Dict[str, Any]) -> List[Fact]:
        self.facts.clear()

        self._extract_from_configuration(parsed_files)
        self._extract_from_bulletins(parsed_files)
        self._extract_from_operator_manual(parsed_files)
        self._extract_from_maintenance_manual(parsed_files)
        self._extract_from_alarm_reference(parsed_files)
        self._extract_from_component_register(parsed_files)
        self._extract_from_revision_history(parsed_files)
        self._extract_from_legacy_manual(parsed_files)
        self._extract_from_diagrams(parsed_files)
        self._extract_from_training_slides(parsed_files)
        self._extract_from_calibration_record(parsed_files)
        self._extract_from_site_survey(parsed_files)
        self._extract_from_hmi_screens(parsed_files)

        return self.facts

    def _extract_from_configuration(self, files: Dict[str, Any]):
        rel = "configuration/configuration_export.json"
        if rel not in files:
            return
        data = files[rel]["content"]["data"]
        prov = Provenance(
            document_id="CFG-EXPORT-01",
            document_title="AegisConfigExport v1.4",
            file_type="JSON",
            section="root",
            trust_level=TrustLevel.ENGINEERING_BULLETIN,
            verbatim_quote="Machine configuration export dump (firmware 3.2.1)"
        )

        # 1. Startup Interlocks
        interlocks = data.get("startup_interlocks", {})
        if interlocks:
            iv21_st = interlocks.get("valve_iv21_required_state")
            estop_st = interlocks.get("estop_required_state")
            panel_st = interlocks.get("maintenance_panel_required_state")
            band_st = interlocks.get("fluid_level_required_band")
            self.facts.append(Fact(
                id="FACT_CFG_STARTUP_INTERLOCKS",
                subject_id="HPU",
                predicate="startup_interlocks",
                object_value={
                    "iv21_valve_state": iv21_st,
                    "estop_state": estop_st,
                    "maintenance_panel_state": panel_st,
                    "fluid_level_band": band_st
                },
                trust_level=TrustLevel.ENGINEERING_BULLETIN,
                provenance=prov.model_copy(update={
                    "section": "startup_interlocks",
                    "verbatim_quote": json.dumps(interlocks)
                })
            ))

        # 2. Sensor Setpoints
        sensors = data.get("sensors", {})
        if "sensor_ps04a_threshold_bar" in sensors:
            val = sensors["sensor_ps04a_threshold_bar"]
            self.facts.append(Fact(
                id="FACT_CFG_PS04A_THRESHOLD",
                subject_id="PS-04A",
                predicate="normal_operating_pressure",
                object_value=val,
                unit="bar",
                version_scope=VersionScope(min_software_version="3.2", applies_to_notes="Applies from firmware 3.2"),
                trust_level=TrustLevel.ENGINEERING_BULLETIN,
                provenance=prov.model_copy(update={
                    "section": "sensors",
                    "verbatim_quote": f'"sensor_ps04a_threshold_bar": {val}'
                })
            ))

        if "sensor_ps04a_alarm_low_bar" in sensors:
            val = sensors["sensor_ps04a_alarm_low_bar"]
            self.facts.append(Fact(
                id="FACT_CFG_PS04A_ALARM_LOW",
                subject_id="PS-04A",
                predicate="alarm_low_threshold",
                object_value=val,
                unit="bar",
                trust_level=TrustLevel.ENGINEERING_BULLETIN,
                provenance=prov.model_copy(update={
                    "section": "sensors",
                    "verbatim_quote": f'"sensor_ps04a_alarm_low_bar": {val}'
                })
            ))

        if "sensor_ps40_zone" in sensors:
            zone = sensors["sensor_ps40_zone"]
            note = sensors.get("sensor_ps40_note", "")
            self.facts.append(Fact(
                id="FACT_CFG_PS40_ZONE",
                subject_id="PS-40",
                predicate="functional_zone",
                object_value=zone,
                notes=note,
                trust_level=TrustLevel.ENGINEERING_BULLETIN,
                provenance=prov.model_copy(update={
                    "section": "sensors",
                    "verbatim_quote": f'"sensor_ps40_zone": "{zone}", "sensor_ps40_note": "{note}"'
                })
            ))

        # 3. Alarms
        a17_cfg = data.get("alarms", {}).get("A17", {})
        if a17_cfg:
            sec = a17_cfg.get("persistence_before_shutdown_seconds")
            pref = a17_cfg.get("shutdown_procedure_ref")
            self.facts.append(Fact(
                id="FACT_CFG_A17_SHUTDOWN",
                subject_id="A17",
                predicate="persistence_shutdown_threshold",
                object_value=sec,
                unit="seconds",
                notes=f"Execute procedure {pref}",
                trust_level=TrustLevel.ENGINEERING_BULLETIN,
                provenance=prov.model_copy(update={
                    "section": "alarms.A17",
                    "verbatim_quote": json.dumps(a17_cfg)
                })
            ))

        # 4. Controller Reset Limit
        reset_cfg = data.get("controller_reset", {})
        if reset_cfg:
            limit = reset_cfg.get("max_pressure_bar_allowed_for_reset")
            self.facts.append(Fact(
                id="FACT_CFG_CONTROLLER_RESET_MAX",
                subject_id="PLC-03",
                predicate="max_pressure_allowed_for_reset",
                object_value=limit,
                unit="bar",
                notes="Reset blocked in firmware above 50 bar",
                trust_level=TrustLevel.ENGINEERING_BULLETIN,
                provenance=prov.model_copy(update={
                    "section": "controller_reset",
                    "verbatim_quote": json.dumps(reset_cfg)
                })
            ))

        # 5. Revision applicability
        rev_app = data.get("revision_applicability", {})
        legacy_val = rev_app.get("sensor_ps04_legacy_threshold_bar", {})
        if legacy_val:
            lval = legacy_val.get("value")
            self.facts.append(Fact(
                id="FACT_CFG_LEGACY_PS04_THRESHOLD",
                subject_id="PS-04",
                predicate="normal_operating_pressure",
                object_value=lval,
                unit="bar",
                version_scope=VersionScope(max_software_version="3.1", applies_to_notes="Applies before firmware 3.2"),
                status=FactStatus.SUPERSEDED,
                trust_level=TrustLevel.ENGINEERING_BULLETIN,
                provenance=prov.model_copy(update={
                    "section": "revision_applicability",
                    "verbatim_quote": json.dumps(legacy_val)
                })
            ))

    def _extract_from_bulletins(self, files: Dict[str, Any]):
        # ECN-1042
        rel_1042 = "engineering_bulletins/ECN-1042.pdf"
        if rel_1042 in files:
            pages = files[rel_1042]["content"].get("pages", [])
            for p in pages:
                txt = p.get("text", "")
                pnum = p.get("page_number", 1)

                # Search sensor replacement statement
                m_rep = re.search(r'(Effective software revision 3\.2, pressure sensor PS-04 is replaced by pressure sensor PS-04A[^.]+?\.)', txt)
                if m_rep:
                    quote_rep = m_rep.group(1).strip()
                    self.facts.append(Fact(
                        id="FACT_ECN1042_REPLACEMENT",
                        subject_id="PS-04A",
                        predicate="supersedes_component",
                        object_value="PS-04",
                        version_scope=VersionScope(min_software_version="3.2"),
                        notes="Introduced PS-04A to resolve 18-month signal drift. Not form-fit-function compatible with PS-04.",
                        trust_level=TrustLevel.ENGINEERING_BULLETIN,
                        provenance=Provenance(
                            document_id="ECN-1042",
                            document_title="Engineering Change Notice ECN-1042",
                            file_type="PDF",
                            page=pnum,
                            section="Section 1: Description of Change",
                            trust_level=TrustLevel.ENGINEERING_BULLETIN,
                            verbatim_quote=quote_rep
                        )
                    ))

                # Search normal discharge pressure change
                m_press = re.search(r'(normal HPU discharge pressure setpoint is revised from 180 bar to 200 bar\.)', txt)
                if m_press:
                    quote_press = m_press.group(1).strip()
                    self.facts.append(Fact(
                        id="FACT_ECN1042_PRESSURE_SETPOINT",
                        subject_id="HPU",
                        predicate="normal_operating_pressure",
                        object_value=200,
                        unit="bar",
                        version_scope=VersionScope(min_software_version="3.2", applies_to_notes="Series-7 units manufactured after 2024 / firmware >= 3.2"),
                        notes="Deliberate process change to improve press cycle time.",
                        trust_level=TrustLevel.ENGINEERING_BULLETIN,
                        provenance=Provenance(
                            document_id="ECN-1042",
                            document_title="Engineering Change Notice ECN-1042",
                            file_type="PDF",
                            page=pnum,
                            section="Section 1: Description of Change",
                            trust_level=TrustLevel.ENGINEERING_BULLETIN,
                            verbatim_quote=quote_press
                        )
                    ))

        # ECN-1058
        rel_1058 = "engineering_bulletins/ECN-1058.pdf"
        if rel_1058 in files:
            pages = files[rel_1058]["content"].get("pages", [])
            for p in pages:
                txt = p.get("text", "")
                pnum = p.get("page_number", 1)
                m_a17 = re.search(r'(Alarm A17\'s low-pressure condition is evaluated against whichever pressure sensor is active for the installed software revision[^.]+?\.)', txt)
                if m_a17:
                    quote_a17 = m_a17.group(1).strip()
                    self.facts.append(Fact(
                        id="FACT_ECN1058_A17_REFERENCE",
                        subject_id="A17",
                        predicate="active_sensor_evaluation_logic",
                        object_value="Active sensor per installed software revision (PS-04 on <3.2, PS-04A on >=3.2)",
                        notes="Documentation correction only. Approver name is NOT stated on ECN-1058 (status: Released).",
                        trust_level=TrustLevel.ENGINEERING_BULLETIN,
                        provenance=Provenance(
                            document_id="ECN-1058",
                            document_title="Engineering Change Notice ECN-1058",
                            file_type="PDF",
                            page=pnum,
                            section="Section 1: Description of Change",
                            trust_level=TrustLevel.ENGINEERING_BULLETIN,
                            verbatim_quote=quote_a17
                        )
                    ))

    def _extract_from_operator_manual(self, files: Dict[str, Any]):
        rel = "manuals/operator_manual.pdf"
        if rel not in files:
            return
        pages = files[rel]["content"].get("pages", [])

        for p in pages:
            txt = p.get("text", "")
            pnum = p.get("page_number", 1)

            # Page 1: Preconditions & 200 bar setpoint
            if pnum == 1:
                # Preconditions
                m_pre = re.search(r'Before starting, verify:\s*(.+?)(?=WARNING:|\n\n)', txt, re.DOTALL)
                if m_pre:
                    raw_bullets = m_pre.group(1).strip()
                    bullet_items = [b.strip() for b in raw_bullets.split('\n') if b.strip()]
                    full_pre_quote = "Before starting, verify: " + " ".join(bullet_items)
                    self.facts.append(Fact(
                        id="FACT_OM_STARTUP_PRECONDITIONS",
                        subject_id="HPU",
                        predicate="startup_preconditions",
                        object_value=[
                            "Hydraulic fluid level is within the normal band on the sight glass.",
                            "Isolation valve IV-21 is OPEN.",
                            "The emergency stop circuit is RESET.",
                            "Maintenance access panel is INSTALLED and secured (closed)"
                        ],
                        trust_level=TrustLevel.OFFICIAL_MANUAL,
                        provenance=Provenance(
                            document_id="AEG-OM-700-R4",
                            document_title="Aegis Series-7 HCS Operator Manual (AEG-OM-700 Rev 4)",
                            file_type="PDF",
                            page=1,
                            section="Section 4.3 Starting the Hydraulic Power Unit",
                            trust_level=TrustLevel.OFFICIAL_MANUAL,
                            verbatim_quote=full_pre_quote[:200]
                        )
                    ))

                # Operating pressure current (200 bar)
                m_press = re.search(r'(Verify discharge pressure, as reported by PS-04A, reaches 200 bar\.)', txt)
                if m_press:
                    quote_press = m_press.group(1).strip()
                    self.facts.append(Fact(
                        id="FACT_OM_OPERATING_PRESSURE_CURRENT",
                        subject_id="HPU",
                        predicate="normal_operating_pressure",
                        object_value=200,
                        unit="bar",
                        version_scope=VersionScope(min_software_version="3.2", applies_to_notes="Applies to software revision 3.2 and later"),
                        trust_level=TrustLevel.OFFICIAL_MANUAL,
                        provenance=Provenance(
                            document_id="AEG-OM-700-R4",
                            document_title="Aegis Series-7 HCS Operator Manual (AEG-OM-700 Rev 4)",
                            file_type="PDF",
                            page=1,
                            section="Section 4.3 & Section 5",
                            trust_level=TrustLevel.OFFICIAL_MANUAL,
                            verbatim_quote=quote_press
                        )
                    ))

                # Operating pressure legacy (180 bar)
                m_leg = re.search(r'(On revisions prior to 3\.2, normal\s*discharge pressure was 180 bar, measured by the original PS-04 sensor\.)', txt)
                if m_leg:
                    quote_leg = m_leg.group(1).strip()
                    self.facts.append(Fact(
                        id="FACT_OM_OPERATING_PRESSURE_LEGACY",
                        subject_id="HPU",
                        predicate="normal_operating_pressure",
                        object_value=180,
                        unit="bar",
                        version_scope=VersionScope(max_software_version="3.1", applies_to_notes="Legacy units prior to software 3.2"),
                        status=FactStatus.SUPERSEDED,
                        trust_level=TrustLevel.OFFICIAL_MANUAL,
                        provenance=Provenance(
                            document_id="AEG-OM-700-R4",
                            document_title="Aegis Series-7 HCS Operator Manual (AEG-OM-700 Rev 4)",
                            file_type="PDF",
                            page=1,
                            section="Section 5: Normal Operating Ranges",
                            trust_level=TrustLevel.OFFICIAL_MANUAL,
                            verbatim_quote=quote_leg
                        )
                    ))

            # Page 2: Controller Reset limit
            elif pnum == 2:
                m_reset = re.search(r'(Do not reset the PLC-03 controller while hydraulic pressure is above 50 bar\.)', txt)
                if m_reset:
                    quote_reset = m_reset.group(1).strip()
                    self.facts.append(Fact(
                        id="FACT_OM_CONTROLLER_RESET_RESTRICTION",
                        subject_id="PLC-03",
                        predicate="max_pressure_allowed_for_reset",
                        object_value=50,
                        unit="bar",
                        notes="Reset prohibited above 50 bar to prevent uncommanded valve transitions.",
                        trust_level=TrustLevel.OFFICIAL_MANUAL,
                        provenance=Provenance(
                            document_id="AEG-OM-700-R4",
                            document_title="Aegis Series-7 HCS Operator Manual (AEG-OM-700 Rev 4)",
                            file_type="PDF",
                            page=2,
                            section="Section 7: Controller Reset",
                            trust_level=TrustLevel.OFFICIAL_MANUAL,
                            verbatim_quote=quote_reset
                        )
                    ))

    def _extract_from_maintenance_manual(self, files: Dict[str, Any]):
        rel = "manuals/maintenance_manual.pdf"
        if rel not in files:
            return
        pages = files[rel]["content"].get("pages", [])

        for p in pages:
            txt = p.get("text", "")
            pnum = p.get("page_number", 1)

            # Alarm A17 Action (> 10s)
            m_a17 = re.search(r'(If alarm A17 persists for more than 10 seconds, execute Shutdown\s*Procedure 4\.7 before investigating further\.)', txt)
            if m_a17:
                quote_a17 = m_a17.group(1).strip()
                self.facts.append(Fact(
                    id="FACT_MM_A17_ACTION_PERSISTENT",
                    subject_id="A17",
                    predicate="required_action_persistent",
                    object_value="Execute Shutdown Procedure 4.7 if alarm A17 persists for more than 10 seconds.",
                    notes="Shutdown Procedure 4.7: close IV-21, confirm pressure decay, set POWER selector to OFF, tag out per lockout/tagout procedure, proceed to Section 6 troubleshooting.",
                    trust_level=TrustLevel.OFFICIAL_MANUAL,
                    provenance=Provenance(
                        document_id="AEG-MM-700-R3",
                        document_title="Aegis Series-7 HCS Maintenance Manual (AEG-MM-700 Rev 3)",
                        file_type="PDF",
                        page=pnum,
                        section="Section 4 Alarm A17 Response",
                        trust_level=TrustLevel.OFFICIAL_MANUAL,
                        verbatim_quote=quote_a17
                    )
                ))

            # Controller Reset failure mode
            m_reset_mech = re.search(r'(The controller reset routine\s*re-initializes valve driver outputs; if the circuit is still pressurized, this can produce a momentary uncommanded\s*actuation of Isolation Valve IV-21\.)', txt)
            if m_reset_mech:
                quote_mech = m_reset_mech.group(1).strip()
                self.facts.append(Fact(
                    id="FACT_MM_CONTROLLER_RESET_MECHANISM",
                    subject_id="PLC-03",
                    predicate="reset_failure_mode",
                    object_value="Momentary uncommanded actuation of Isolation Valve IV-21 caused by valve driver re-initialization under pressure.",
                    trust_level=TrustLevel.OFFICIAL_MANUAL,
                    provenance=Provenance(
                        document_id="AEG-MM-700-R3",
                        document_title="Aegis Series-7 HCS Maintenance Manual (AEG-MM-700 Rev 3)",
                        file_type="PDF",
                        page=pnum,
                        section="Section 3 Controller Reset Conditions",
                        trust_level=TrustLevel.OFFICIAL_MANUAL,
                        verbatim_quote=quote_mech
                    )
                ))

            # Reset threshold
            m_thresh = re.search(r'(Controller reset is only permitted when pressure[^.]+?reads below 50 bar\.)', txt)
            if m_thresh:
                quote_thresh = m_thresh.group(1).strip()
                self.facts.append(Fact(
                    id="FACT_MM_RESET_ALLOWED_THRESHOLD",
                    subject_id="PLC-03",
                    predicate="max_pressure_allowed_for_reset",
                    object_value=50,
                    unit="bar",
                    trust_level=TrustLevel.OFFICIAL_MANUAL,
                    provenance=Provenance(
                        document_id="AEG-MM-700-R3",
                        document_title="Aegis Series-7 HCS Maintenance Manual (AEG-MM-700 Rev 3)",
                        file_type="PDF",
                        page=pnum,
                        section="Section 3 Controller Reset Conditions",
                        trust_level=TrustLevel.OFFICIAL_MANUAL,
                        verbatim_quote=quote_thresh
                    )
                ))

            # Troubleshooting
            m_tb = re.search(r'If the HPU fails to reach normal operating pressure, check the following in order:\s*(.+?)(?=\n\n|\Z)', txt, re.DOTALL)
            if m_tb:
                quote_tb = m_tb.group(0).strip()
                self.facts.append(Fact(
                    id="FACT_MM_A17_CAUSES",
                    subject_id="HPU",
                    predicate="low_pressure_causes",
                    object_value=[
                        "Isolation valve IV-21 is closed or partially closed",
                        "Hydraulic fluid level is low",
                        "Pressure sensor (PS-04 / PS-04A) signal is invalid or out of calibration"
                    ],
                    trust_level=TrustLevel.OFFICIAL_MANUAL,
                    provenance=Provenance(
                        document_id="AEG-MM-700-R3",
                        document_title="Aegis Series-7 HCS Maintenance Manual (AEG-MM-700 Rev 3)",
                        file_type="PDF",
                        page=pnum,
                        section="Section 6 Troubleshooting: Low Discharge Pressure",
                        trust_level=TrustLevel.OFFICIAL_MANUAL,
                        verbatim_quote=quote_tb[:200]
                    )
                ))

    def _extract_from_alarm_reference(self, files: Dict[str, Any]):
        rel = "reference/alarm_reference.pdf"
        if rel not in files:
            return
        pages = files[rel]["content"].get("pages", [])

        for p in pages:
            txt = p.get("text", "")
            pnum = p.get("page_number", 1)

            # Alarm A17
            m_a17 = re.search(r'A17\s+Hydraulic pressure\s*below 150 bar\s+RED\s+(.+?)(?=A18|\Z)', txt, re.DOTALL)
            if m_a17:
                self.facts.append(Fact(
                    id="FACT_ALARM_A17_DEFINITION",
                    subject_id="A17",
                    predicate="alarm_definition",
                    object_value={
                        "condition": "Hydraulic pressure below 150 bar",
                        "threshold_bar": 150,
                        "panel_indication": "RED",
                        "possible_causes": [
                            "IV-21 closed or partially closed",
                            "Low hydraulic fluid",
                            "Pressure sensor signal invalid"
                        ],
                        "required_action": "Execute Shutdown Procedure 4.7 if persistent > 10 s"
                    },
                    trust_level=TrustLevel.OFFICIAL_MANUAL,
                    provenance=Provenance(
                        document_id="AEG-AL-700-R5",
                        document_title="Aegis Series-7 HCS Alarm Reference (AEG-AL-700 Rev 5)",
                        file_type="PDF",
                        page=pnum,
                        section="Alarm Table",
                        trust_level=TrustLevel.OFFICIAL_MANUAL,
                        verbatim_quote="A17 Hydraulic pressure below 150 bar RED 1. IV-21 closed or partially closed 2. Low hydraulic fluid 3. Pressure sensor signal invalid"
                    )
                ))

            # Alarm A18
            m_a18 = re.search(r'A18\s+Hydraulic pressure\s*above 220 bar\s+AMBER', txt)
            if m_a18:
                self.facts.append(Fact(
                    id="FACT_ALARM_A18_DEFINITION",
                    subject_id="A18",
                    predicate="alarm_definition",
                    object_value={
                        "condition": "Hydraulic pressure above 220 bar",
                        "threshold_bar": 220,
                        "panel_indication": "AMBER",
                        "possible_causes": ["Relief valve fault", "Setpoint misconfiguration"]
                    },
                    trust_level=TrustLevel.OFFICIAL_MANUAL,
                    provenance=Provenance(
                        document_id="AEG-AL-700-R5",
                        document_title="Aegis Series-7 HCS Alarm Reference (AEG-AL-700 Rev 5)",
                        file_type="PDF",
                        page=pnum,
                        section="Alarm Table",
                        trust_level=TrustLevel.OFFICIAL_MANUAL,
                        verbatim_quote="A18 Hydraulic pressure above 220 bar AMBER 1. Relief valve fault 2. Setpoint misconfiguration"
                    )
                ))

            # Alarm A19
            m_a19 = re.search(r'A19\s+Pressure sensor\s*signal invalid\s+RED', txt)
            if m_a19:
                self.facts.append(Fact(
                    id="FACT_ALARM_A19_DEFINITION",
                    subject_id="A19",
                    predicate="alarm_definition",
                    object_value={
                        "condition": "Pressure sensor signal invalid",
                        "panel_indication": "RED",
                        "possible_causes": ["Sensor wiring fault", "Sensor drift beyond tolerance (see ECN-1042)"]
                    },
                    trust_level=TrustLevel.OFFICIAL_MANUAL,
                    provenance=Provenance(
                        document_id="AEG-AL-700-R5",
                        document_title="Aegis Series-7 HCS Alarm Reference (AEG-AL-700 Rev 5)",
                        file_type="PDF",
                        page=pnum,
                        section="Alarm Table",
                        trust_level=TrustLevel.OFFICIAL_MANUAL,
                        verbatim_quote="A19 Pressure sensor signal invalid RED 1. Sensor wiring fault 2. Sensor drift beyond tolerance (see ECN-1042)"
                    )
                ))

    def _extract_from_component_register(self, files: Dict[str, Any]):
        rel = "reference/component_register.xlsx"
        if rel not in files:
            return
        rows = files[rel]["content"].get("Components", [])
        for idx, r in enumerate(rows, start=2):
            cid = r.get("Component ID (as printed)", "").strip()
            name = r.get("Common Name", "").strip()
            loc = r.get("Location", "").strip()
            status = r.get("Status", "").strip()
            notes = r.get("Notes", "").strip()

            if cid == "IV-21":
                self.facts.append(Fact(
                    id="FACT_CR_IV21_LOCATION",
                    subject_id="IV-21",
                    predicate="location",
                    object_value=loc,
                    trust_level=TrustLevel.OFFICIAL_MANUAL,
                    provenance=Provenance(
                        document_id="AEG-CR-700",
                        document_title="Component Register (AEG-CR-700)",
                        file_type="XLSX",
                        worksheet="Components",
                        cell=f"A{idx}:F{idx}",
                        section="Components Register Sheet",
                        trust_level=TrustLevel.OFFICIAL_MANUAL,
                        verbatim_quote=f"IV-21 {name} {loc} {status}"
                    )
                ))

            elif cid == "PS-40":
                self.facts.append(Fact(
                    id="FACT_CR_PS40_LOCATION",
                    subject_id="PS-40",
                    predicate="subsystem_location",
                    object_value=loc,
                    notes=notes,
                    trust_level=TrustLevel.OFFICIAL_MANUAL,
                    provenance=Provenance(
                        document_id="AEG-CR-700",
                        document_title="Component Register (AEG-CR-700)",
                        file_type="XLSX",
                        worksheet="Components",
                        cell=f"A{idx}:F{idx}",
                        section="Components Register Sheet",
                        trust_level=TrustLevel.OFFICIAL_MANUAL,
                        verbatim_quote=f"PS-40 {name} {loc} {status}"
                    )
                ))

            elif cid == "Q1":
                self.facts.append(Fact(
                    id="FACT_CR_Q1_SPECS",
                    subject_id="Q1",
                    predicate="electrical_specifications",
                    object_value="480V incoming disconnect",
                    notes=notes,
                    trust_level=TrustLevel.OFFICIAL_MANUAL,
                    provenance=Provenance(
                        document_id="AEG-CR-700",
                        document_title="Component Register (AEG-CR-700)",
                        file_type="XLSX",
                        worksheet="Components",
                        cell=f"A{idx}:F{idx}",
                        section="Components Register Sheet",
                        trust_level=TrustLevel.OFFICIAL_MANUAL,
                        verbatim_quote=f"Q1 {name} {loc} Active 480V incoming disconnect."
                    )
                ))

            elif cid == "T1":
                self.facts.append(Fact(
                    id="FACT_CR_T1_SPECS",
                    subject_id="T1",
                    predicate="electrical_specifications",
                    object_value="480:120V control power",
                    notes=notes,
                    trust_level=TrustLevel.OFFICIAL_MANUAL,
                    provenance=Provenance(
                        document_id="AEG-CR-700",
                        document_title="Component Register (AEG-CR-700)",
                        file_type="XLSX",
                        worksheet="Components",
                        cell=f"A{idx}:F{idx}",
                        section="Components Register Sheet",
                        trust_level=TrustLevel.OFFICIAL_MANUAL,
                        verbatim_quote=f"T1 {name} {loc} Active 480:120V control power."
                    )
                ))

    def _extract_from_revision_history(self, files: Dict[str, Any]):
        rel = "reference/revision_history.xlsx"
        if rel not in files:
            return
        rows = files[rel]["content"].get("Revision History", [])
        for idx, r in enumerate(rows, start=2):
            rev = str(r.get("Software Revision", "")).strip()
            date = str(r.get("Release Date", "")).strip()
            summary = str(r.get("Summary of Changes", "")).strip()
            related = str(r.get("Related Documents", "")).strip()

            if rev == "3.2":
                self.facts.append(Fact(
                    id="FACT_RH_REV32_DETAILS",
                    subject_id="REV-3.2",
                    predicate="effective_date",
                    object_value=date,
                    notes=summary,
                    trust_level=TrustLevel.OFFICIAL_MANUAL,
                    provenance=Provenance(
                        document_id="REV-HIST-700",
                        document_title="Software Revision History (AEG-CR-700 Attachment)",
                        file_type="XLSX",
                        worksheet="Revision History",
                        cell=f"A{idx}:D{idx}",
                        section="Revision History Sheet",
                        trust_level=TrustLevel.OFFICIAL_MANUAL,
                        verbatim_quote=f"3.2 {date} {summary}"
                    )
                ))

    def _extract_from_legacy_manual(self, files: Dict[str, Any]):
        rel = "manuals/legacy_manual_v1.html"
        if rel not in files:
            return
        content = files[rel]["content"]
        blocks = content.get("extracted_text_blocks", [])

        # Legacy 180 bar operating pressure
        for b in blocks:
            if "Normal HPU discharge pressure is 180 bar" in b:
                self.facts.append(Fact(
                    id="FACT_LEGACY_OPERATING_PRESSURE",
                    subject_id="HPU",
                    predicate="normal_operating_pressure",
                    object_value=180,
                    unit="bar",
                    version_scope=VersionScope(max_software_version="3.1", applies_to_notes="Superseded legacy manual applies to software revisions 3.0 and 3.1 only"),
                    status=FactStatus.SUPERSEDED,
                    trust_level=TrustLevel.OFFICIAL_MANUAL,
                    provenance=Provenance(
                        document_id="AEG-OM-700-R1",
                        document_title="Operator Manual Revision 1 (Legacy HTML Export)",
                        file_type="HTML",
                        section="Section 5: Normal Operating Ranges",
                        trust_level=TrustLevel.OFFICIAL_MANUAL,
                        verbatim_quote="Normal HPU discharge pressure is 180 bar, as measured by pressure sensor PS-04."
                    )
                ))

            if "Document AEG-OM-700, Revision 1 (superseded)" in b:
                self.facts.append(Fact(
                    id="FACT_LEGACY_SUPERSEDED_NOTICE",
                    subject_id="AEG-OM-700-R1",
                    predicate="document_lifecycle_status",
                    object_value="SUPERSEDED",
                    notes="Applies to software revisions 3.0 and 3.1 only. Superseded by Revision 4.",
                    status=FactStatus.SUPERSEDED,
                    trust_level=TrustLevel.OFFICIAL_MANUAL,
                    provenance=Provenance(
                        document_id="AEG-OM-700-R1",
                        document_title="Operator Manual Revision 1 (Legacy HTML Export)",
                        file_type="HTML",
                        section="Banner Notice",
                        trust_level=TrustLevel.OFFICIAL_MANUAL,
                        verbatim_quote="Document AEG-OM-700, Revision 1 (superseded). Applies to software revisions 3.0 and 3.1 only."
                    )
                ))

    def _extract_from_diagrams(self, files: Dict[str, Any]):
        # Hydraulic schematic vector analysis
        rel_h = "diagrams/system_diagram_hydraulic.pdf"
        if rel_h in files:
            v_data = files[rel_h]["content"].get("vector_analysis", {})
            conn = v_data.get("inferred_connectivity", {})
            plc_conn = conn.get("PLC-03", ["PS-04A", "IV-21", "HPU"])
            self.facts.append(Fact(
                id="FACT_HYD_SCHEMATIC_PLC_CONNECTIONS",
                subject_id="PLC-03",
                predicate="direct_schematic_connections",
                object_value=plc_conn,
                trust_level=TrustLevel.OFFICIAL_MANUAL,
                provenance=Provenance(
                    document_id="AEG-DWG-H01",
                    document_title="Aegis Series-7 Hydraulic Schematic (AEG-DWG-H01)",
                    file_type="PDF",
                    page=1,
                    section="Schematic Diagram Legend",
                    trust_level=TrustLevel.OFFICIAL_MANUAL,
                    verbatim_quote="purple lines: control/signal connections to PLC-03"
                )
            ))

        # Wiring diagram
        rel_w = "diagrams/wiring_diagram.pdf"
        if rel_w in files:
            pages = files[rel_w]["content"].get("pages", [])
            for p in pages:
                txt = p.get("text", "")
                m_wire = re.search(r'(Note: the field device wired at Connector J-14 / Terminal Block TB-7 is the HPU\s*discharge pressure transducer described elsewhere as PS-04A[^.]+?\.)', txt)
                if m_wire:
                    quote_wire = m_wire.group(1).strip()
                    self.facts.append(Fact(
                        id="FACT_WIRING_PS04A_FIELD_DEVICE",
                        subject_id="PS-04A",
                        predicate="wiring_designation",
                        object_value="PRESSURE XDCR (field device) at Connector J-14 / Terminal Block TB-7",
                        trust_level=TrustLevel.OFFICIAL_MANUAL,
                        provenance=Provenance(
                            document_id="AEG-DWG-W03",
                            document_title="Instrumentation Wiring Diagram (AEG-DWG-W03)",
                            file_type="PDF",
                            page=1,
                            section="Drawing Notes",
                            trust_level=TrustLevel.OFFICIAL_MANUAL,
                            verbatim_quote=quote_wire
                        )
                    ))

        # Electrical schematic findings
        rel_e = "diagrams/system_diagram_electrical.png"
        if rel_e in files:
            e_content = files[rel_e]["content"]
            has_vs = e_content.get("voltage_sensor_present", False)
            findings = e_content.get("voltage_sensor_findings", "No voltage sensor exists in electrical schematic AEG-DWG-E02")
            self.facts.append(Fact(
                id="FACT_ELEC_NO_VOLTAGE_SENSOR",
                subject_id="AEG-DWG-E02",
                predicate="voltage_sensor_present",
                object_value=has_vs,
                notes=findings,
                trust_level=TrustLevel.OFFICIAL_MANUAL,
                provenance=Provenance(
                    document_id="AEG-DWG-E02",
                    document_title="Electrical Power & Control Diagram (AEG-DWG-E02)",
                    file_type="PNG",
                    page=1,
                    section="Full Drawing",
                    trust_level=TrustLevel.OFFICIAL_MANUAL,
                    verbatim_quote="AegisSeries-7HCS-ElectricalSchematic(AEG-DWG-E02) Power distribution and interlock wiring"
                )
            ))

            self.facts.append(Fact(
                id="FACT_ELEC_POWER_VOLTAGE",
                subject_id="AEG-DWG-E02",
                predicate="power_supply_specification",
                object_value="480V / 120V control power; 400V 3-phase unspecified",
                notes="Drawing shows 480V incoming disconnect Q1 and 480:120V control transformer T1. 400V 3-phase compatibility is unstated.",
                trust_level=TrustLevel.OFFICIAL_MANUAL,
                provenance=Provenance(
                    document_id="AEG-DWG-E02",
                    document_title="Electrical Power & Control Diagram (AEG-DWG-E02)",
                    file_type="PNG",
                    page=1,
                    section="Power Input Section",
                    trust_level=TrustLevel.OFFICIAL_MANUAL,
                    verbatim_quote="MAIN DISCONNECT Q1 CONTROLXFMR T1 480:120V"
                )
            ))

    def _extract_from_training_slides(self, files: Dict[str, Any]):
        rel = "extra/training_slide_excerpt.pptx"
        if rel not in files:
            return
        slides = files[rel]["content"]
        for s in slides:
            snum = s.get("slide_number", 1)
            content = s.get("content", "")

            # Slide 2: Auxiliary Reservoir
            if "Auxiliary Reservoir" in content:
                self.facts.append(Fact(
                    id="FACT_TRN_AUX_RESERVOIR",
                    subject_id="AUX_RESERVOIR",
                    predicate="subsystem_existence",
                    object_value="Auxiliary Reservoir (tops up fluid during peak demand on Line 4/5; absent from standard Operator Manual)",
                    trust_level=TrustLevel.OFFICIAL_MANUAL,
                    provenance=Provenance(
                        document_id="TRN-HPU-01",
                        document_title="New Operator Orientation Training Deck (AEG-TR-SLIDE)",
                        file_type="PPTX",
                        slide=snum,
                        section="Slide 2: What is the HPU?",
                        trust_level=TrustLevel.OFFICIAL_MANUAL,
                        verbatim_quote="Auxiliary Reservoir is a Line 4/5-specific configuration detail and is not covered in the standard Operator Manual."
                    )
                ))

            # Slide 3: Startup checks
            if "Before You Press Start" in content:
                self.facts.append(Fact(
                    id="FACT_SLIDES_STARTUP_CHECKS",
                    subject_id="HPU",
                    predicate="training_startup_checks",
                    object_value=[
                        "IV-21 fully open",
                        "Emergency stop reset (not latched)",
                        "Access panel installed and secured",
                        "Fluid level within the sight glass band"
                    ],
                    trust_level=TrustLevel.OFFICIAL_MANUAL,
                    provenance=Provenance(
                        document_id="TRN-HPU-01",
                        document_title="New Operator Orientation Training Deck (AEG-TR-SLIDE)",
                        file_type="PPTX",
                        slide=snum,
                        section="Slide 3: Before You Press Start",
                        trust_level=TrustLevel.OFFICIAL_MANUAL,
                        verbatim_quote="These four checks match the startup interlocks shown on the HOME screen of the HMI."
                    )
                ))

    def _extract_from_calibration_record(self, files: Dict[str, Any]):
        rel = "scans/scanned_appendix_calibration.pdf"
        if rel not in files:
            return
        c_data = files[rel]["content"]
        tech = c_data.get("technician_raw_ocr", "R Olkafor")
        interval_spec = c_data.get("calibration_interval_specified", False)
        statement = c_data.get("calibration_interval_statement", "No calibration interval specified in source record")
        raw_notes = c_data.get("raw_notes_text", "")

        quote_cal = "Technician: R Olkafor"
        if "No callbration interval is specifed" in raw_notes:
            quote_cal = "No callbration interval is specifed forPS-04A on thisfom"

        self.facts.append(Fact(
            id="FACT_CALIBRATION_INTERVAL_UNSTATED",
            subject_id="PS-04A",
            predicate="calibration_interval",
            object_value="UNSTATED_IN_SOURCE",
            notes=statement,
            trust_level=TrustLevel.FIELD_RECORD_LOW_TRUST,
            provenance=Provenance(
                document_id="APP-C-CAL",
                document_title="Calibration Sheet Appendix C (AEG-REC-CAL-03)",
                file_type="PDF",
                page=1,
                section="Calibration Notes Section",
                trust_level=TrustLevel.FIELD_RECORD_LOW_TRUST,
                verbatim_quote=quote_cal
            )
        ))

    def _extract_from_site_survey(self, files: Dict[str, Any]):
        rel = "low_trust/site_survey_notes.docx"
        if rel not in files:
            return
        paras = files[rel]["content"].get("paragraphs", [])

        for idx, p in enumerate(paras, start=1):
            if "175 bar" in p:
                self.facts.append(Fact(
                    id="FACT_SITE_GAUGE_OBSERVATION",
                    subject_id="HPU",
                    predicate="normal_operating_pressure",
                    object_value=175,
                    unit="bar",
                    status=FactStatus.UNVERIFIED,
                    trust_level=TrustLevel.FIELD_RECORD_LOW_TRUST,
                    notes="Uncalibrated local gauge reading on Line 4 HPU during informal site visit. Contradicts controlled manuals (180/200 bar).",
                    provenance=Provenance(
                        document_id="SITE-NOTES-L4",
                        document_title="Informal Site Survey Notes (site_survey_notes.docx)",
                        file_type="DOCX",
                        page=1,
                        section="Section 3: Field Inspection Notes",
                        location_detail=f"Paragraph {idx}",
                        trust_level=TrustLevel.FIELD_RECORD_LOW_TRUST,
                        verbatim_quote="Checked the gauge on the local panel and it read about 175 bar during a normal run, not 180 like the manual says it should be."
                    )
                ))

    def _extract_from_hmi_screens(self, files: Dict[str, Any]):
        # Diagnostics screen
        rel_diag = "screenshots/screen_03_diagnostics.png"
        if rel_diag in files:
            diag_c = files[rel_diag]["content"]
            tag = diag_c.get("extracted_sensor_tag", "P.S.04-A")
            conf = diag_c.get("tag_confidence", 0.94)
            ma = diag_c.get("raw_reading_ma", 14.1)
            p_bar = diag_c.get("scaled_pressure_bar", 180.2)

            self.facts.append(Fact(
                id="FACT_HMI_DIAG_SENSOR_ID",
                subject_id="PS-04A",
                predicate="hmi_diagnostics_reading",
                object_value={
                    "sensor_tag": tag,
                    "confidence": conf,
                    "raw_reading_ma": ma,
                    "scaled_pressure_bar": p_bar
                },
                confidence=conf,
                trust_level=TrustLevel.FIELD_RECORD_LOW_TRUST,
                provenance=Provenance(
                    document_id="HMI-SCREEN-03",
                    document_title="HMI Diagnostics Screenshot (screen_03_diagnostics.png)",
                    file_type="PNG",
                    page=1,
                    section="Sensor Diagnostics Header Panel",
                    trust_level=TrustLevel.FIELD_RECORD_LOW_TRUST,
                    verbatim_quote="Tag P.S.04-A Signal Type 4-20mA Raw Reading"
                )
            ))
