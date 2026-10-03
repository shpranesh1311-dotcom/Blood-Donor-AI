"""
train.py
========
Complete ML training pipeline for the Blood Donor AI system.

Steps:
    1. Load dataset (donors.csv, emergency_requests.csv, donor_response_history.csv)
    2. Clean data / handle missing values
    3. Feature engineering (see features.py - shared with inference)
    4. Train/test split (stratified, because the label is imbalanced)
    5. Train baseline models: Logistic Regression, Random Forest, XGBoost
    6. Evaluate with Accuracy, Precision, Recall, F1, ROC-AUC, confusion matrix
    7. Select best model by ROC-AUC (NOT raw accuracy - see note below)
    8. Calibrate probabilities of the winning model
    9. Save the trained pipeline with joblib + a metadata JSON file

WHY NOT OPTIMIZE FOR ACCURACY ALONE?
-------------------------------------
Whether a donor responds to a given emergency request is a fairly
imbalanced outcome (most sampled donor/request pairs do NOT result in a
response). A model that always predicts "will not respond" could still
reach high accuracy while being useless - it would never surface a
single usable candidate. For a matching/ranking system we care much
more about:
    - Recall on the positive class: are we missing donors who would
      actually have responded (and could have saved time in an emergency)?
    - Precision: when we say "likely to respond", is that trustworthy
      enough that a coordinator should prioritise contacting this donor?
    - ROC-AUC: how well the model ranks positives above negatives across
      ALL thresholds - which is exactly what our ranking module needs,
      since it uses the probability score directly rather than a single
      cutoff.
    - Calibration: because the ranking formula (services/ranking.py)
      treats the model's output as a genuine probability and blends it
      with other 0-1 factors, a well-calibrated probability (not just a
      well-ordered score) makes the combined ranking more meaningful.

Usage:
    python ml/train.py
"""

import json
import os
import sys
import warnings

import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, BASE_DIR)

from ml.features import FEATURE_COLUMNS, build_feature_row, safe_response_rate  # noqa: E402

RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
MODELS_DIR = os.path.join(BASE_DIR, "models")
os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)

SEED = 42


def load_and_join():
    donors = pd.read_csv(os.path.join(RAW_DIR, "donors.csv"))
    requests = pd.read_csv(os.path.join(RAW_DIR, "emergency_requests.csv"))
    responses = pd.read_csv(os.path.join(RAW_DIR, "donor_response_history.csv"))

    # --- Clean / handle missing values ---
    donors["last_donation_date"] = donors["last_donation_date"].fillna("")
    donors["current_availability"] = donors["current_availability"].fillna(0).astype(int)
    responses["response_time_minutes"] = pd.to_numeric(
        responses["response_time_minutes"], errors="coerce"
    )

    merged = responses.merge(donors, on="donor_id", how="left", suffixes=("", "_donor"))
    merged = merged.merge(requests, on="request_id", how="left", suffixes=("", "_request"))

    merged = merged.dropna(subset=["age", "blood_group", "urgency_level", "distance_km"])
    return merged


def engineer_features(merged: pd.DataFrame):
    raw_rows = []
    for _, r in merged.iterrows():
        req_dt = pd.to_datetime(r["request_datetime"], errors="coerce")
        raw_rows.append({
            "age": r["age"],
            "blood_group": r["blood_group"],
            "total_donations": r["total_donations"],
            "previous_requests_received": r["previous_requests_received"],
            "previous_requests_responded": r["previous_requests_responded"],
            "average_response_time_minutes": r["average_response_time_minutes"],
            "current_availability": r["current_availability"],
            "distance_km": r["distance_km"],
            "urgency_level": r["urgency_level"],
            "units_required": r["units_required"],
            "hour_of_day": req_dt.hour if pd.notnull(req_dt) else 12,
            "day_of_week": req_dt.dayofweek if pd.notnull(req_dt) else 0,
        })
    X = pd.DataFrame([build_feature_row(row) for row in raw_rows])[FEATURE_COLUMNS]
    y = merged["will_respond"].astype(int).reset_index(drop=True)
    return X, y


def evaluate_model(name, model, X_test, y_test):
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]

    metrics = {
        "model": name,
        "accuracy": round(accuracy_score(y_test, y_pred), 4),
        "precision": round(precision_score(y_test, y_pred, zero_division=0), 4),
        "recall": round(recall_score(y_test, y_pred, zero_division=0), 4),
        "f1_score": round(f1_score(y_test, y_pred, zero_division=0), 4),
        "roc_auc": round(roc_auc_score(y_test, y_proba), 4),
        "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
    }
    print(f"\n--- {name} ---")
    for k in ["accuracy", "precision", "recall", "f1_score", "roc_auc"]:
        print(f"  {k:10s}: {metrics[k]}")
    print(f"  confusion_matrix (rows=actual, cols=predicted):\n{np.array(metrics['confusion_matrix'])}")
    print(classification_report(y_test, y_pred, zero_division=0))
    return metrics


def main():
    print("[1/7] Loading and joining raw CSVs ...")
    merged = load_and_join()
    print(f"  -> {len(merged):,} donor-response training rows")

    print("[2/7] Feature engineering ...")
    X, y = engineer_features(merged)
    print(f"  -> feature matrix shape: {X.shape}")
    print(f"  -> class distribution:\n{y.value_counts(normalize=True).rename('proportion')}")

    print("[3/7] Train/test split (stratified, 80/20) ...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=SEED, stratify=y
    )

    print("[4/7] Training baseline models ...")
    candidates = {}

    log_reg = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", LogisticRegression(max_iter=1000, class_weight="balanced", random_state=SEED)),
    ])
    log_reg.fit(X_train, y_train)
    candidates["LogisticRegression"] = log_reg

    rf = RandomForestClassifier(
        n_estimators=300, max_depth=10, min_samples_leaf=5,
        class_weight="balanced", random_state=SEED, n_jobs=-1,
    )
    rf.fit(X_train, y_train)
    candidates["RandomForest"] = rf

    try:
        from xgboost import XGBClassifier
        pos = y_train.sum()
        neg = len(y_train) - pos
        scale_pos_weight = (neg / pos) if pos > 0 else 1.0
        xgb = XGBClassifier(
            n_estimators=300, max_depth=5, learning_rate=0.08,
            subsample=0.9, colsample_bytree=0.9,
            scale_pos_weight=scale_pos_weight, eval_metric="logloss",
            random_state=SEED, n_jobs=-1,
        )
        xgb.fit(X_train, y_train)
        candidates["XGBoost"] = xgb
    except ImportError:
        print("  (xgboost not installed - skipping XGBoost candidate)")

    print("[5/7] Evaluating all candidates ...")
    all_metrics = []
    for name, model in candidates.items():
        all_metrics.append(evaluate_model(name, model, X_test, y_test))

    best = max(all_metrics, key=lambda m: m["roc_auc"])
    best_name = best["model"]
    best_model = candidates[best_name]
    print(f"\n[6/7] Best model selected by ROC-AUC: {best_name} (ROC-AUC={best['roc_auc']})")

    print("      Calibrating probabilities of the best model (sigmoid/Platt scaling) ...")
    calibrated = CalibratedClassifierCV(best_model, method="sigmoid", cv=3)
    calibrated.fit(X_train, y_train)
    calibrated_metrics = evaluate_model(f"{best_name} (calibrated)", calibrated, X_test, y_test)

    print("[7/7] Saving trained model + metadata ...")
    model_path = os.path.join(MODELS_DIR, "trained_model.joblib")
    joblib.dump(calibrated, model_path)

    metadata = {
        "best_model_name": best_name,
        "feature_columns": FEATURE_COLUMNS,
        "training_rows": int(len(X_train)),
        "test_rows": int(len(X_test)),
        "class_distribution": y.value_counts(normalize=True).round(4).to_dict(),
        "all_candidate_metrics": all_metrics,
        "calibrated_metrics": calibrated_metrics,
        "random_seed": SEED,
        "notes": (
            "Model predicts the PROBABILITY that a donor responds to an emergency "
            "request. This is a probabilistic estimate for prioritisation/assistance "
            "only - it does not guarantee donor behaviour and does not replace human "
            "judgement by hospital staff or the blood bank."
        ),
    }
    with open(os.path.join(MODELS_DIR, "model_metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"\nSaved model  -> {model_path}")
    print(f"Saved metadata -> {os.path.join(MODELS_DIR, 'model_metadata.json')}")
    print("\nDone. You can now run: python run.py")


if __name__ == "__main__":
    main()
