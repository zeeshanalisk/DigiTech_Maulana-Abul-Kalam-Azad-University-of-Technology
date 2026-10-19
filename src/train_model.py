"""Train and evaluate a patient-grouped two-hour glucose excursion model."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
from joblib import dump
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.metrics import (roc_auc_score, average_precision_score, brier_score_loss,
    precision_score, recall_score, f1_score, accuracy_score, confusion_matrix, fbeta_score)
from sklearn.model_selection import train_test_split
from .features import FEATURE_COLUMNS, TARGET_COLUMN
from .synthetic_data import generate_dataset

ROOT = Path(__file__).resolve().parents[1]


def train_pipeline(data_path: str | Path | None = None, seed: int = 42) -> dict:
    data_file = Path(data_path) if data_path else ROOT / "data" / "synthetic_twin_stream.csv"
    if data_file.exists():
        df = pd.read_csv(data_file)
    else:
        df = generate_dataset(seed=seed)
        data_file.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(data_file, index=False)
    eligible = df.loc[df["eligible_for_early_warning"] == 1].copy()
    eligible[TARGET_COLUMN] = eligible[TARGET_COLUMN].astype(int)
    # Patient-level partition: a patient's measurements cannot appear in both train and holdout.
    unique_ids = np.array(sorted(eligible["patient_id"].unique()))
    trainval_ids, test_ids = train_test_split(unique_ids, test_size=0.20, random_state=seed, shuffle=True)
    train_ids, val_ids = train_test_split(trainval_ids, test_size=0.20, random_state=seed + 1, shuffle=True)
    train = eligible[eligible.patient_id.isin(train_ids)]
    val = eligible[eligible.patient_id.isin(val_ids)]
    test = eligible[eligible.patient_id.isin(test_ids)]
    model = ExtraTreesClassifier(
        n_estimators=180, max_depth=16, min_samples_leaf=10, max_features=0.9,
        class_weight=None, random_state=seed, n_jobs=-1
    )
    model.fit(train[FEATURE_COLUMNS], train[TARGET_COLUMN])
    val_prob = model.predict_proba(val[FEATURE_COLUMNS])[:, 1]
    thresholds = np.arange(0.10, 0.801, 0.01)
    threshold_scores = [fbeta_score(val[TARGET_COLUMN], val_prob >= th, beta=2, zero_division=0) for th in thresholds]
    threshold = float(thresholds[int(np.argmax(threshold_scores))])
    test_prob = model.predict_proba(test[FEATURE_COLUMNS])[:, 1]
    test_pred = (test_prob >= threshold).astype(int)
    auc = float(roc_auc_score(test[TARGET_COLUMN], test_prob)) if test[TARGET_COLUMN].nunique() > 1 else None
    ap = float(average_precision_score(test[TARGET_COLUMN], test_prob))
    metrics = {
        "project": "GlucoTwin India",
        "task": "Predict whether a synthetic glucose reading crosses 180 mg/dL within the next 2 hours, among rows currently below 180 mg/dL.",
        "data_type": "Fully synthetic; generated deterministically with seed 42 by default.",
        "seed": seed,
        "patients_total": int(df.patient_id.nunique()),
        "records_total": int(len(df)),
        "eligible_records": int(len(eligible)),
        "event_rate_eligible_all": round(float(eligible[TARGET_COLUMN].mean()), 4),
        "train_patients": int(len(train_ids)),
        "validation_patients": int(len(val_ids)),
        "test_patients": int(len(test_ids)),
        "train_records": int(len(train)),
        "validation_records": int(len(val)),
        "test_records": int(len(test)),
        "selected_threshold_from_validation_f2": round(threshold, 3),
        "test_roc_auc": round(auc, 4) if auc is not None else None,
        "test_average_precision": round(ap, 4),
        "test_brier_score": round(float(brier_score_loss(test[TARGET_COLUMN], test_prob)), 4),
        "test_accuracy_at_threshold": round(float(accuracy_score(test[TARGET_COLUMN], test_pred)), 4),
        "test_precision_at_threshold": round(float(precision_score(test[TARGET_COLUMN], test_pred, zero_division=0)), 4),
        "test_recall_at_threshold": round(float(recall_score(test[TARGET_COLUMN], test_pred, zero_division=0)), 4),
        "test_f1_at_threshold": round(float(f1_score(test[TARGET_COLUMN], test_pred, zero_division=0)), 4),
        "test_f2_at_threshold": round(float(fbeta_score(test[TARGET_COLUMN], test_pred, beta=2, zero_division=0)), 4),
        "test_confusion_matrix_tn_fp_fn_tp": confusion_matrix(test[TARGET_COLUMN], test_pred, labels=[0,1]).ravel().tolist(),
        "feature_columns": FEATURE_COLUMNS,
        "important_limitations": [
            "Metrics describe an artificial simulator, not real-world clinical accuracy.",
            "No prospective, external, or clinical validation has been performed.",
            "Risk output is for research/demo triage only and must not guide diagnosis or treatment."
        ]
    }
    model_bundle = {
        "model": model,
        "feature_columns": FEATURE_COLUMNS,
        "threshold": threshold,
        "model_name": "ExtraTreesClassifier",
        "target_name": TARGET_COLUMN,
        "seed": seed,
    }
    (ROOT / "models").mkdir(exist_ok=True)
    (ROOT / "reports").mkdir(exist_ok=True)
    dump(model_bundle, ROOT / "models" / "glucotwin_model.joblib", compress=3)
    with (ROOT / "reports" / "model_evaluation.json").open("w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    fi = pd.DataFrame({"feature": FEATURE_COLUMNS, "importance": model.feature_importances_}).sort_values("importance", ascending=False)
    fi.to_csv(ROOT / "reports" / "feature_importance.csv", index=False)
    test_out = test[["patient_id", "timestamp", TARGET_COLUMN]].copy()
    test_out["predicted_risk"] = test_prob
    test_out["predicted_event_at_tuned_threshold"] = test_pred
    test_out.to_csv(ROOT / "reports" / "heldout_patient_predictions.csv", index=False)
    print(json.dumps(metrics, indent=2))
    return metrics

if __name__ == "__main__":
    train_pipeline()
