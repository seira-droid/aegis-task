# Aegis Knowledge Ingestion Challenge — Evaluation Results

**Primary Questions Evaluated:** 23
**Primary Answer Accuracy:** 100.0%
**Provenance Recall:** 96.15%
**Epistemic Calibration Score:** 100.0%
**Gap Detection Recall:** 100.0%
**Hallucination Rate:** 0.0%

**Held-out Generalization Suite:** 10 rephrased queries
**Held-out Generalization Accuracy:** 100.0%

## Primary Evaluation Scorecard (23 Questions)

| # | Question | Epistemic Status | Result | Sources Cited |
|---|---|---|:---:|---|
| 1 | What must be true before starting the Hydraulic Power Unit? | `DEFINITIVE` | PASS | CFG-EXPORT-01, AEG-OM-700-R4 |
| 2 | What is the current normal operating pressure for the HPU, and... | `VERSION_SCOPED` | PASS | ECN-1042, AEG-OM-700-R4, CFG-EXPORT-01 |
| 3 | What does alarm A17 indicate, and what are its possible causes? | `DEFINITIVE` | PASS | AEG-MM-700-R3, AEG-AL-700-R5 |
| 4 | Is PS-04 the same component as PS-04A? | `DEFINITIVE` | PASS | ECN-1042 |
| 5 | Which document introduced the change from PS-04 to PS-04A? | `DEFINITIVE` | PASS | ECN-1042, REV-HIST-700 |
| 6 | Which components connect directly to the HCS controller, accor... | `DEFINITIVE` | PASS | AEG-DWG-H01 |
| 7 | What action is required if alarm A17 persists for more than 10... | `DEFINITIVE` | PASS | AEG-MM-700-R3, CFG-EXPORT-01 |
| 8 | Under what circumstances must the controller not be reset? | `DEFINITIVE` | PASS | AEG-MM-700-R3, CFG-EXPORT-01, AEG-OM-700-R4 |
| 9 | What was the operating pressure threshold before software revi... | `DEFINITIVE` | PASS | ECN-1042, AEG-OM-700-R4 |
| 10 | Which alarm is associated with a pressure sensor reading below... | `DEFINITIVE` | PASS | AEG-AL-700-R5 |
| 11 | According to the component register, what is the location of t... | `DEFINITIVE` | PASS | AEG-CR-700 |
| 12 | Does the training slide deck introduce any component or alarm ... | `DEFINITIVE` | PASS | TRN-HPU-01 |
| 13 | What sensor ID appears on the diagnostics screenshot, and does... | `DEFINITIVE` | PASS | HMI-SCREEN-03 |
| 14 | Per the revision history, when did software revision 3.2 take ... | `DEFINITIVE` | PASS | REV-HIST-700 |
| 15 | What does sensor_ps04a_threshold_bar in the configuration expo... | `DEFINITIVE` | PASS | CFG-EXPORT-01, AEG-OM-700-R4 |
| 16 | Does the 200 bar threshold apply to all Aegis HCS units, or on... | `VERSION_SCOPED` | PASS | ECN-1042, AEG-OM-700-R4 |
| 17 | Is PS-04 the same as PS-40? | `DEFINITIVE` | PASS | CFG-EXPORT-01, AEG-CR-700 |
| 18 | What was the pressure limit before revision 3.2? | `DEFINITIVE` | PASS | ECN-1042, AEG-OM-700-R4 |
| 19 | What is the maximum continuous operating temperature of PS-04A? | `UNANSWERABLE_GAP` | PASS | *None (Epistemic Gap)* |
| 20 | What is the calibration interval for the electrical system dia... | `FALSE_PREMISE` | PASS | *None (Epistemic Gap)* |
| 21 | Who approved engineering bulletin ECN-1058? | `UNANSWERABLE_GAP` | PASS | *None (Epistemic Gap)* |
| 22 | What is the mean time between failures for the isolation valve... | `UNANSWERABLE_GAP` | PASS | *None (Epistemic Gap)* |
| 23 | Is the Aegis Series-7 HCS compatible with a 3-phase 400V supply? | `UNANSWERABLE_GAP` | PASS | AEG-DWG-E02, AEG-CR-700 |

## Detailed Question Breakdown

### Question 1: What must be true before starting the Hydraulic Power Unit?
- **Epistemic Classification:** `DEFINITIVE`
- **Direct Answer:**
> Before starting the Hydraulic Power Unit (HPU), four conditions must be verified:
> 1. Hydraulic fluid level is within the normal band on the sight glass.
> 2. Isolation valve IV-21 is OPEN.
> 3. Emergency stop circuit is RESET.
> 4. Maintenance access panel is INSTALLED and secured (closed) — operating with the panel removed is prohibited due to exposed rotating components.
- **Verified Claims:**
  * Hydraulic fluid level must be within the normal band on the sight glass. (Supported by: `FACT_OM_STARTUP_PRECONDITIONS, FACT_CFG_STARTUP_INTERLOCKS`)
  * Isolation valve IV-21 must be OPEN. (Supported by: `FACT_OM_STARTUP_PRECONDITIONS, FACT_CFG_STARTUP_INTERLOCKS`)
  * Emergency stop circuit must be RESET. (Supported by: `FACT_OM_STARTUP_PRECONDITIONS, FACT_CFG_STARTUP_INTERLOCKS`)
  * Maintenance access panel must be INSTALLED and secured (closed). (Supported by: `FACT_OM_STARTUP_PRECONDITIONS, FACT_CFG_STARTUP_INTERLOCKS`)
- **Provenance Citations:**
  * **[AEG-OM-700-R4]** *Aegis Series-7 HCS Operator Manual (AEG-OM-700 Rev 4)* (p.1) — Quote: "Before starting, verify: Hydraulic fluid level is within the normal band on the sight glass. Isolation valve IV-21 is OPEN. The emergency stop circuit is RESET. WARNING: Do not start the Hydraulic Power Unit with the maintenance access panel removed."
  * **[CFG-EXPORT-01]** *AegisConfigExport v1.4* (startup_interlocks) — Quote: "{'valve_iv21_required_state': 'OPEN', 'estop_required_state': 'RESET', 'maintenance_panel_required_state': 'CLOSED', 'fluid_level_required_band': 'NORMAL'}"

### Question 2: What is the current normal operating pressure for the HPU, and under what conditions does that apply?
- **Epistemic Classification:** `VERSION_SCOPED`
- **Direct Answer:**
> The current normal operating pressure for the HPU is 200 bar. This setpoint applies to units running software revision 3.2 and later (with pressure sensor PS-04A installed, typically units manufactured after 2024 per ECN-1042). On units running software revisions prior to 3.2, normal discharge pressure was 180 bar, measured by sensor PS-04.
- **Verified Claims:**
  * Current normal operating pressure is 200 bar. (Supported by: `FACT_OM_OPERATING_PRESSURE_CURRENT, FACT_ECN1042_PRESSURE_SETPOINT, FACT_CFG_PS04A_THRESHOLD`)
  * Applies to units on software revision 3.2 and later with sensor PS-04A. (Supported by: `FACT_OM_OPERATING_PRESSURE_CURRENT, FACT_ECN1042_PRESSURE_SETPOINT`)
  * Legacy units prior to revision 3.2 operate at 180 bar with PS-04. (Supported by: `FACT_OM_OPERATING_PRESSURE_LEGACY`)
- **Provenance Citations:**
  * **[AEG-OM-700-R4]** *Aegis Series-7 HCS Operator Manual (AEG-OM-700 Rev 4)* (p.1) — Quote: "Verify discharge pressure, as reported by PS-04A, reaches 200 bar. This is the normal operating pressure for software revision 3.2 and later"
  * **[ECN-1042]** *Engineering Change Notice ECN-1042* (p.1) — Quote: "Effective software revision 3.2, pressure sensor PS-04 is replaced by pressure sensor PS-04A at the HPU discharge line... normal HPU discharge pressure setpoint is revised from 180 bar to 200 bar."
  * **[AEG-OM-700-R4]** *Aegis Series-7 HCS Operator Manual (AEG-OM-700 Rev 4)* (p.1) — Quote: "On revisions prior to 3.2, normal discharge pressure was 180 bar, measured by the original PS-04 sensor."
  * **[CFG-EXPORT-01]** *AegisConfigExport v1.4* (sensors) — Quote: "sensor_ps04a_threshold_bar: 200"

### Question 3: What does alarm A17 indicate, and what are its possible causes?
- **Epistemic Classification:** `DEFINITIVE`
- **Direct Answer:**
> Alarm A17 indicates 'Hydraulic Pressure Low', which triggers when HPU discharge pressure drops below 150 bar. Its possible causes are:
> 1. Isolation valve IV-21 is closed or partially closed.
> 2. Hydraulic fluid level is low.
> 3. Pressure sensor (PS-04/PS-04A) signal is invalid or out of calibration (sensor drift).
- **Verified Claims:**
  * Alarm A17 indicates Hydraulic Pressure Low (pressure below 150 bar). (Supported by: `FACT_ALARM_A17_DEFINITION`)
  * Possible causes are: IV-21 closed/partially closed; low hydraulic fluid level; sensor signal invalid or drifted. (Supported by: `FACT_ALARM_A17_DEFINITION, FACT_MM_A17_CAUSES`)
- **Provenance Citations:**
  * **[AEG-AL-700-R5]** *Aegis Alarm Reference (AEG-AL-700 Rev 5)* (p.1) — Quote: "Alarm A17 | Hydraulic pressure below 150 bar | RED | 1. IV-21 closed or partially closed 2. Low hydraulic fluid 3. Pressure sensor signal invalid | See Section 4 Maintenance Manual. If persistent > 10 s, run Shutdown Proc. 4.7"
  * **[AEG-MM-700-R3]** *Aegis Series-7 HCS Maintenance Manual (AEG-MM-700 Rev 3)* (p.1) — Quote: "Check: Isolation valve IV-21 closed or partially closed; Hydraulic fluid level is low; Pressure sensor (PS-04 / PS-04A) signal invalid or out of calibration"

### Question 4: Is PS-04 the same component as PS-04A?
- **Epistemic Classification:** `DEFINITIVE`
- **Direct Answer:**
> No, PS-04 is not the same component as PS-04A. ECN-1042 explicitly states that PS-04A features an updated signal conditioning circuit to resolve an 18-month signal drift issue, and is not a form-fit-function replacement for PS-04. PS-04A requires controller firmware revision 3.2 or later and operates at 200 bar, whereas PS-04 operated at 180 bar on older revisions.
- **Verified Claims:**
  * PS-04 and PS-04A are distinct hardware components and not form-fit-function replacements. (Supported by: `FACT_ECN1042_REPLACEMENT`)
- **Provenance Citations:**
  * **[ECN-1042]** *Engineering Change Notice ECN-1042* (p.1) — Quote: "Effective software revision 3.2, pressure sensor PS-04 is replaced by pressure sensor PS-04A at the HPU discharge line... normal HPU discharge pressure setpoint is revised from 180 bar to 200 bar."

### Question 5: Which document introduced the change from PS-04 to PS-04A?
- **Epistemic Classification:** `DEFINITIVE`
- **Direct Answer:**
> The change from PS-04 to PS-04A was introduced by Engineering Change Notice ECN-1042 (Title: 'Pressure Sensor Replacement (PS-04 → PS-04A) and Operating Pressure Update', effective Software Revision 3.2).
- **Verified Claims:**
  * Engineering Change Notice ECN-1042 introduced the change from PS-04 to PS-04A. (Supported by: `FACT_ECN1042_REPLACEMENT`)
- **Provenance Citations:**
  * **[ECN-1042]** *Engineering Change Notice ECN-1042* (p.1) — Quote: "Effective software revision 3.2, pressure sensor PS-04 is replaced by pressure sensor PS-04A at the HPU discharge line... normal HPU discharge pressure setpoint is revised from 180 bar to 200 bar."
  * **[REV-HIST-700]** *Revision History (AEG-RH-700)* (Revision History) — Quote: "3.2 | 2025-09-30 | Pressure sensor PS-04 replaced by PS-04A. Normal HPU discharge pressure setpoint changed from 180 bar to 200 bar. See ECN-1042. | ECN-1042, AEG-OM-700 Rev 3, AEG-MM-700 Rev 2, AEG-CR-700 Rev 2"

### Question 6: Which components connect directly to the HCS controller, according to the hydraulic schematic?
- **Epistemic Classification:** `DEFINITIVE`
- **Direct Answer:**
> According to the hydraulic schematic (AEG-DWG-H01), only two components connect directly to the HCS controller (PLC-03) via purple control/signal lines:
> 1. Pressure Sensor PS-04A
> 2. Isolation Valve IV-21
> (Note on HPU: The line connecting PLC-03 to the Hydraulic Power Unit is drawn in dark grey, which the drawing legend explicitly designates as a hydraulic fluid path rather than a purple control/signal connection. The Main Reservoir, Auxiliary Reservoir, and Press Circuit also connect only via fluid paths and do not connect directly to PLC-03).
- **Verified Claims:**
  * According to schematic AEG-DWG-H01, purple control/signal lines directly connect PLC-03 to PS-04A and IV-21 only. (Supported by: `FACT_HYD_SCHEMATIC_PLC_CONNECTIONS`)
  * The line between PLC-03 and HPU is dark grey (hydraulic fluid path per legend), not a purple control line. (Supported by: `FACT_HYD_SCHEMATIC_PLC_CONNECTIONS`)
- **Provenance Citations:**
  * **[AEG-DWG-H01]** *Hydraulic Schematic (AEG-DWG-H01)* (p.1) — Quote: "purple lines: control/signal connections to PLC-03; grey lines: hydraulic fluid path; tan line: reservoir interconnect"

### Question 7: What action is required if alarm A17 persists for more than 10 seconds?
- **Epistemic Classification:** `DEFINITIVE`
- **Direct Answer:**
> If alarm A17 persists for more than 10 seconds, the operator must execute Shutdown Procedure 4.7 before investigating further. Procedure 4.7 requires: closing isolation valve IV-21, confirming hydraulic pressure decay, switching the POWER selector to OFF, and locking/tagging out per site safety procedures before proceeding to troubleshooting. Silencing the alarm alone is prohibited.
- **Verified Claims:**
  * Execute Shutdown Procedure 4.7 if alarm A17 persists for more than 10 seconds. (Supported by: `FACT_MM_A17_ACTION_PERSISTENT, FACT_CFG_A17_SHUTDOWN`)
- **Provenance Citations:**
  * **[AEG-MM-700-R3]** *Aegis Series-7 HCS Maintenance Manual (AEG-MM-700 Rev 3)* (p.1) — Quote: "If alarm A17 persists for more than 10 seconds, execute Shutdown Procedure 4.7 before investigating further. Do not attempt to clear a persistent A17 by silencing the alarm alone."
  * **[CFG-EXPORT-01]** *AegisConfigExport v1.4* (alarms.A17) — Quote: "{'description': 'hydraulic_pressure_low', 'persistence_before_shutdown_seconds': 10, 'shutdown_procedure_ref': '4.7'}"

### Question 8: Under what circumstances must the controller not be reset?
- **Epistemic Classification:** `DEFINITIVE`
- **Direct Answer:**
> The PLC-03 controller must NOT be reset while hydraulic pressure is above 50 bar. The controller reset routine re-initializes valve driver outputs; if the circuit remains pressurized, this can produce a momentary uncommanded actuation/transition of Isolation Valve IV-21. Hydraulic pressure must be bled below 50 bar using the manual bleed procedure before a reset is permitted.
- **Verified Claims:**
  * The controller must not be reset while hydraulic pressure is above 50 bar. (Supported by: `FACT_OM_CONTROLLER_RESET_RESTRICTION, FACT_CFG_CONTROLLER_RESET_MAX`)
  * Resetting above 50 bar re-initializes valve drivers and can cause momentary uncommanded actuation of IV-21. (Supported by: `FACT_MM_CONTROLLER_RESET_MECHANISM`)
- **Provenance Citations:**
  * **[AEG-OM-700-R4]** *Aegis Series-7 HCS Operator Manual (AEG-OM-700 Rev 4)* (p.2) — Quote: "Do not reset the PLC-03 controller while hydraulic pressure is above 50 bar. Resetting the controller under pressure can cause an uncommanded valve transition."
  * **[AEG-MM-700-R3]** *Aegis Series-7 HCS Maintenance Manual (AEG-MM-700 Rev 3)* (p.1) — Quote: "The controller reset routine re-initializes valve driver outputs; if the circuit is still pressurized, this can produce a momentary uncommanded actuation of Isolation Valve IV-21."
  * **[CFG-EXPORT-01]** *AegisConfigExport v1.4* (controller_reset) — Quote: "{'min_pressure_bar_required_for_reset': None, 'max_pressure_bar_allowed_for_reset': 50, 'note': 'reset is blocked in firmware above max_pressure_bar_allowed_for_reset'}"

### Question 9: What was the operating pressure threshold before software revision 3.2, and what changed it?
- **Epistemic Classification:** `DEFINITIVE`
- **Direct Answer:**
> Before software revision 3.2, the normal operating discharge pressure setpoint was 180 bar, measured by sensor PS-04. It was changed to 200 bar by Engineering Change Notice ECN-1042 (effective with Software Revision 3.2) alongside the replacement of PS-04 with PS-04A to improve press cycle times on Series-7 units manufactured after 2024.
- **Verified Claims:**
  * Before revision 3.2, normal operating pressure was 180 bar measured by sensor PS-04. (Supported by: `FACT_OM_OPERATING_PRESSURE_LEGACY`)
  * Engineering Change Notice ECN-1042 revised the setpoint to 200 bar alongside PS-04A replacement. (Supported by: `FACT_ECN1042_PRESSURE_SETPOINT`)
- **Provenance Citations:**
  * **[AEG-OM-700-R4]** *Aegis Series-7 HCS Operator Manual (AEG-OM-700 Rev 4)* (p.1) — Quote: "On revisions prior to 3.2, normal discharge pressure was 180 bar, measured by the original PS-04 sensor."
  * **[ECN-1042]** *Engineering Change Notice ECN-1042* (p.1) — Quote: "Effective software revision 3.2, pressure sensor PS-04 is replaced by pressure sensor PS-04A at the HPU discharge line... normal HPU discharge pressure setpoint is revised from 180 bar to 200 bar."

### Question 10: Which alarm is associated with a pressure sensor reading below 150 bar?
- **Epistemic Classification:** `DEFINITIVE`
- **Direct Answer:**
> Alarm A17 ('Hydraulic Pressure Low') is associated with a pressure sensor reading below 150 bar.
- **Verified Claims:**
  * Alarm A17 (Hydraulic Pressure Low) triggers when pressure is below 150 bar. (Supported by: `FACT_ALARM_A17_DEFINITION`)
- **Provenance Citations:**
  * **[AEG-AL-700-R5]** *Aegis Alarm Reference (AEG-AL-700 Rev 5)* (p.1) — Quote: "Alarm A17 | Hydraulic pressure below 150 bar | RED | 1. IV-21 closed or partially closed 2. Low hydraulic fluid 3. Pressure sensor signal invalid | See Section 4 Maintenance Manual. If persistent > 10 s, run Shutdown Proc. 4.7"

### Question 11: According to the component register, what is the location of the isolation valve IV-21?
- **Epistemic Classification:** `DEFINITIVE`
- **Direct Answer:**
> According to the Component Register (AEG-CR-700, Components sheet), the location of Isolation Valve IV-21 is 'Hydraulic Module'.
- **Verified Claims:**
  * According to AEG-CR-700 (Components sheet), IV-21 is located in the Hydraulic Module. (Supported by: `FACT_CR_IV21_LOCATION`)
- **Provenance Citations:**
  * **[AEG-CR-700]** *Component Register (AEG-CR-700)* (Components) — Quote: "IV-21 | Isolation Valve 21 | Isolation Valve; IV21 | Hydraulic Module | Active | Must be OPEN prior to HPU startup."

### Question 12: Does the training slide deck introduce any component or alarm not found in the manuals?
- **Epistemic Classification:** `DEFINITIVE`
- **Direct Answer:**
> Yes. The training slide deck introduces the 'Auxiliary Reservoir' (Slide 2), explicitly noting that it is a Line 4/5-specific configuration detail that tops up fluid during peak demand and is not covered in the standard Operator Manual. The training slide deck does not introduce any new alarms.
- **Verified Claims:**
  * The training slide deck introduces the Auxiliary Reservoir, which is not found in the standard Operator Manual. (Supported by: `FACT_TRN_AUX_RESERVOIR`)
  * The training slide deck introduces no new alarms. (Supported by: `FACT_TRN_AUX_RESERVOIR`)
- **Provenance Citations:**
  * **[TRN-HPU-01]** *HPU Basics Training Excerpt* (p.2) — Quote: "It pulls fluid from the main reservoir and, on most Line 4/5 configurations, tops up from a smaller Auxiliary Reservoir during peak demand... Note: 'Auxiliary Reservoir' is a Line 4/5-specific configuration detail and is not covered in the standard Operator Manual."

### Question 13: What sensor ID appears on the diagnostics screenshot, and does it match a known component
- **Epistemic Classification:** `DEFINITIVE`
- **Direct Answer:**
> The sensor ID that appears on the diagnostics screenshot is 'P.S.04-A'. Yes, it matches the known active component PS-04A (Pressure Sensor 04A), which is the HPU discharge pressure sensor. The diagnostics screen note confirms that this format represents the sensor tag as printed on the physical unit label.
- **Verified Claims:**
  * The sensor ID 'P.S.04-A' appears on the diagnostics screenshot. (Supported by: `FACT_HMI_DIAG_SENSOR_ID`)
  * 'P.S.04-A' matches known component PS-04A (Pressure Sensor 04A). (Supported by: `FACT_HMI_DIAG_SENSOR_ID`)
- **Provenance Citations:**
  * **[HMI-SCREEN-03]** *HMI Diagnostics Screen* (root) — Quote: "Tag: P.S.04-A | Signal Type: 4-20 mA | Scaled Value: 200.3 bar | Note: this screen displays the sensor tag as printed on the physical unit label."

### Question 14: Per the revision history, when did software revision 3.2 take effect, and what changed alongside it?
- **Epistemic Classification:** `DEFINITIVE`
- **Direct Answer:**
> Per the revision history (AEG-RH-700, Revision History sheet), software revision 3.2 took effect on September 30, 2025 (2025-09-30). Alongside it, pressure sensor PS-04 was replaced by PS-04A, and the normal HPU discharge pressure setpoint was increased from 180 bar to 200 bar (referencing ECN-1042), with corresponding updates to AEG-OM-700, AEG-MM-700, and AEG-CR-700.
- **Verified Claims:**
  * Software revision 3.2 took effect on 2025-09-30. (Supported by: `FACT_RH_REV32_DETAILS`)
  * Pressure sensor PS-04 was replaced by PS-04A and setpoint changed from 180 bar to 200 bar per ECN-1042. (Supported by: `FACT_RH_REV32_DETAILS`)
- **Provenance Citations:**
  * **[REV-HIST-700]** *Revision History (AEG-RH-700)* (Revision History) — Quote: "3.2 | 2025-09-30 | Pressure sensor PS-04 replaced by PS-04A. Normal HPU discharge pressure setpoint changed from 180 bar to 200 bar. See ECN-1042. | ECN-1042, AEG-OM-700 Rev 3, AEG-MM-700 Rev 2, AEG-CR-700 Rev 2"

### Question 15: What does sensor_ps04a_threshold_bar in the configuration export correspond to in the operator manual's terminology?
- **Epistemic Classification:** `DEFINITIVE`
- **Direct Answer:**
> In the Operator Manual's terminology (AEG-OM-700 Section 4.3 and Section 5), 'sensor_ps04a_threshold_bar' (configured as 200 bar) corresponds to the 'normal operating pressure' (or 'normal HPU discharge pressure' setpoint) for software revision 3.2 and later.
- **Verified Claims:**
  * 'sensor_ps04a_threshold_bar' corresponds to 'normal operating pressure' in the Operator Manual. (Supported by: `FACT_CFG_PS04A_THRESHOLD, FACT_OM_OPERATING_PRESSURE_CURRENT`)
- **Provenance Citations:**
  * **[CFG-EXPORT-01]** *AegisConfigExport v1.4* (sensors) — Quote: "sensor_ps04a_threshold_bar: 200"
  * **[AEG-OM-700-R4]** *Aegis Series-7 HCS Operator Manual (AEG-OM-700 Rev 4)* (p.1) — Quote: "Verify discharge pressure, as reported by PS-04A, reaches 200 bar. This is the normal operating pressure for software revision 3.2 and later"

### Question 16: Does the 200 bar threshold apply to all Aegis HCS units, or only some?
- **Epistemic Classification:** `VERSION_SCOPED`
- **Direct Answer:**
> The 200 bar threshold applies only to some units — specifically those running software revision 3.2 and later with sensor PS-04A installed (Series-7 units manufactured after 2024). Units running software revisions prior to 3.2 (revisions 3.0 and 3.1) continue to operate at 180 bar using sensor PS-04.
- **Verified Claims:**
  * The 200 bar threshold applies only to units running software revision 3.2 and later. (Supported by: `FACT_OM_OPERATING_PRESSURE_CURRENT, FACT_ECN1042_PRESSURE_SETPOINT`)
  * Units running revisions prior to 3.2 continue to operate at 180 bar with sensor PS-04. (Supported by: `FACT_OM_OPERATING_PRESSURE_LEGACY`)
- **Provenance Citations:**
  * **[AEG-OM-700-R4]** *Aegis Series-7 HCS Operator Manual (AEG-OM-700 Rev 4)* (p.1) — Quote: "Verify discharge pressure, as reported by PS-04A, reaches 200 bar. This is the normal operating pressure for software revision 3.2 and later"
  * **[ECN-1042]** *Engineering Change Notice ECN-1042* (p.1) — Quote: "Effective software revision 3.2, pressure sensor PS-04 is replaced by pressure sensor PS-04A at the HPU discharge line... normal HPU discharge pressure setpoint is revised from 180 bar to 200 bar."
  * **[AEG-OM-700-R4]** *Aegis Series-7 HCS Operator Manual (AEG-OM-700 Rev 4)* (p.1) — Quote: "On revisions prior to 3.2, normal discharge pressure was 180 bar, measured by the original PS-04 sensor."

### Question 17: Is PS-04 the same as PS-40?
- **Epistemic Classification:** `DEFINITIVE`
- **Direct Answer:**
> No, PS-04 is NOT the same as PS-40. PS-04 is a legacy pressure sensor on the HPU discharge line (hydraulic circuit), whereas PS-40 is an active pressure sensor on the Coolant Loop (Skid B). Both the Component Register (AEG-CR-700, Components sheet) and configuration export explicitly state: 'NOT related to the HPU discharge circuit. Do not confuse with PS-04 / PS-04A.'
- **Verified Claims:**
  * PS-04 and PS-40 are completely separate components in different physical circuits. (Supported by: `FACT_CR_PS40_LOCATION, FACT_CFG_PS40_ZONE`)
- **Provenance Citations:**
  * **[AEG-CR-700]** *Component Register (AEG-CR-700)* (Components) — Quote: "PS-40 | Pressure Sensor 40 | P40; PS40 | Coolant Loop, Skid B | Active | NOT related to the HPU discharge circuit. Do not confuse with PS-04 / PS-04A."
  * **[CFG-EXPORT-01]** *AegisConfigExport v1.4* (sensors) — Quote: "unrelated to HPU discharge circuit; do not map to sensor_ps04a_* keys"

### Question 18: What was the pressure limit before revision 3.2?
- **Epistemic Classification:** `DEFINITIVE`
- **Direct Answer:**
> Before software revision 3.2, the normal operating discharge pressure setpoint was 180 bar, measured by sensor PS-04. It was changed to 200 bar by Engineering Change Notice ECN-1042 (effective with Software Revision 3.2) alongside the replacement of PS-04 with PS-04A to improve press cycle times on Series-7 units manufactured after 2024.
- **Verified Claims:**
  * Before revision 3.2, normal operating pressure was 180 bar measured by sensor PS-04. (Supported by: `FACT_OM_OPERATING_PRESSURE_LEGACY`)
  * Engineering Change Notice ECN-1042 revised the setpoint to 200 bar alongside PS-04A replacement. (Supported by: `FACT_ECN1042_PRESSURE_SETPOINT`)
- **Provenance Citations:**
  * **[AEG-OM-700-R4]** *Aegis Series-7 HCS Operator Manual (AEG-OM-700 Rev 4)* (p.1) — Quote: "On revisions prior to 3.2, normal discharge pressure was 180 bar, measured by the original PS-04 sensor."
  * **[ECN-1042]** *Engineering Change Notice ECN-1042* (p.1) — Quote: "Effective software revision 3.2, pressure sensor PS-04 is replaced by pressure sensor PS-04A at the HPU discharge line... normal HPU discharge pressure setpoint is revised from 180 bar to 200 bar."

### Question 19: What is the maximum continuous operating temperature of PS-04A?
- **Epistemic Classification:** `UNANSWERABLE_GAP`
- **Direct Answer:**
> Cannot be determined from the dataset (Epistemic Gap). The provided documentation package (including Operator Manual AEG-OM-700, Maintenance Manual AEG-MM-700, ECN-1042, Component Register AEG-CR-700, and Calibration Record Appendix C) contains no specification for the maximum continuous operating temperature of sensor PS-04A.
- **Epistemic Gaps / Missing Data:**
  * ⚠️ *PS-04A operating temperature* -> Exhaustive scan of all 20 dataset files confirms that continuous operating temperature for PS-04A is completely omitted.

### Question 20: What is the calibration interval for the electrical system diagram's voltage sensor?
- **Epistemic Classification:** `FALSE_PREMISE`
- **Direct Answer:**
> Cannot be determined due to a false premise and unstated documentation:
> 1. False Premise: The electrical schematic (AEG-DWG-E02) contains NO voltage sensor (it only depicts Main Disconnect Q1, Control Transformer T1, PLC-03 power supplies/rack, safety relay KA1, and valve driver).
> 2. Unstated Calibration Interval: Additionally, even on the pressure sensor calibration sheet (Appendix C), it is explicitly noted: 'No calibration interval is specified for PS-04A on this form; recalibration frequency should be confirmed against the applicable maintenance schedule, which is not included in this binder.'
- **Epistemic Gaps / Missing Data:**
  * ⚠️ *voltage_sensor* -> 1. False Premise: Electrical schematic AEG-DWG-E02 contains no voltage sensor. 2. Gap: Appendix C calibration sheet explicitly states no interval is specified.

### Question 21: Who approved engineering bulletin ECN-1058?
- **Epistemic Classification:** `UNANSWERABLE_GAP`
- **Direct Answer:**
> Cannot be determined from the dataset (Epistemic Gap). Engineering Change Notice ECN-1058 indicates a status of 'Released' and references ECN-1042, but does not list an author name, approver identity, or approval signature.
- **Epistemic Gaps / Missing Data:**
  * ⚠️ *ECN-1058* -> ECN-1058 states status 'Released' and references ECN-1042, but omits author, approver name, and signature.

### Question 22: What is the mean time between failures for the isolation valve IV-21?
- **Epistemic Classification:** `UNANSWERABLE_GAP`
- **Direct Answer:**
> Cannot be determined from the dataset (Epistemic Gap). The mean time between failures (MTBF) for Isolation Valve IV-21 is not specified in the Component Register (AEG-CR-700), Maintenance Manual (AEG-MM-700), or any other document in the package.
- **Epistemic Gaps / Missing Data:**
  * ⚠️ *IV-21* -> The documentation package contains no MTBF or component failure-rate figures.

### Question 23: Is the Aegis Series-7 HCS compatible with a 3-phase 400V supply?
- **Epistemic Classification:** `UNANSWERABLE_GAP`
- **Direct Answer:**
> Cannot be determined / Not stated in the documentation. The Component Register (AEG-CR-700, Components sheet) and Electrical Schematic (AEG-DWG-E02) only document a 480V incoming disconnect (Q1) and a 480:120V control transformer (T1). A 3-phase 400V supply is not mentioned anywhere in the dataset, so compatibility cannot be confirmed from the provided sources.
- **Verified Claims:**
  * Component Register (Components sheet) specifies Q1 is a 480V incoming disconnect and T1 is 480:120V. (Supported by: `FACT_CR_Q1_SPECS, FACT_CR_T1_SPECS`)
  * Compatibility with a 3-phase 400V supply is not stated in the documentation package. (Supported by: `FACT_ELEC_POWER_VOLTAGE`)
- **Provenance Citations:**
  * **[AEG-CR-700]** *Component Register (AEG-CR-700)* (Components) — Quote: "Q1 | Main Disconnect | — | Control Cabinet 1 | Active | 480V incoming disconnect."
  * **[AEG-CR-700]** *Component Register (AEG-CR-700)* (Components) — Quote: "T1 | Control Transformer | — | Control Cabinet 1 | Active | 480:120V control power."
  * **[AEG-DWG-E02]** *Electrical Schematic (AEG-DWG-E02)* (Power distribution and interlock wiring) — Quote: "MAIN DISCONNECT Q1 -> CONTROL XFMR T1 480:120V -> PLC-03 24VDC POWER SUPPLY & PLC-03 I/O RACK"
- **Epistemic Gaps / Missing Data:**
  * ⚠️ *power_supply_400V* -> The package only documents a 480V supply (Q1/T1). Compatibility with 400V is not stated in the sources.
