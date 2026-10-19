from __future__ import annotations
import json
from pathlib import Path
import sys
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from src.features import FEATURE_COLUMNS, TARGET_COLUMN
from src.train_model import train_pipeline
from src.twin_engine import load_bundle, predict_row

st.set_page_config(page_title="GlucoTwin India | DigiTech", page_icon="🧬", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;600;700;800&display=swap');
html, body, [class*="css"] {font-family: 'DM Sans', sans-serif;}
.stApp {background: linear-gradient(180deg,#f6f9ff 0%,#ffffff 34%,#f8fbff 100%);}
.block-container {padding-top: 1.5rem; padding-bottom: 2rem; max-width: 1400px;}
.hero {background: linear-gradient(125deg,#111d42 0%,#1f3b72 55%,#176e84 100%); padding: 1.6rem 1.8rem; border-radius: 20px; color: white; margin-bottom: 1.2rem; box-shadow: 0 12px 35px rgba(19,44,89,.18);}
.hero h1 {font-family:Manrope,sans-serif;font-size:2.25rem;margin:0 0 .35rem 0;color:#fff;}
.hero p {font-size:1.02rem;color:#dce9ff;margin:0;}
.kpi {background:white;border:1px solid #e3eaf5;border-radius:15px;padding:16px 18px;box-shadow:0 3px 12px rgba(25,51,89,.04);height:100%;}
.kpi .label {font-size:.78rem;color:#66758c;font-weight:600;text-transform:uppercase;letter-spacing:.05em;}
.kpi .value {font-family:Manrope,sans-serif;font-weight:800;font-size:1.7rem;color:#16274b;margin-top:4px;}
.kpi .hint {font-size:.78rem;color:#8090a7;margin-top:2px;}
.section {font-family:Manrope,sans-serif;font-size:1.18rem;font-weight:800;color:#14264b;margin:0 0 .5rem 0;}
.small-muted {color:#6b7990;font-size:.83rem;}
.risk-high {background:#fff0ef;color:#ad2520;border:1px solid #ffcfcb;padding:14px;border-radius:13px;}
.risk-mid {background:#fff8e8;color:#865600;border:1px solid #f4dfaa;padding:14px;border-radius:13px;}
.risk-low {background:#eaf8f3;color:#146b55;border:1px solid #c7eee1;padding:14px;border-radius:13px;}
div[data-testid="stMetric"] {background:white;border:1px solid #e4eaf3;padding:14px;border-radius:14px;}
</style>
""", unsafe_allow_html=True)

@st.cache_data(show_spinner=False)
def load_data():
    path = ROOT / "data" / "synthetic_twin_stream.csv"
    if not path.exists():
        from src.synthetic_data import generate_dataset
        path.parent.mkdir(exist_ok=True)
        df = generate_dataset()
        df.to_csv(path, index=False)
    df = pd.read_csv(path, parse_dates=["timestamp"])
    return df

@st.cache_resource(show_spinner=False)
def get_bundle():
    p = ROOT / "models" / "glucotwin_model.joblib"
    if not p.exists():
        train_pipeline()
    return load_bundle(p)

df = load_data()
bundle = get_bundle()
metrics_path = ROOT / "reports" / "model_evaluation.json"
metrics = json.loads(metrics_path.read_text()) if metrics_path.exists() else {}

st.markdown("""
<div class="hero">
  <div style="font-weight:700;letter-spacing:.13em;font-size:.72rem;color:#79e3e1;margin-bottom:.45rem">DIGITECH  •  DIGITAL TWIN CHALLENGE 2026</div>
  <h1>GlucoTwin India</h1>
  <p>A patient-specific, explainable early-warning twin for simulated glucose excursions — combining historical EHR context with a continuously updating wearable + CGM stream.</p>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### Twin controls")
    st.caption("Pick a synthetic patient and move along their hourly timeline.")
    patients = sorted(df.patient_id.unique())
    chosen_patient = st.selectbox("Synthetic patient", patients, index=min(7, len(patients)-1), format_func=lambda x: f"{x} · demo profile")
    patient_df = df[df.patient_id == chosen_patient].sort_values("timestamp").reset_index(drop=True)
    min_i, max_i = 4, max(4, len(patient_df)-3)
    selected_idx = st.slider("Advance the twin (hour index)", min_value=min_i, max_value=max_i, value=max_i, step=1,
                             help="Changes the observation time. The prediction uses only features available at the selected time.")
    row = patient_df.iloc[selected_idx].copy()
    st.markdown("---")
    st.markdown("### What-if scenario")
    st.caption("Sensitivity analysis only; edits model inputs and is not a physiological simulation.")
    scenario_carbs = st.slider("Carbohydrates logged in last hour (g)", 0, 110, int(row["carbs_last_hour_g"]), 5)
    scenario_steps = st.slider("Steps in last hour", 0, 3000, int(row["steps_last_hour"]), 100)
    scenario_sleep = st.slider("Sleep last night (hours)", 3.5, 10.0, float(row["sleep_hours_last_night"]), 0.5)
    use_scenario = st.checkbox("Apply scenario to forecast", value=False)
    st.markdown("---")
    st.caption("Synthetic data only • research prototype • not a medical device")

model_input = row.copy()
if use_scenario:
    model_input["carbs_last_hour_g"] = float(scenario_carbs)
    model_input["carbs_last_2h_g"] = float(scenario_carbs + max(0, float(row["carbs_last_2h_g"]) - float(row["carbs_last_hour_g"])))
    model_input["steps_last_hour"] = float(scenario_steps)
    model_input["sleep_hours_last_night"] = float(scenario_sleep)
result = predict_row(model_input, bundle)
risk = result["risk"]
current_glucose = float(row["current_glucose_mg_dl"])

c1, c2, c3, c4 = st.columns(4)
def kpi(col, label, value, hint):
    col.markdown(f'<div class="kpi"><div class="label">{label}</div><div class="value">{value}</div><div class="hint">{hint}</div></div>', unsafe_allow_html=True)
kpi(c1, "Current CGM reading", f"{current_glucose:.0f} <span style='font-size:.8rem;font-weight:600'>mg/dL</span>", f"{row['timestamp'].strftime('%d %b %Y · %H:%M')}")
kpi(c2, "2-hour model risk", f"{risk*100:.0f}%", "Estimated probability in synthetic data")
kpi(c3, "Twin health context", f"HbA1c {float(row['hba1c_pct']):.1f}%", f"BMI {float(row['bmi']):.1f} · {float(row['diabetes_duration_years']):.0f} years")
kpi(c4, "Wearable signal", f"{float(row['resting_hr_bpm']):.0f} bpm", f"HRV {float(row['hrv_ms']):.0f} ms · {int(row['steps_last_hour']):,} steps")
st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

left, right = st.columns([1.48, 1])
with left:
    st.markdown('<div class="section">Glucose trajectory · last 24 hours</div>', unsafe_allow_html=True)
    hist = patient_df.iloc[max(0, selected_idx-23):selected_idx+1].copy()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=hist.timestamp, y=hist.current_glucose_mg_dl, mode="lines+markers", name="Synthetic CGM", line=dict(width=3, color="#167d93"), marker=dict(size=5)))
    fig.add_hline(y=180, line_dash="dash", line_color="#e45b55", annotation_text="180 mg/dL event threshold", annotation_position="top left")
    fig.update_layout(height=330, margin=dict(l=5,r=5,t=10,b=5), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="white", font=dict(color="#4a5972"), xaxis_title=None, yaxis_title="Glucose (mg/dL)", legend=dict(orientation="h", y=1.13), xaxis=dict(showgrid=False), yaxis=dict(gridcolor="#edf1f7"))
    st.plotly_chart(fig, use_container_width=True)
with right:
    st.markdown('<div class="section">Forecast & review cue</div>', unsafe_allow_html=True)
    if current_glucose >= 180:
        st.markdown(f'<div class="risk-high"><b>Current elevated reading</b><br>Current synthetic CGM value is already at or above 180 mg/dL. The early-warning score is not the right interpretation for this observation.</div>', unsafe_allow_html=True)
    elif risk >= result["threshold"]:
        st.markdown(f'<div class="risk-high"><b>Review threshold met</b><br>Model estimate is above the validation-selected review threshold. Estimated chance of crossing 180 mg/dL within 2 hours: {risk:.0%}. Prioritise a clinician review of the recent CGM curve and context.</div>', unsafe_allow_html=True)
    elif risk >= 0.70 * result["threshold"]:
        st.markdown(f'<div class="risk-mid"><b>Watchlist</b><br>Model estimate is near the validation-selected review threshold. Estimated chance of a threshold crossing within 2 hours: {risk:.0%}. Review data quality and recent meal/activity context.</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="risk-low"><b>Lower model-estimated risk</b><br>Estimated chance of a threshold crossing within 2 hours: {risk:.0%}. This is not a guarantee that an event will not occur.</div>', unsafe_allow_html=True)
    st.markdown("\n")
    st.write("**Clinician workflow prompt**")
    st.write("1. Confirm CGM signal quality and timestamp alignment.")
    st.write("2. Review recent meal, activity, sleep and historical context.")
    st.write("3. Decide whether follow-up or further assessment is appropriate.")
    st.caption("The prototype does not prescribe medicines, change doses, diagnose diabetes, or replace clinician judgment.")

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
sec1, sec2 = st.columns([1.05, 1.4])
with sec1:
    st.markdown('<div class="section">Historical EHR snapshot</div>', unsafe_allow_html=True)
    ehr = pd.DataFrame([
        ("Age", f"{int(row['age_years'])} years"), ("Sex (simulated)", str(row["sex"])),
        ("BMI", f"{float(row['bmi']):.1f} kg/m²"), ("HbA1c", f"{float(row['hba1c_pct']):.1f}%"),
        ("Diabetes duration", f"{float(row['diabetes_duration_years']):.1f} years"),
        ("Hypertension flag", "Present" if int(row["hypertension"]) else "Not flagged"),
        ("Medication adherence", f"{float(row['medication_adherence']):.0%} (simulated)"),
    ], columns=["EHR field", "Synthetic value"])
    st.dataframe(ehr, hide_index=True, use_container_width=True, height=290)
with sec2:
    st.markdown('<div class="section">What is shaping the model?</div>', unsafe_allow_html=True)
    fi_path = ROOT / "reports" / "feature_importance.csv"
    if fi_path.exists():
        fi = pd.read_csv(fi_path).head(8).sort_values("importance")
        fig2 = px.bar(fi, x="importance", y="feature", orientation="h", labels={"importance":"Model feature importance", "feature":"Input feature"})
        fig2.update_traces(marker_color="#3c92a8")
        fig2.update_layout(height=290, margin=dict(l=5,r=5,t=5,b=5), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="white", font=dict(color="#4a5972"), xaxis=dict(gridcolor="#edf1f7"), yaxis_title=None)
        st.plotly_chart(fig2, use_container_width=True)
    st.caption("Global feature importance shows what the trained model used across training records. It is not a causal explanation for this individual forecast.")

with st.expander("Model evaluation on held-out synthetic patients"):
    st.warning("These metrics are measured on held-out synthetic patient IDs only. They are not estimates of performance on real people or clinical settings.")
    m1,m2,m3,m4 = st.columns(4)
    m1.metric("ROC-AUC", f"{metrics.get('test_roc_auc', 0):.3f}" if metrics.get('test_roc_auc') is not None else "N/A")
    m2.metric("Average precision", f"{metrics.get('test_average_precision', 0):.3f}")
    m3.metric("Recall at threshold", f"{metrics.get('test_recall_at_threshold', 0):.3f}")
    m4.metric("Brier score", f"{metrics.get('test_brier_score', 0):.3f}")
    st.write(f"Patient-level split: {metrics.get('train_patients','?')} train / {metrics.get('validation_patients','?')} validation / {metrics.get('test_patients','?')} test patients. Tuned threshold: {metrics.get('selected_threshold_from_validation_f2','?')}.")

with st.expander("Retrospective ground truth for this synthetic timestamp (demo only)"):
    truth = int(row[TARGET_COLUMN])
    st.write(f"Synthetic outcome label recorded by the simulator: **{'threshold crossing in the next 2 hours' if truth else 'no threshold crossing in the next 2 hours'}**.")
    st.caption("This field exists only for retrospective demonstration and model evaluation. It is not used as a prediction input.")

st.markdown("---")
st.markdown("**Privacy & safety:** All records are generated for this prototype; no real patient data are collected. This is a student research demonstration, not a validated medical device. Do not use its outputs for diagnosis, treatment, or emergency decisions.")
st.markdown("<span class='small-muted'>DigiTech · GlucoTwin India · Digital Twin Challenge 2026</span>", unsafe_allow_html=True)
