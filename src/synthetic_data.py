"""Generate reproducible synthetic EHR + wearable/CGM streams.

All records are artificial. No real patient data are used.
"""
from __future__ import annotations
import numpy as np
import pandas as pd


def generate_dataset(n_patients: int = 240, days: int = 14, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows: list[dict] = []
    start = pd.Timestamp("2026-01-05 00:00:00")
    hours = days * 24
    for p in range(n_patients):
        pid = f"GT-{p + 1:04d}"
        age = int(np.clip(rng.normal(54, 12), 24, 82))
        sex = str(rng.choice(["Female", "Male"], p=[0.51, 0.49]))
        bmi = float(np.clip(rng.normal(28.7, 5.2), 18.0, 44.0))
        duration = float(np.clip(rng.gamma(2.2, 3.0), 0, 24))
        hba1c = float(np.clip(rng.normal(7.4 + 0.025 * max(duration - 8, 0), 1.05), 5.5, 12.0))
        hypertension = int(rng.random() < (0.20 + 0.009 * max(age - 35, 0) + 0.008 * max(bmi - 25, 0)))
        adherence = float(np.clip(rng.beta(7, 2), 0.42, 1.0))
        resting_base = float(np.clip(rng.normal(71 + 0.18 * (bmi - 25), 6), 52, 92))
        hrv_base = float(np.clip(rng.normal(52 - 0.25 * max(age - 40, 0) - 0.25 * max(bmi - 25, 0), 10), 18, 90))
        baseline = float(np.clip(91 + 10.5 * (hba1c - 5.5) + 0.52 * max(bmi - 25, 0) + 0.28 * duration + 3 * hypertension, 95, 172))
        carbs = np.zeros(hours, dtype=float)
        steps = np.zeros(hours, dtype=int)
        heart = np.zeros(hours, dtype=float)
        hrv = np.zeros(hours, dtype=float)
        stress = np.zeros(hours, dtype=float)
        sleep = np.zeros(hours, dtype=float)
        sleep_eff = np.zeros(hours, dtype=float)
        glucose = np.zeros(hours, dtype=float)
        hours_since_meal = np.zeros(hours, dtype=int)
        last_meal_idx = -100
        for t in range(hours):
            stamp = start + pd.Timedelta(hours=t)
            hour = stamp.hour
            # Meal logging: breakfast, lunch, dinner, with occasional snacks.
            meal_prob = 0.66 if hour in [7, 8, 9, 12, 13, 14, 19, 20, 21] else (0.06 if 10 <= hour <= 23 else 0.025)
            if rng.random() < meal_prob:
                if hour in [7, 8, 9]:
                    carbs[t] = float(np.clip(rng.normal(42, 15), 12, 88))
                elif hour in [12, 13, 14]:
                    carbs[t] = float(np.clip(rng.normal(58, 18), 15, 105))
                elif hour in [19, 20, 21]:
                    carbs[t] = float(np.clip(rng.normal(53, 17), 15, 100))
                else:
                    carbs[t] = float(np.clip(rng.normal(18, 8), 5, 42))
                last_meal_idx = t
            hours_since_meal[t] = int(min(t - last_meal_idx, 24)) if last_meal_idx >= 0 else 24
            if 0 <= hour <= 5 or hour >= 23:
                steps[t] = int(rng.poisson(20))
            elif 6 <= hour <= 22:
                lam = 520 if hour in [7, 8, 9, 12, 13, 14, 18, 19, 20] else 370
                steps[t] = int(np.clip(rng.poisson(lam), 0, 2600))
                if rng.random() < 0.05:
                    steps[t] += int(rng.integers(800, 2400))
            daily_sleep = float(np.clip(rng.normal(6.8 - 0.12 * hypertension, 1.05), 3.7, 9.4))
            sleep[t] = daily_sleep
            sleep_eff[t] = float(np.clip(rng.normal(86 - 1.4 * max(6 - daily_sleep, 0), 7), 58, 99))
            stress[t] = float(np.clip(rng.normal(4.4 + 0.2 * hypertension, 2.0), 0, 10))
            heart[t] = float(np.clip(rng.normal(resting_base + 0.010 * steps[t] + 1.05 * stress[t], 4), 48, 145))
            hrv[t] = float(np.clip(rng.normal(hrv_base - 0.22 * (heart[t] - resting_base) - 1.1 * stress[t], 8), 10, 105))
            prev1 = carbs[t - 1] if t >= 1 else 0.0
            prev2 = carbs[t - 2] if t >= 2 else 0.0
            activity_relief = min(steps[t] / 1000.0, 3.0) * 1.5
            adherence_relief = 5.3 * adherence
            circadian = 3.0 if 5 <= hour <= 8 else (1.5 if hour >= 20 else 0.0)
            disturbance = rng.normal(0, 7.0)
            prev_g = glucose[t - 1] if t else baseline + rng.normal(0, 6)
            g = (0.69 * prev_g + 0.31 * baseline + 0.37 * carbs[t] + 0.16 * prev1 + 0.06 * prev2
                 - activity_relief - adherence_relief + 0.55 * stress[t] + circadian + disturbance)
            glucose[t] = float(np.clip(g, 62, 290))
        for t in range(hours - 2):
            stamp = start + pd.Timedelta(hours=t)
            recent = glucose[max(0, t - 2):t + 1]
            current = float(glucose[t])
            g1 = float(glucose[t - 1]) if t > 0 else current
            carbs_1 = float(carbs[t])
            carbs_2 = float(carbs[t] + (carbs[t - 1] if t > 0 else 0))
            future_max = float(max(glucose[t + 1], glucose[t + 2]))
            eligible = int(current < 180)
            event = int(eligible and future_max >= 180)
            rows.append({
                "patient_id": pid,
                "timestamp": stamp.isoformat(),
                "age_years": age,
                "sex": sex,
                "bmi": round(bmi, 1),
                "diabetes_duration_years": round(duration, 1),
                "hba1c_pct": round(hba1c, 2),
                "hypertension": hypertension,
                "medication_adherence": round(adherence, 3),
                "current_glucose_mg_dl": round(current, 1),
                "glucose_change_1h_mg_dl": round(current - g1, 1),
                "glucose_mean_3h_mg_dl": round(float(np.mean(recent)), 1),
                "glucose_std_3h_mg_dl": round(float(np.std(recent)), 1),
                "carbs_last_hour_g": round(carbs_1, 1),
                "carbs_last_2h_g": round(carbs_2, 1),
                "steps_last_hour": int(steps[t]),
                "resting_hr_bpm": round(float(heart[t]), 1),
                "hrv_ms": round(float(hrv[t]), 1),
                "sleep_hours_last_night": round(float(sleep[t]), 1),
                "sleep_efficiency_pct": round(float(sleep_eff[t]), 1),
                "hours_since_last_meal": int(hours_since_meal[t]),
                "stress_score": round(float(stress[t]), 1),
                "future_2h_max_glucose_mg_dl": round(future_max, 1),
                "eligible_for_early_warning": eligible,
                "new_high_glucose_event_next_2h": event,
            })
    df = pd.DataFrame(rows)
    return df


def main() -> None:
    from pathlib import Path
    out = Path(__file__).resolve().parents[1] / "data" / "synthetic_twin_stream.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    df = generate_dataset()
    df.to_csv(out, index=False)
    print(f"Saved {len(df):,} synthetic hourly records to {out}")
    eligible = df[df["eligible_for_early_warning"] == 1]
    print(f"Eligible early-warning rows: {len(eligible):,}; event rate: {eligible['new_high_glucose_event_next_2h'].mean():.3f}")

if __name__ == "__main__":
    main()
