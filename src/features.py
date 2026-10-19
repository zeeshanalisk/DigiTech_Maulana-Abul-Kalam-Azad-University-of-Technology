"""Shared feature contract for the GlucoTwin forecasting model."""
FEATURE_COLUMNS = [
    "age_years",
    "bmi",
    "diabetes_duration_years",
    "hba1c_pct",
    "hypertension",
    "medication_adherence",
    "current_glucose_mg_dl",
    "glucose_change_1h_mg_dl",
    "glucose_mean_3h_mg_dl",
    "glucose_std_3h_mg_dl",
    "carbs_last_hour_g",
    "carbs_last_2h_g",
    "steps_last_hour",
    "resting_hr_bpm",
    "hrv_ms",
    "sleep_hours_last_night",
    "sleep_efficiency_pct",
    "hours_since_last_meal",
    "stress_score",
]
TARGET_COLUMN = "new_high_glucose_event_next_2h"
PATIENT_COLUMN = "patient_id"
