"""Prediction utilities for the patient-specific digital twin UI."""
from __future__ import annotations
from pathlib import Path
import pandas as pd
from joblib import load
from .features import FEATURE_COLUMNS

ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "models" / "glucotwin_model.joblib"


def load_bundle(path: str | Path = MODEL_PATH):
    return load(path)


def predict_row(row: pd.Series | dict, bundle: dict | None = None) -> dict:
    bundle = bundle or load_bundle()
    values = pd.DataFrame([{col: float(row[col]) for col in FEATURE_COLUMNS}])
    model = bundle["model"]
    risk = float(model.predict_proba(values)[0, 1])
    threshold = float(bundle.get("threshold", 0.5))
    return {
        "risk": risk,
        "threshold": threshold,
        "risk_band": "Review threshold met" if risk >= threshold else ("Watchlist" if risk >= 0.70 * threshold else "Below model review threshold"),
        "above_threshold": bool(risk >= threshold),
    }
