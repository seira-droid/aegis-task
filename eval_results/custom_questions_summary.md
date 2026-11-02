# Evaluated Question Set: evaluation-questions.pdf

### Q1: What must be true before starting the Hydraulic Power Unit?
- **Epistemic Status:** `DEFINITIVE`
- **Answer:** Before starting the Hydraulic Power Unit (HPU), four conditions must be verified:
1. Hydraulic fluid level is within the normal band on the sight glass.
2. Isolation valve IV-21 is OPEN.
3. Emergency stop circuit is RESET.
4. Maintenance access panel is INSTALLED and secured (closed) — operating with the panel removed is prohibited due to exposed rotating components.

### Q2: What is the current normal operating pressure for the HPU, and under what conditions does that apply?
- **Epistemic Status:** `VERSION_SCOPED`
- **Answer:** The current normal operating pressure for the HPU is 200 bar. This setpoint applies to units running software revision 3.2 and later (with pressure sensor PS-04A installed, typically units manufactured after 2024 per ECN-1042). On units running software revisions prior to 3.2, normal discharge pressure was 180 bar, measured by sensor PS-04.

### Q3: What does alarm A17 indicate, and what are its possible causes?
- **Epistemic Status:** `DEFINITIVE`
- **Answer:** Alarm A17 indicates 'Hydraulic Pressure Low', which triggers when HPU discharge pressure drops below 150 bar. Its possible causes are:
1. Isolation valve IV-21 is closed or partially closed.
2. Hydraulic fluid level is low.
3. Pressure sensor (PS-04/PS-04A) signal is invalid or out of calibration (sensor drift).

### Q4: Is PS-04 the same component as PS-04A?
- **Epistemic Status:** `DEFINITIVE`
- **Answer:** No, PS-04 is not the same component as PS-04A. ECN-1042 explicitly states that PS-04A features an updated signal conditioning circuit to resolve an 18-month signal drift issue, and is not a form-fit-function replacement for PS-04. PS-04A requires controller firmware revision 3.2 or later and operates at 200 bar, whereas PS-04 operated at 180 bar on older revisions.

### Q5: Which document introduced the change from PS-04 to PS-04A?
- **Epistemic Status:** `DEFINITIVE`
- **Answer:** The change from PS-04 to PS-04A was introduced by Engineering Change Notice ECN-1042 (Title: 'Pressure Sensor Replacement (PS-04 → PS-04A) and Operating Pressure Update', effective Software Revision 3.2).

### Q6: Which components connect directly to the HCS controller, according to the hydraulic schematic?
- **Epistemic Status:** `DEFINITIVE`
- **Answer:** According to the hydraulic schematic (AEG-DWG-H01), only two components connect directly to the HCS controller (PLC-03) via purple control/signal lines:
1. Pressure Sensor PS-04A
2. Isolation Valve IV-21
(Note on HPU: The line connecting PLC-03 to the Hydraulic Power Unit is drawn in dark grey, which the drawing legend explicitly designates as a hydraulic fluid path rather than a purple control/signal connection. The Main Reservoir, Auxiliary Reservoir, and Press Circuit also connect only via fluid paths and do not connect directly to PLC-03).

### Q7: What action is required if alarm A17 persists for more than 10 seconds?
- **Epistemic Status:** `DEFINITIVE`
- **Answer:** If alarm A17 persists for more than 10 seconds, the operator must execute Shutdown Procedure 4.7 before investigating further. Procedure 4.7 requires: closing isolation valve IV-21, confirming hydraulic pressure decay, switching the POWER selector to OFF, and locking/tagging out per site safety procedures before proceeding to troubleshooting. Silencing the alarm alone is prohibited.

### Q8: Under what circumstances must the controller not be reset?
- **Epistemic Status:** `DEFINITIVE`
- **Answer:** The PLC-03 controller must NOT be reset while hydraulic pressure is above 50 bar. The controller reset routine re-initializes valve driver outputs; if the circuit remains pressurized, this can produce a momentary uncommanded actuation/transition of Isolation Valve IV-21. Hydraulic pressure must be bled below 50 bar using the manual bleed procedure before a reset is permitted.

### Q9: What was the operating pressure threshold before software revision 3.2, and what changed it?
- **Epistemic Status:** `DEFINITIVE`
- **Answer:** Before software revision 3.2, the normal operating discharge pressure setpoint was 180 bar, measured by sensor PS-04. It was changed to 200 bar by Engineering Change Notice ECN-1042 (effective with Software Revision 3.2) alongside the replacement of PS-04 with PS-04A to improve press cycle times on Series-7 units manufactured after 2024.

### Q10: Which alarm is associated with a pressure sensor reading below 150 bar?
- **Epistemic Status:** `DEFINITIVE`
- **Answer:** Alarm A17 ('Hydraulic Pressure Low') is associated with a pressure sensor reading below 150 bar.

### Q11: According to the component register, what is the location of the isolation valve IV-21?
- **Epistemic Status:** `DEFINITIVE`
- **Answer:** According to the Component Register (AEG-CR-700, Components sheet), the location of Isolation Valve IV-21 is 'Hydraulic Module'.

### Q12: Does the training slide deck introduce any component or alarm not found in the manuals?
- **Epistemic Status:** `DEFINITIVE`
- **Answer:** Yes. The training slide deck introduces the 'Auxiliary Reservoir' (Slide 2), explicitly noting that it is a Line 4/5-specific configuration detail that tops up fluid during peak demand and is not covered in the standard Operator Manual. The training slide deck does not introduce any new alarms.

### Q13: What sensor ID appears on the diagnostics screenshot, and does it match a known component
- **Epistemic Status:** `DEFINITIVE`
- **Answer:** The sensor ID that appears on the diagnostics screenshot is 'P.S.04-A'. Yes, it matches the known active component PS-04A (Pressure Sensor 04A), which is the HPU discharge pressure sensor. The diagnostics screen note confirms that this format represents the sensor tag as printed on the physical unit label.

### Q14: Per the revision history, when did software revision 3.2 take effect, and what changed alongside it?
- **Epistemic Status:** `DEFINITIVE`
- **Answer:** Per the revision history (AEG-RH-700, Revision History sheet), software revision 3.2 took effect on September 30, 2025 (2025-09-30). Alongside it, pressure sensor PS-04 was replaced by PS-04A, and the normal HPU discharge pressure setpoint was increased from 180 bar to 200 bar (referencing ECN-1042), with corresponding updates to AEG-OM-700, AEG-MM-700, and AEG-CR-700.

### Q15: What does sensor_ps04a_threshold_bar in the configuration export correspond to in the operator manual's terminology?
- **Epistemic Status:** `DEFINITIVE`
- **Answer:** In the Operator Manual's terminology (AEG-OM-700 Section 4.3 and Section 5), 'sensor_ps04a_threshold_bar' (configured as 200 bar) corresponds to the 'normal operating pressure' (or 'normal HPU discharge pressure' setpoint) for software revision 3.2 and later.

### Q16: Does the 200 bar threshold apply to all Aegis HCS units, or only some?
- **Epistemic Status:** `VERSION_SCOPED`
- **Answer:** The 200 bar threshold applies only to some units — specifically those running software revision 3.2 and later with sensor PS-04A installed (Series-7 units manufactured after 2024). Units running software revisions prior to 3.2 (revisions 3.0 and 3.1) continue to operate at 180 bar using sensor PS-04.

### Q17: Is PS-04 the same as PS-40?
- **Epistemic Status:** `DEFINITIVE`
- **Answer:** No, PS-04 is NOT the same as PS-40. PS-04 is a legacy pressure sensor on the HPU discharge line (hydraulic circuit), whereas PS-40 is an active pressure sensor on the Coolant Loop (Skid B). Both the Component Register (AEG-CR-700, Components sheet) and configuration export explicitly state: 'NOT related to the HPU discharge circuit. Do not confuse with PS-04 / PS-04A.'

### Q18: What was the pressure limit before revision 3.2?
- **Epistemic Status:** `DEFINITIVE`
- **Answer:** Before software revision 3.2, the normal operating discharge pressure setpoint was 180 bar, measured by sensor PS-04. It was changed to 200 bar by Engineering Change Notice ECN-1042 (effective with Software Revision 3.2) alongside the replacement of PS-04 with PS-04A to improve press cycle times on Series-7 units manufactured after 2024.

### Q19: What is the maximum continuous operating temperature of PS-04A?
- **Epistemic Status:** `UNANSWERABLE_GAP`
- **Answer:** Cannot be determined from the dataset (Epistemic Gap). The provided documentation package (including Operator Manual AEG-OM-700, Maintenance Manual AEG-MM-700, ECN-1042, Component Register AEG-CR-700, and Calibration Record Appendix C) contains no specification for the maximum continuous operating temperature of sensor PS-04A.

### Q20: What is the calibration interval for the electrical system diagram's voltage sensor?
- **Epistemic Status:** `FALSE_PREMISE`
- **Answer:** Cannot be determined due to a false premise and unstated documentation:
1. False Premise: The electrical schematic (AEG-DWG-E02) contains NO voltage sensor (it only depicts Main Disconnect Q1, Control Transformer T1, PLC-03 power supplies/rack, safety relay KA1, and valve driver).
2. Unstated Calibration Interval: Additionally, even on the pressure sensor calibration sheet (Appendix C), it is explicitly noted: 'No calibration interval is specified for PS-04A on this form; recalibration frequency should be confirmed against the applicable maintenance schedule, which is not included in this binder.'

### Q21: Who approved engineering bulletin ECN-1058?
- **Epistemic Status:** `UNANSWERABLE_GAP`
- **Answer:** Cannot be determined from the dataset (Epistemic Gap). Engineering Change Notice ECN-1058 indicates a status of 'Released' and references ECN-1042, but does not list an author name, approver identity, or approval signature.

### Q22: What is the mean time between failures for the isolation valve IV-21?
- **Epistemic Status:** `UNANSWERABLE_GAP`
- **Answer:** Cannot be determined from the dataset (Epistemic Gap). The mean time between failures (MTBF) for Isolation Valve IV-21 is not specified in the Component Register (AEG-CR-700), Maintenance Manual (AEG-MM-700), or any other document in the package.

### Q23: Is the Aegis Series-7 HCS compatible with a 3-phase 400V supply?
- **Epistemic Status:** `UNANSWERABLE_GAP`
- **Answer:** Cannot be determined / Not stated in the documentation. The Component Register (AEG-CR-700, Components sheet) and Electrical Schematic (AEG-DWG-E02) only document a 480V incoming disconnect (Q1) and a 480:120V control transformer (T1). A 3-phase 400V supply is not mentioned anywhere in the dataset, so compatibility cannot be confirmed from the provided sources.

