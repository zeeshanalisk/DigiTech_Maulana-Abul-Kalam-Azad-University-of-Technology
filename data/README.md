# Synthetic data dictionary

`synthetic_twin_stream.csv` contains 80,160 generated hourly records from 240 artificial patient profiles across 14 days per profile (the final two future steps per trajectory are kept as target context rather than emitted as rows).

| Field | Meaning |
|---|---|
| `patient_id` | Artificial ID such as `GT-0008`; not derived from a real person |
| `timestamp` | Simulated hourly timestamp |
| `age_years`, `sex`, `bmi` | Synthetic demographic/body-profile context |
| `diabetes_duration_years`, `hba1c_pct`, `hypertension` | Synthetic historical EHR-like fields |
| `medication_adherence` | Artificial model input; not a treatment recommendation |
| `current_glucose_mg_dl` | Simulated CGM-like reading at time t |
| `glucose_change_1h_mg_dl`, `glucose_mean_3h_mg_dl`, `glucose_std_3h_mg_dl` | Current/recent glucose summary features |
| `carbs_last_hour_g`, `carbs_last_2h_g` | Simulated meal-log features |
| `steps_last_hour`, `resting_hr_bpm`, `hrv_ms` | Simulated wearable-style features |
| `sleep_hours_last_night`, `sleep_efficiency_pct`, `stress_score` | Simulated contextual signals |
| `hours_since_last_meal` | Simulated elapsed time from last logged meal |
| `future_2h_max_glucose_mg_dl` | Simulator-only outcome reference; excluded from model features |
| `eligible_for_early_warning` | 1 if current synthetic glucose is below 180 mg/dL |
| `new_high_glucose_event_next_2h` | Simulator label: eligible row and either next 1h/2h reading reaches 180 mg/dL |

Regenerate with `python -m src.synthetic_data`. Default seed is 42. Do not interpret this artificial distribution as representative of any population.
