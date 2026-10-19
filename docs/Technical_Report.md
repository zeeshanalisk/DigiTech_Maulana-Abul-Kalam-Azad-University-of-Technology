# GlucoTwin India — Technical Report

## 1. Executive summary

GlucoTwin India is a proof-of-concept patient-specific digital twin for forecasting a narrowly defined event: a synthetic glucose reading crossing 180 mg/dL within the next two hourly samples. It combines historical patient-profile fields with dynamic CGM/wearable-like streams, presents a probability in a clinician-oriented interface, and supports transparent scenario sensitivity exploration.

This is an engineering demonstration, not a clinical prediction system. The simulator creates the labels; therefore, measured results indicate how well the model learns this particular synthetic process, not how accurately it would forecast glucose in real patients.

## 2. Motivation and scope

The Digital Twin Challenge asks teams to join static/historical EHR-style information with a dynamic sensor stream and produce a localized health-outcome forecast. Rather than claiming a whole-body model, this prototype limits itself to a two-hour glucose-threshold crossing. The scope is intentionally narrow so the full pipeline can be implemented, inspected and demonstrated.

## 3. Synthetic data generation

`src/synthetic_data.py` creates artificial person-level factors (age, sex, BMI, diabetes duration, HbA1c, hypertension flag, simulated adherence) and hourly values for glucose, carbohydrates, steps, heart rate, HRV, previous-night sleep, sleep efficiency and a stress proxy. A stochastic recurrence simulates glucose dynamics. The next-two-hour target is generated from simulated future glucose values.

The training target is available only for retrospective labeling. Future glucose values and target columns are explicitly excluded from the model features. No real patient records are used.

## 4. Task definition

For a timestamp t with current synthetic glucose below 180 mg/dL, the target is positive when at least one of the simulator readings at t+1 hour or t+2 hours reaches or exceeds 180 mg/dL. Rows whose current glucose is already at or above 180 mg/dL are excluded from the early-warning modelling set; the dashboard reports them as currently elevated rather than treating them as a successful forecast.

This cut-off is a prototype label chosen to make the modelling task concrete. Real glucose targets and alerts are individualised and must be interpreted by a clinician. The output is not a diagnosis or treatment directive.

## 5. Feature fusion

Static/historical context: age, BMI, diabetes duration, HbA1c, hypertension and simulated medication adherence.

Dynamic context: current glucose, one-hour glucose change, short-window glucose mean and variability, recent carbohydrate logs, steps, heart rate, HRV, previous-night sleep, sleep efficiency, time since meal and stress proxy.

At inference, the selected timestamp's available feature vector is scored; the future label is never passed to the model. The scenario controls change model inputs to demonstrate sensitivity but do not run a full physiological simulator.

## 6. Model and evaluation

An Extra Trees classifier estimates the probability of the positive target. A decision threshold is chosen on the validation set by maximising F2 score. Patients—not hourly rows—are separated into train, validation and test partitions to reduce same-person leakage across splits.

Measured metrics and the exact group/record counts are recorded in `reports/model_evaluation.json`. The test metrics are synthetic-domain metrics, not clinical performance indicators. `reports/feature_importance.csv` records global model feature importance; that importance is neither causal nor a local explanation for a single patient.

## 7. User experience

The Streamlit dashboard provides:

- synthetic patient selection and time-step advancement;
- a 24-hour glucose timeline with event threshold reference;
- current EHR context and dynamic wearable/CGM observations;
- model-estimated probability and a clinician review cue;
- a what-if sensitivity panel for meal carbs, steps and sleep;
- global feature importance and held-out synthetic model metrics;
- retrospective synthetic outcome labels in a clearly separated expander.

## 8. Responsible use and safeguards

- No real patient data, direct identifiers or live sensor connections are present.
- The app does not diagnose, prescribe, change medication, or make emergency decisions.
- The result is labelled as a model estimate, not certainty.
- Current values at/above the event threshold are surfaced as existing elevations rather than future-event forecasts.
- A low predicted probability is not evidence that risk is absent.
- Model features and target depend on an artificial process. Real-world deployment would require clinical validation, calibration, external validation, monitoring, security review, clinician governance and regulatory assessment.

## 9. Future work

1. Evaluate on appropriately governed, real-world de-identified CGM and EHR datasets.
2. Calibrate probabilities and quantify uncertainty across subgroups and sensor quality levels.
3. Add missingness-aware time-series modelling and stronger patient-level longitudinal baselines.
4. Build auditable event explanations with methods validated for the final model.
5. Complete clinical workflow research with clinicians and patients before any real deployment.
6. Add privacy/security controls, access management and audit logging if real records are ever introduced.

## 10. References

- International Diabetes Federation. *IDF Diabetes Atlas, 11th Edition* (2025). https://diabetesatlas.org/media/uploads/sites/3/2025/10/IDF_Diabetes_Atlas_11th_Edition_2025_WEB.pdf
- World Health Organization. *Diabetes Fact Sheet*. https://www.who.int/news-room/fact-sheets/detail/diabetes
- Happiest Health / Unstop. *Digital Twin Challenge 2026*. https://unstop.com/hackathons/crp-digital-twin-challenge-2026-happiest-health-1757873
