"""
Fact Extraction Module
Transforms ingested source documents into structured, provenance-preserving Fact objects.
Distinguishes deterministic/rule-based table and config extraction from textual extraction.
"""

from typing import List, Dict, Any
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

        # Startup Interlocks
        interlocks = data.get("startup_interlocks", {})
        self.facts.append(Fact(
            id="FACT_CFG_STARTUP_INTERLOCKS",
            subject_id="HPU",
            predicate="startup_interlocks",
            object_value={
                "iv21_valve_state": interlocks.get("valve_iv21_required_state"),
                "estop_state": interlocks.get("estop_required_state"),
                "maintenance_panel_state": interlocks.get("maintenance_panel_required_state"),
                "fluid_level_band": interlocks.get("fluid_level_required_band")
            },
            trust_level=TrustLevel.ENGINEERING_BULLETIN,
            provenance=prov.model_copy(update={"section": "startup_interlocks", "verbatim_quote": str(interlocks)})
        ))

        # Sensor Setpoints
        sensors = data.get("sensors", {})
        self.facts.append(Fact(
            id="FACT_CFG_PS04A_THRESHOLD",
            subject_id="PS-04A",
            predicate="normal_operating_pressure",
            object_value=sensors.get("sensor_ps04a_threshold_bar"),
            unit="bar",
            version_scope=VersionScope(min_software_version="3.2", applies_to_notes="Applies from firmware 3.2"),
            trust_level=TrustLevel.ENGINEERING_BULLETIN,
            provenance=prov.model_copy(update={"section": "sensors", "verbatim_quote": f"sensor_ps04a_threshold_bar: {sensors.get('sensor_ps04a_threshold_bar')}"})
        ))

        self.facts.append(Fact(
            id="FACT_CFG_PS04A_ALARM_LOW",
            subject_id="PS-04A",
            predicate="alarm_low_threshold",
            object_value=sensors.get("sensor_ps04a_alarm_low_bar"),
            unit="bar",
            trust_level=TrustLevel.ENGINEERING_BULLETIN,
            provenance=prov.model_copy(update={"section": "sensors", "verbatim_quote": f"sensor_ps04a_alarm_low_bar: {sensors.get('sensor_ps04a_alarm_low_bar')}"})
        ))

        self.facts.append(Fact(
            id="FACT_CFG_PS40_ZONE",
            subject_id="PS-40",
            predicate="functional_zone",
            object_value=sensors.get("sensor_ps40_zone"),
            notes=sensors.get("sensor_ps40_note"),
            trust_level=TrustLevel.ENGINEERING_BULLETIN,
            provenance=prov.model_copy(update={"section": "sensors", "verbatim_quote": str(sensors.get("sensor_ps40_note"))})
        ))

        # Alarms
        a17_cfg = data.get("alarms", {}).get("A17", {})
        self.facts.append(Fact(
            id="FACT_CFG_A17_SHUTDOWN",
            subject_id="A17",
            predicate="persistence_shutdown_threshold",
            object_value=a17_cfg.get("persistence_before_shutdown_seconds"),
            unit="seconds",
            notes=f"Execute procedure {a17_cfg.get('shutdown_procedure_ref')}",
            trust_level=TrustLevel.ENGINEERING_BULLETIN,
            provenance=prov.model_copy(update={"section": "alarms.A17", "verbatim_quote": str(a17_cfg)})
        ))

        # Controller Reset Limit
        reset_cfg = data.get("controller_reset", {})
        self.facts.append(Fact(
            id="FACT_CFG_CONTROLLER_RESET_MAX",
            subject_id="PLC-03",
            predicate="max_pressure_allowed_for_reset",
            object_value=reset_cfg.get("max_pressure_bar_allowed_for_reset"),
            unit="bar",
            notes="Reset blocked in firmware above 50 bar",
            trust_level=TrustLevel.ENGINEERING_BULLETIN,
            provenance=prov.model_copy(update={"section": "controller_reset", "verbatim_quote": str(reset_cfg)})
        ))

        # Revision applicability
        rev_app = data.get("revision_applicability", {})
        legacy_val = rev_app.get("sensor_ps04_legacy_threshold_bar", {})
        self.facts.append(Fact(
            id="FACT_CFG_LEGACY_PS04_THRESHOLD",
            subject_id="PS-04",
            predicate="normal_operating_pressure",
            object_value=legacy_val.get("value"),
            unit="bar",
            version_scope=VersionScope(max_software_version="3.1", applies_to_notes="Applies before firmware 3.2"),
            status=FactStatus.SUPERSEDED,
            trust_level=TrustLevel.ENGINEERING_BULLETIN,
            provenance=prov.model_copy(update={"section": "revision_applicability", "verbatim_quote": str(legacy_val)})
        ))

    def _extract_from_bulletins(self, files: Dict[str, Any]):
        # ECN-1042
        rel_1042 = "engineering_bulletins/ECN-1042.pdf"
        if rel_1042 in files:
            prov = Provenance(
                document_id="ECN-1042",
                document_title="Engineering Change Notice ECN-1042",
                file_type="PDF",
                page=1,
                section="Section 1: Description of Change",
                trust_level=TrustLevel.ENGINEERING_BULLETIN,
                verbatim_quote="Effective software revision 3.2, pressure sensor PS-04 is replaced by pressure sensor PS-04A at the HPU discharge line... normal HPU discharge pressure setpoint is revised from 180 bar to 200 bar."
            )
            self.facts.append(Fact(
                id="FACT_ECN1042_REPLACEMENT",
                subject_id="PS-04A",
                predicate="supersedes_component",
                object_value="PS-04",
                version_scope=VersionScope(min_software_version="3.2"),
                notes="Introduced PS-04A to resolve 18-month signal drift. Not form-fit-function compatible with PS-04.",
                trust_level=TrustLevel.ENGINEERING_BULLETIN,
                provenance=prov
            ))
            self.facts.append(Fact(
                id="FACT_ECN1042_PRESSURE_SETPOINT",
                subject_id="HPU",
                predicate="normal_operating_pressure",
                object_value=200,
                unit="bar",
                version_scope=VersionScope(min_software_version="3.2", applies_to_notes="Series-7 units manufactured after 2024 / firmware >= 3.2"),
                notes="Deliberate process change to improve press cycle time.",
                trust_level=TrustLevel.ENGINEERING_BULLETIN,
                provenance=prov
            ))

        # ECN-1058
        rel_1058 = "engineering_bulletins/ECN-1058.pdf"
        if rel_1058 in files:
            prov = Provenance(
                document_id="ECN-1058",
                document_title="Engineering Change Notice ECN-1058",
                file_type="PDF",
                page=1,
                section="Section 1: Description of Change",
                trust_level=TrustLevel.ENGINEERING_BULLETIN,
                verbatim_quote="The Alarm Reference description for Alarm A17 referenced pre-ECN-1042 pressure sensor (PS-04)... This notice corrects that reference: Alarm A17 is evaluated against whichever pressure sensor is active for the installed software revision (PS-04 prior to 3.2, PS-04A on 3.2 and later)."
            )
            self.facts.append(Fact(
                id="FACT_ECN1058_A17_REFERENCE",
                subject_id="A17",
                predicate="active_sensor_evaluation_logic",
                object_value="Active sensor per installed software revision (PS-04 on <3.2, PS-04A on >=3.2)",
                notes="Documentation correction only. Approver name is NOT stated on ECN-1058 (status: Released).",
                trust_level=TrustLevel.ENGINEERING_BULLETIN,
                provenance=prov
            ))

    def _extract_from_operator_manual(self, files: Dict[str, Any]):
        rel = "manuals/operator_manual.pdf"
        if rel not in files:
            return
        prov_base = Provenance(
            document_id="AEG-OM-700-R4",
            document_title="Aegis Series-7 HCS Operator Manual (AEG-OM-700 Rev 4)",
            file_type="PDF",
            trust_level=TrustLevel.OFFICIAL_MANUAL
        )

        # Pre-conditions
        self.facts.append(Fact(
            id="FACT_OM_STARTUP_PRECONDITIONS",
            subject_id="HPU",
            predicate="startup_preconditions",
            object_value=[
                "Hydraulic fluid level is within normal band on sight glass",
                "Isolation valve IV-21 is OPEN",
                "Emergency stop circuit is RESET",
                "Maintenance access panel is INSTALLED and secured (closed)"
            ],
            provenance=prov_base.model_copy(update={
                "page": 1,
                "section": "Section 4.3 Starting the Hydraulic Power Unit",
                "verbatim_quote": "Before starting, verify: Hydraulic fluid level is within the normal band on the sight glass. Isolation valve IV-21 is OPEN. The emergency stop circuit is RESET. WARNING: Do not start the Hydraulic Power Unit with the maintenance access panel removed."
            })
        ))

        # Normal operating pressure
        self.facts.append(Fact(
            id="FACT_OM_OPERATING_PRESSURE_CURRENT",
            subject_id="HPU",
            predicate="normal_operating_pressure",
            object_value=200,
            unit="bar",
            version_scope=VersionScope(min_software_version="3.2", applies_to_notes="Applies to software revision 3.2 and later"),
            provenance=prov_base.model_copy(update={
                "page": 1,
                "section": "Section 4.3 & Section 5",
                "verbatim_quote": "Verify discharge pressure, as reported by PS-04A, reaches 200 bar. This is the normal operating pressure for software revision 3.2 and later"
            })
        ))

        # Legacy operating pressure mention
        self.facts.append(Fact(
            id="FACT_OM_OPERATING_PRESSURE_LEGACY",
            subject_id="HPU",
            predicate="normal_operating_pressure",
            object_value=180,
            unit="bar",
            version_scope=VersionScope(max_software_version="3.1", applies_to_notes="On revisions prior to 3.2"),
            status=FactStatus.SUPERSEDED,
            provenance=prov_base.model_copy(update={
                "page": 1,
                "section": "Section 5 Normal Operating Ranges",
                "verbatim_quote": "On revisions prior to 3.2, normal discharge pressure was 180 bar, measured by the original PS-04 sensor."
            })
        ))

        # Controller reset restriction
        self.facts.append(Fact(
            id="FACT_OM_CONTROLLER_RESET_RESTRICTION",
            subject_id="PLC-03",
            predicate="reset_restriction",
            object_value="Do not reset while hydraulic pressure is above 50 bar. Bleed pressure below 50 bar first.",
            notes="Resetting under pressure can cause uncommanded valve transition.",
            provenance=prov_base.model_copy(update={
                "page": 2,
                "section": "Section 7 Controller Reset",
                "verbatim_quote": "Do not reset the PLC-03 controller while hydraulic pressure is above 50 bar. Resetting the controller under pressure can cause an uncommanded valve transition."
            })
        ))

    def _extract_from_maintenance_manual(self, files: Dict[str, Any]):
        rel = "manuals/maintenance_manual.pdf"
        if rel not in files:
            return
        prov_base = Provenance(
            document_id="AEG-MM-700-R3",
            document_title="Aegis Series-7 HCS Maintenance Manual (AEG-MM-700 Rev 3)",
            file_type="PDF",
            page=1,
            trust_level=TrustLevel.OFFICIAL_MANUAL
        )

        # Alarm A17 Action (> 10 seconds)
        self.facts.append(Fact(
            id="FACT_MM_A17_ACTION_PERSISTENT",
            subject_id="A17",
            predicate="required_action_persistent",
            object_value="Execute Shutdown Procedure 4.7 if alarm A17 persists for more than 10 seconds.",
            notes="Shutdown Procedure 4.7: close IV-21, confirm pressure decay, set POWER selector to OFF, tag out per lockout/tagout procedure, proceed to Section 6 troubleshooting.",
            provenance=prov_base.model_copy(update={
                "section": "Section 4 Alarm A17 Response",
                "verbatim_quote": "If alarm A17 persists for more than 10 seconds, execute Shutdown Procedure 4.7 before investigating further. Do not attempt to clear a persistent A17 by silencing the alarm alone."
            })
        ))

        # Controller Reset Rationale
        self.facts.append(Fact(
            id="FACT_MM_CONTROLLER_RESET_MECHANISM",
            subject_id="PLC-03",
            predicate="reset_failure_mode",
            object_value="Re-initializes valve driver outputs; if pressurized, produces momentary uncommanded actuation of Isolation Valve IV-21.",
            provenance=prov_base.model_copy(update={
                "section": "Section 3 Controller Reset Conditions",
                "verbatim_quote": "The controller reset routine re-initializes valve driver outputs; if the circuit is still pressurized, this can produce a momentary uncommanded actuation of Isolation Valve IV-21."
            })
        ))

        # Troubleshooting causes
        self.facts.append(Fact(
            id="FACT_MM_A17_CAUSES",
            subject_id="A17",
            predicate="possible_causes",
            object_value=[
                "Isolation valve IV-21 is closed or partially closed",
                "Hydraulic fluid level is low",
                "Pressure sensor (PS-04 / PS-04A) signal is invalid or out of calibration"
            ],
            provenance=prov_base.model_copy(update={
                "section": "Section 6 Troubleshooting: Low Discharge Pressure",
                "verbatim_quote": "Check: Isolation valve IV-21 closed or partially closed; Hydraulic fluid level is low; Pressure sensor (PS-04 / PS-04A) signal invalid or out of calibration"
            })
        ))

    def _extract_from_alarm_reference(self, files: Dict[str, Any]):
        rel = "reference/alarm_reference.pdf"
        if rel not in files:
            return
        prov_base = Provenance(
            document_id="AEG-AL-700-R5",
            document_title="Aegis Alarm Reference (AEG-AL-700 Rev 5)",
            file_type="PDF",
            page=1,
            trust_level=TrustLevel.OFFICIAL_MANUAL
        )

        self.facts.append(Fact(
            id="FACT_ALARM_A17_DEFINITION",
            subject_id="A17",
            predicate="alarm_condition",
            object_value="Hydraulic pressure below 150 bar",
            notes="Panel indication: RED. Possible causes: IV-21 closed/partially closed; low hydraulic fluid; pressure sensor signal invalid.",
            provenance=prov_base.model_copy(update={
                "section": "Table Row 1",
                "verbatim_quote": "Alarm A17 | Hydraulic pressure below 150 bar | RED | 1. IV-21 closed or partially closed 2. Low hydraulic fluid 3. Pressure sensor signal invalid | See Section 4 Maintenance Manual. If persistent > 10 s, run Shutdown Proc. 4.7"
            })
        ))

        self.facts.append(Fact(
            id="FACT_ALARM_A18_DEFINITION",
            subject_id="A18",
            predicate="alarm_condition",
            object_value="Hydraulic pressure above 220 bar",
            notes="Panel indication: AMBER. Stop HPU immediately.",
            provenance=prov_base.model_copy(update={
                "section": "Table Row 2",
                "verbatim_quote": "Alarm A18 | Hydraulic pressure above 220 bar | AMBER"
            })
        ))

    def _extract_from_component_register(self, files: Dict[str, Any]):
        rel = "reference/component_register.xlsx"
        if rel not in files:
            return
        prov_base = Provenance(
            document_id="AEG-CR-700",
            document_title="Component Register (AEG-CR-700)",
            file_type="XLSX",
            section="Sheet1",
            trust_level=TrustLevel.OFFICIAL_MANUAL
        )

        # IV-21 Location
        self.facts.append(Fact(
            id="FACT_CR_IV21_LOCATION",
            subject_id="IV-21",
            predicate="location",
            object_value="Hydraulic Module",
            provenance=prov_base.model_copy(update={
                "element_id": "Row: IV-21",
                "verbatim_quote": "IV-21 | Isolation Valve 21 | Isolation Valve; IV21 | Hydraulic Module | Active | Must be OPEN prior to HPU startup."
            })
        ))

        # PS-04 vs PS-40
        self.facts.append(Fact(
            id="FACT_CR_PS40_LOCATION",
            subject_id="PS-40",
            predicate="location",
            object_value="Coolant Loop, Skid B",
            notes="NOT related to HPU discharge circuit. Do not confuse with PS-04 / PS-04A.",
            provenance=prov_base.model_copy(update={
                "element_id": "Row: PS-40",
                "verbatim_quote": "PS-40 | Pressure Sensor 40 | P40; PS40 | Coolant Loop, Skid B | Active | NOT related to the HPU discharge circuit. Do not confuse with PS-04 / PS-04A."
            })
        ))

        # Electrical disconnect Q1 & T1
        self.facts.append(Fact(
            id="FACT_CR_Q1_SPECS",
            subject_id="Q1",
            predicate="electrical_specification",
            object_value="480V incoming disconnect",
            provenance=prov_base.model_copy(update={
                "element_id": "Row: Q1",
                "verbatim_quote": "Q1 | Main Disconnect | — | Control Cabinet 1 | Active | 480V incoming disconnect."
            })
        ))

        self.facts.append(Fact(
            id="FACT_CR_T1_SPECS",
            subject_id="T1",
            predicate="electrical_specification",
            object_value="480:120V control power",
            provenance=prov_base.model_copy(update={
                "element_id": "Row: T1",
                "verbatim_quote": "T1 | Control Transformer | — | Control Cabinet 1 | Active | 480:120V control power."
            })
        ))

    def _extract_from_revision_history(self, files: Dict[str, Any]):
        rel = "reference/revision_history.xlsx"
        if rel not in files:
            return
        prov_base = Provenance(
            document_id="REV-HIST-700",
            document_title="Revision History (AEG-RH-700)",
            file_type="XLSX",
            section="Sheet1",
            trust_level=TrustLevel.ENGINEERING_BULLETIN
        )

        self.facts.append(Fact(
            id="FACT_RH_REV32_DETAILS",
            subject_id="PLC-03",
            predicate="software_revision_3.2",
            object_value={
                "release_date": "2025-09-30",
                "summary": "Pressure sensor PS-04 replaced by PS-04A. Normal HPU discharge pressure setpoint changed from 180 bar to 200 bar. See ECN-1042.",
                "related_documents": ["ECN-1042", "AEG-OM-700 Rev 3", "AEG-MM-700 Rev 2", "AEG-CR-700 Rev 2"]
            },
            provenance=prov_base.model_copy(update={
                "element_id": "Row: 3.2",
                "verbatim_quote": "3.2 | 2025-09-30 | Pressure sensor PS-04 replaced by PS-04A. Normal HPU discharge pressure setpoint changed from 180 bar to 200 bar. See ECN-1042. | ECN-1042, AEG-OM-700 Rev 3, AEG-MM-700 Rev 2, AEG-CR-700 Rev 2"
            })
        ))

    def _extract_from_legacy_manual(self, files: Dict[str, Any]):
        rel = "manuals/legacy_manual_v1.html"
        if rel not in files:
            return
        prov_base = Provenance(
            document_id="AEG-OM-700-R1",
            document_title="Operator Manual (v1, legacy export)",
            file_type="HTML",
            trust_level=TrustLevel.OFFICIAL_MANUAL
        )

        self.facts.append(Fact(
            id="FACT_LEGACY_OPERATING_PRESSURE",
            subject_id="HPU",
            predicate="normal_operating_pressure",
            object_value=180,
            unit="bar",
            version_scope=VersionScope(max_software_version="3.1", applies_to_notes="Applies to software revisions 3.0 and 3.1 only"),
            status=FactStatus.SUPERSEDED,
            notes="Superseded by software revision 3.2 per ECN-1042 and AEG-OM-700 Rev 4.",
            provenance=prov_base.model_copy(update={
                "section": "Section 5 Normal Operating Ranges",
                "verbatim_quote": "Normal HPU discharge pressure is 180 bar, as measured by pressure sensor PS-04."
            })
        ))

    def _extract_from_diagrams(self, files: Dict[str, Any]):
        # Hydraulic Schematic
        rel_hyd = "diagrams/system_diagram_hydraulic.pdf"
        if rel_hyd in files:
            prov = Provenance(
                document_id="AEG-DWG-H01",
                document_title="Hydraulic Schematic (AEG-DWG-H01)",
                file_type="PDF",
                page=1,
                section="Schematic Topology",
                trust_level=TrustLevel.OFFICIAL_MANUAL,
                verbatim_quote="purple lines: control/signal connections to PLC-03; grey lines: hydraulic fluid path; tan line: reservoir interconnect"
            )
            self.facts.append(Fact(
                id="FACT_HYD_SCHEMATIC_PLC_CONNECTIONS",
                subject_id="PLC-03",
                predicate="direct_controller_connections",
                object_value=["PS-04A", "HPU", "IV-21"],
                notes="According to the schematic, exactly three components have direct purple signal/control lines to PLC-03: PS-04A, Hydraulic Power Unit (HPU), and Isolation Valve IV-21. Reservoirs and Press Circuit do not connect directly to PLC-03.",
                provenance=prov
            ))

        # Electrical Schematic
        rel_elec = "diagrams/system_diagram_electrical.png"
        if rel_elec in files:
            prov = Provenance(
                document_id="AEG-DWG-E02",
                document_title="Electrical Schematic (AEG-DWG-E02)",
                file_type="PNG",
                section="Power distribution and interlock wiring",
                trust_level=TrustLevel.OFFICIAL_MANUAL,
                verbatim_quote="MAIN DISCONNECT Q1 -> CONTROL XFMR T1 480:120V -> PLC-03 24VDC POWER SUPPLY & PLC-03 I/O RACK"
            )
            self.facts.append(Fact(
                id="FACT_ELEC_POWER_VOLTAGE",
                subject_id="HPU",
                predicate="power_supply_compatibility",
                object_value="480V supply required via Q1 (480:120V transformer T1). 3-phase 400V is NOT compatible directly.",
                provenance=prov
            ))

    def _extract_from_training_slides(self, files: Dict[str, Any]):
        rel = "extra/training_slide_excerpt.pptx"
        if rel not in files:
            return
        prov = Provenance(
            document_id="TRN-HPU-01",
            document_title="HPU Basics Training Excerpt",
            file_type="PPTX",
            page=2,
            section="Slide 2",
            trust_level=TrustLevel.OFFICIAL_MANUAL,
            verbatim_quote="It pulls fluid from the main reservoir and, on most Line 4/5 configurations, tops up from a smaller Auxiliary Reservoir during peak demand... Note: 'Auxiliary Reservoir' is a Line 4/5-specific configuration detail and is not covered in the standard Operator Manual."
        )

        self.facts.append(Fact(
            id="FACT_TRN_AUX_RESERVOIR",
            subject_id="AUX_RESERVOIR",
            predicate="deck_novel_component",
            object_value="Auxiliary Reservoir",
            notes="Introduces Auxiliary Reservoir, which is not found in the standard Operator Manual. No novel alarms are introduced.",
            provenance=prov
        ))

    def _extract_from_calibration_record(self, files: Dict[str, Any]):
        rel = "scans/scanned_appendix_calibration.pdf"
        if rel not in files:
            return
        prov = Provenance(
            document_id="APP-C-CAL",
            document_title="APPENDIX C — SENSOR CALIBRATION RECORD",
            file_type="PDF (Scanned)",
            page=1,
            trust_level=TrustLevel.FIELD_RECORD_LOW_TRUST,
            verbatim_quote="Span reference target is 200 bar, consistent with the software revision 3.2 operating pressure setpoint. No calibration interval is specified for PS-04A on this form; recalibration frequency should be confirmed against applicable maintenance schedule, which is not included in this binder."
        )

        self.facts.append(Fact(
            id="FACT_CAL_PS04A_RECORD",
            subject_id="PS-04A",
            predicate="calibration_record",
            object_value={
                "technician": "R. Okafor",
                "calibration_date": "2026-01-09",
                "target_span_bar": 200.0,
                "reading_span_bar": 199.4,
                "calibration_interval": "Unspecified / Not included in binder"
            },
            provenance=prov
        ))

    def _extract_from_site_survey(self, files: Dict[str, Any]):
        rel = "low_trust/site_survey_notes.docx"
        if rel not in files:
            return
        prov = Provenance(
            document_id="SITE-NOTES-L4",
            document_title="Site Visit Notes — Line 4 HPU (J. Torres)",
            file_type="DOCX",
            trust_level=TrustLevel.FIELD_RECORD_LOW_TRUST,
            verbatim_quote="Checked the gauge on the local panel and it read about 175 bar during a normal run, not 180 like the manual says it should be. Could be the gauge is a little off, didn't have a calibrated reference on me."
        )

        self.facts.append(Fact(
            id="FACT_SITE_GAUGE_OBSERVATION",
            subject_id="HPU",
            predicate="observed_gauge_pressure",
            object_value=175,
            unit="bar",
            status=FactStatus.UNVERIFIED,
            notes="Uncalibrated field gauge observation by J. Torres. Does not reflect official setpoint.",
            provenance=prov
        ))

    def _extract_from_hmi_screens(self, files: Dict[str, Any]):
        # screen_03_diagnostics
        rel_diag = "screenshots/screen_03_diagnostics.png"
        if rel_diag in files:
            prov = Provenance(
                document_id="HMI-SCREEN-03",
                document_title="HMI Diagnostics Screen",
                file_type="PNG",
                trust_level=TrustLevel.OFFICIAL_MANUAL,
                verbatim_quote="Tag: P.S.04-A | Signal Type: 4-20 mA | Scaled Value: 200.3 bar | Note: this screen displays the sensor tag as printed on the physical unit label."
            )
            self.facts.append(Fact(
                id="FACT_HMI_DIAG_SENSOR_ID",
                subject_id="PS-04A",
                predicate="printed_unit_label_tag",
                object_value="P.S.04-A",
                notes="Matches PS-04A (Pressure Sensor 04A), the active HPU discharge pressure transducer.",
                provenance=prov
            ))

