# GlucoTwin India — DigiTech

**An explainable, patient-specific digital twin prototype for two-hour early warning of synthetic glucose excursions.**

> **Important:** This is a student proof-of-concept built entirely with synthetic data. It is not a medical device, has not been clinically validated, and must not be used for diagnosis, treatment, medication changes, or emergency decisions.

## Team and institution

- **Team name:** DigiTech
- **Team lead:** Zeeshan Ali Sheikh 
- **College/incubator:** Maulana Abul Kalam Azad University of Technology

## Project title

**GlucoTwin India: An Explainable, Two-Hour Digital Twin for Early Warning of Glucose Excursions**

## Problem statement

A retrospective laboratory result or a single glucose reading does not describe how a person's glucose trajectory may evolve over the next few hours. This prototype demonstrates how historical patient context can be fused with time-stamped glucose and wearable-style signals to estimate whether a synthetic glucose reading currently below 180 mg/dL will cross that threshold within two hours.

This narrowly scoped proof-of-concept addresses the challenge's requirement for two data streams and a doctor-facing conceptual dashboard. It does **not** claim to predict every type of adverse health event or provide an individual treatment plan.

## Healthcare use case

A clinician opens a synthetic patient twin, reviews static EHR-style context (age, BMI, diabetes duration, HbA1c, hypertension flag and simulated medication adherence), and sees an hourly stream (CGM reading/trend, meal carbohydrate log, steps, heart rate, HRV, sleep and stress proxy). The model estimates the probability of a threshold crossing in the next two hours. A review cue prompts the clinician to verify signal quality and context before deciding what, if anything, to do.

The 180 mg/dL line is a **prototype event label**, not a universal clinical decision rule. Clinical interpretation depends on context and must be made by a qualified clinician.

## What makes this a digital twin (rather than only a classifier)?

1. **Patient-specific state:** static profile fields are joined to that patient's evolving hourly sensor stream.
2. **Temporal update:** move the time slider to advance the twin and obtain a fresh forecast based only on information available at that timestamp.
3. **Forecast + retrospective check:** the dashboard shows a model-estimated probability; the simulator's future label is isolated in an expander for retrospective demonstration only.
4. **Scenario exploration:** adjust recent carbs, steps and sleep to inspect model sensitivity. This is deliberately labeled as a model-input sensitivity tool, not a complete physiological simulator or causal intervention estimate.
5. **Human-in-the-loop:** outputs are review prompts, never automated diagnosis or medication instructions.

## Technical stack

- Python 3.11+
- Streamlit dashboard
- pandas and NumPy for synthetic EHR/time-series creation and feature preparation
- scikit-learn `ExtraTreesClassifier` for a probabilistic two-hour early-warning model (requirements pin version 1.8.0 to match the bundled model artefact)
- joblib for model packaging
- Plotly for patient timeline and feature-importance views
- Python `unittest` for basic data-integrity tests (no extra test dependency required)

## AI/ML methodology

- **Target:** among timestamps where current synthetic glucose is below 180 mg/dL, label 1 if either of the next two hourly simulator readings is at least 180 mg/dL; otherwise label 0.
- **Inputs:** historical EHR context plus current/recent CGM, recent meal carbs, step count, heart rate, HRV, previous-night sleep, sleep efficiency, time since last logged meal and stress proxy.
- **Model:** Extra Trees ensemble; a decision threshold is selected on validation data to maximise F2 score, giving more weight to recall during this demonstration.
- **Evaluation:** split by unique patient IDs into train, validation and held-out test groups. Measurements from one patient never appear in more than one partition.
- **Reproducibility:** default simulator/model seed is 42; full settings and measured held-out synthetic metrics are in [`reports/model_evaluation.json`](reports/model_evaluation.json).
- **Interpretability:** global feature importance is displayed. It is not a causal explanation for an individual prediction.

## Architecture

See [`docs/Architecture_Diagram.pdf`](docs/Architecture_Diagram.pdf) or [`assets/architecture.png`](assets/architecture.png). Editable slide source is included in [`docs/GlucoTwin_India_Presentation.pptx`](docs/GlucoTwin_India_Presentation.pptx).

## Run locally

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m src.synthetic_data
python -m src.train_model
streamlit run app.py
```

Open the local URL printed by Streamlit. If model/data artefacts are absent, the app can generate/train them on first run; running the two Python commands explicitly first makes the setup easier to debug.

## Repository contents

- `app.py` — clinician-facing Streamlit prototype
- `src/synthetic_data.py` — reproducible EHR + hourly wearable/CGM-style stream simulator
- `src/train_model.py` — patient-grouped training/evaluation pipeline
- `src/twin_engine.py` — model loading and prediction helper
- `data/synthetic_twin_stream.csv` — generated artificial hourly records for the demo
- `models/glucotwin_model.joblib` — reproducible model bundle
- `reports/model_evaluation.json` — measured held-out synthetic evaluation
- `reports/feature_importance.csv` — global feature importance
- `reports/heldout_patient_predictions.csv` — held-out predictions for reproducibility and audit
- `docs/Architecture_Diagram.pdf` — architecture diagram
- `docs/GlucoTwin_India_Presentation.pptx` and `.pdf` — presentation
- `docs/Technical_Report.md` — methods, limits and future work

## Required 20-minute demonstration video

**YouTube Status:** `https://youtu.be/AESWoVHgU5E`

The timed narration and screen-by-screen run-of-show is in [`docs/GlucoTwin_Demo-Video.mp4`][`docs/GlucoTwin_Video-Subtitles.srt`]. The video is least 20 minutes long, demonstrating the working app, explain the model and synthetic data and discusses the limitations.

## Open-source license

This repository is released under the **MIT License**. See [`LICENSE`](LICENSE).

## Data privacy and responsible use

- All patient profiles and sensor streams in this repository are synthetic and generated by `src/synthetic_data.py`.
- No clinical database or personal health record is bundled.
- No live devices, APIs, or external patient systems are connected.
- Simulated medication adherence is only a synthetic input, not a recommendation.
- Clinical deployment would require prospective clinical validation, independent external evaluation, safety/ethics review, human factors testing, security review, calibration analysis and medical/regulatory assessment.

## Evidence and context

- The International Diabetes Federation's 2025 Diabetes Atlas reports an estimated **90.0 million** adults aged 20–79 living with diabetes in India in 2024; estimates depend on the Atlas definition and methodology. [IDF Diabetes Atlas, 11th edition (2025)](https://diabetesatlas.org/media/uploads/sites/3/2025/10/IDF_Diabetes_Atlas_11th_Edition_2025_WEB.pdf)
- WHO notes diabetes can cause severe long-term complications and that detection, appropriate treatment, physical activity and healthy eating are important parts of management. [WHO Diabetes Fact Sheet](https://www.who.int/news-room/fact-sheets/detail/diabetes)
- Challenge requirements and submission checklist: [Digital Twin Challenge 2026 — Unstop](https://unstop.com/hackathons/crp-digital-twin-challenge-2026-happiest-health-1757873)

---

**DigiTech | GlucoTwin India | Digital Twin Challenge 2026**
