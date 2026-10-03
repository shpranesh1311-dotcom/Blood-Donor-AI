"""
generate_dataset.py
====================
Generates a fully SYNTHETIC / FICTIONAL dataset for the
AI-Based Blood Donor Availability Prediction and Intelligent Matching System.

IMPORTANT:
    - Every donor name, location, id and history record produced by this
      script is randomly generated. None of it refers to real people.
    - This script is reproducible: running it twice with the same code
      produces the same data because a fixed random seed is used.

Outputs (written to data/raw/):
    donors.csv
    donation_history.csv
    emergency_requests.csv
    donor_response_history.csv

Usage:
    python ml/generate_dataset.py
    python ml/generate_dataset.py --donors 8000 --requests 1500
"""

import argparse
import os
import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

SEED = 42
random.seed(SEED)
np.random.seed(SEED)

BLOOD_GROUPS = ["O+", "O-", "A+", "A-", "B+", "B-", "AB+", "AB-"]
# Roughly realistic population distribution (India-weighted, for demo realism only)
BLOOD_GROUP_WEIGHTS = [0.34, 0.08, 0.22, 0.07, 0.11, 0.03, 0.04, 0.01]
_w_sum = sum(BLOOD_GROUP_WEIGHTS)
BLOOD_GROUP_WEIGHTS = [w / _w_sum for w in BLOOD_GROUP_WEIGHTS]

# Fictional Coimbatore-area style cities/areas (demo geography only)
CITIES = [
    ("Coimbatore Central", 11.0016, 76.9558),
    ("Peelamedu", 11.0296, 77.0266),
    ("Saibaba Colony", 11.0189, 76.9463),
    ("RS Puram", 11.0060, 76.9520),
    ("Gandhipuram", 11.0175, 76.9674),
    ("Singanallur", 11.0006, 77.0290),
    ("Ukkadam", 10.9887, 76.9600),
    ("Vadavalli", 11.0224, 76.9130),
    ("Podanur", 10.9530, 76.9670),
    ("Kalapatti", 11.0680, 77.0430),
]

FIRST_NAMES = [
    "Arjun", "Priya", "Vijay", "Divya", "Karthik", "Meena", "Suresh", "Anitha",
    "Ramesh", "Lakshmi", "Sathish", "Kavya", "Prakash", "Deepa", "Manoj", "Swathi",
    "Ganesh", "Revathi", "Naveen", "Pooja", "Senthil", "Bhavani", "Dinesh", "Nithya",
    "Arun", "Sandhya", "Vikram", "Roja", "Muthu", "Geetha",
]
LAST_NAMES = [
    "Kumar", "Raj", "Krishnan", "Moorthy", "Iyer", "Pillai", "Nair", "Reddy",
    "Sharma", "Gowda", "Chandran", "Subramani", "Rajan", "Balan", "Menon",
]

DONOR_STATUS = ["active", "inactive", "suspended"]
AVAILABILITY_PREF = ["anytime", "weekdays", "weekends", "emergency_only"]


def fake_name(rng):
    return f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"


def jitter_coords(lat, lon, rng, spread=0.03):
    return round(lat + rng.uniform(-spread, spread), 6), round(lon + rng.uniform(-spread, spread), 6)


def random_date_within(days_back, rng):
    return datetime.now() - timedelta(days=int(rng.integers(0, days_back)))


def generate_donors(n_donors, rng):
    rows = []
    for i in range(1, n_donors + 1):
        donor_id = f"D{i:05d}"
        age = int(np.clip(rng.normal(32, 9), 18, 65))
        gender = rng.choice(["M", "F", "Other"], p=[0.55, 0.43, 0.02])
        blood_group = rng.choice(BLOOD_GROUPS, p=BLOOD_GROUP_WEIGHTS)
        city_name, base_lat, base_lon = CITIES[rng.integers(0, len(CITIES))]
        lat, lon = jitter_coords(base_lat, base_lon, rng)

        total_donations = int(np.clip(rng.poisson(4), 0, 40))
        # last donation date correlates loosely with total_donations
        if total_donations == 0:
            last_donation_date = ""
        else:
            days_back = int(rng.integers(15, 900))
            last_donation_date = (datetime.now() - timedelta(days=days_back)).date().isoformat()

        previous_requests_received = int(np.clip(total_donations + rng.integers(0, 6), 0, 60))
        # response propensity - a hidden "true" trait used to generate realistic behaviour
        base_response_propensity = np.clip(rng.beta(2.2, 2.0), 0, 1)
        previous_requests_responded = int(
            np.clip(rng.binomial(previous_requests_received, base_response_propensity)
                    if previous_requests_received > 0 else 0, 0, previous_requests_received)
        )

        avg_response_time = float(np.clip(rng.normal(60 - base_response_propensity * 30, 20), 5, 240))
        availability_preference = rng.choice(AVAILABILITY_PREF, p=[0.4, 0.25, 0.2, 0.15])
        current_availability = int(rng.random() < (0.55 + 0.2 * base_response_propensity))
        donor_status = rng.choice(DONOR_STATUS, p=[0.86, 0.11, 0.03])

        rows.append({
            "donor_id": donor_id,
            "name": fake_name(rng),  # fictional name, demo only
            "age": age,
            "gender": gender,
            "blood_group": blood_group,
            "city": city_name,
            "latitude": lat,
            "longitude": lon,
            "last_donation_date": last_donation_date,
            "total_donations": total_donations,
            "previous_requests_received": previous_requests_received,
            "previous_requests_responded": previous_requests_responded,
            "average_response_time_minutes": round(avg_response_time, 1),
            "availability_preference": availability_preference,
            "current_availability": current_availability,
            "donor_status": donor_status,
            "_response_propensity": round(float(base_response_propensity), 4),  # hidden trait, kept for realism
        })
    return pd.DataFrame(rows)


def generate_donation_history(donors_df, rng):
    rows = []
    donation_counter = 1
    for _, d in donors_df.iterrows():
        n = int(d["total_donations"])
        for _ in range(n):
            donation_id = f"DON{donation_counter:06d}"
            donation_counter += 1
            days_back = int(rng.integers(10, 1000))
            donation_date = (datetime.now() - timedelta(days=days_back)).date().isoformat()
            status = rng.choice(["completed", "deferred", "cancelled"], p=[0.9, 0.07, 0.03])
            response_time = float(np.clip(rng.normal(d["average_response_time_minutes"], 15), 5, 300))
            rows.append({
                "donation_id": donation_id,
                "donor_id": d["donor_id"],
                "donation_date": donation_date,
                "donation_status": status,
                "response_time_minutes": round(response_time, 1),
            })
    return pd.DataFrame(rows)


def generate_emergency_requests(n_requests, rng):
    rows = []
    for i in range(1, n_requests + 1):
        request_id = f"REQ{i:05d}"
        blood_group = rng.choice(BLOOD_GROUPS, p=BLOOD_GROUP_WEIGHTS)
        units_required = int(rng.integers(1, 6))
        urgency = rng.choice(["Critical", "High", "Medium", "Low"], p=[0.15, 0.30, 0.35, 0.20])
        city_name, base_lat, base_lon = CITIES[rng.integers(0, len(CITIES))]
        lat, lon = jitter_coords(base_lat, base_lon, rng, spread=0.015)
        days_back = int(rng.integers(0, 365))
        hours_back = int(rng.integers(0, 24))
        request_datetime = datetime.now() - timedelta(days=days_back, hours=hours_back)
        status = rng.choice(["fulfilled", "partially_fulfilled", "unfulfilled", "cancelled"],
                             p=[0.55, 0.2, 0.15, 0.10])
        rows.append({
            "request_id": request_id,
            "blood_group_required": blood_group,
            "units_required": units_required,
            "urgency_level": urgency,
            "hospital_area": city_name,
            "latitude": lat,
            "longitude": lon,
            "request_datetime": request_datetime.isoformat(timespec="minutes"),
            "request_status": status,
        })
    return pd.DataFrame(rows)


COMPATIBLE_DONORS = {
    "O-": ["O-"],
    "O+": ["O-", "O+"],
    "A-": ["O-", "A-"],
    "A+": ["O-", "O+", "A-", "A+"],
    "B-": ["O-", "B-"],
    "B+": ["O-", "O+", "B-", "B+"],
    "AB-": ["O-", "A-", "B-", "AB-"],
    "AB+": ["O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"],
}


def generate_donor_response_history(requests_df, donors_df, rng, max_candidates_per_request=25):
    """
    For every emergency request, sample a handful of blood-compatible donors
    and simulate whether they responded. The simulated response also becomes
    the ML label 'will_respond' used for training.
    """
    donors_by_group = {bg: donors_df[donors_df["blood_group"] == bg] for bg in BLOOD_GROUPS}
    rows = []

    for _, req in requests_df.iterrows():
        compatible_groups = COMPATIBLE_DONORS[req["blood_group_required"]]
        candidate_pool = pd.concat([donors_by_group[g] for g in compatible_groups if g in donors_by_group])
        candidate_pool = candidate_pool[candidate_pool["donor_status"] == "active"]
        if candidate_pool.empty:
            continue

        n_candidates = min(max_candidates_per_request, len(candidate_pool))
        sampled = candidate_pool.sample(n=n_candidates, random_state=int(rng.integers(0, 1_000_000)))

        req_time = pd.to_datetime(req["request_datetime"])
        urgency_boost = {"Critical": 0.18, "High": 0.10, "Medium": 0.0, "Low": -0.08}[req["urgency_level"]]

        for _, donor in sampled.iterrows():
            # distance factor (rough haversine-free approximation is fine for synthetic data)
            dist_km = haversine_km(req["latitude"], req["longitude"], donor["latitude"], donor["longitude"])
            distance_factor = max(0, 0.25 - dist_km * 0.01)

            availability_factor = 0.12 if donor["current_availability"] else -0.15
            propensity = donor["_response_propensity"]

            response_prob = np.clip(
                propensity + urgency_boost + distance_factor + availability_factor
                + rng.normal(0, 0.08),
                0.02, 0.98,
            )
            responded = int(rng.random() < response_prob)
            response_time = float(np.clip(
                rng.normal(donor["average_response_time_minutes"] * (1.3 - propensity * 0.4), 20),
                5, 300,
            )) if responded else None

            rows.append({
                "request_id": req["request_id"],
                "donor_id": donor["donor_id"],
                "distance_km": round(dist_km, 2),
                "response": responded,
                "response_time_minutes": round(response_time, 1) if response_time is not None else "",
                "timestamp": (req_time + timedelta(minutes=int(rng.integers(1, 180)))).isoformat(timespec="minutes"),
                "will_respond": responded,  # ML target label
            })
    return pd.DataFrame(rows)


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    c = 2 * np.arcsin(np.sqrt(a))
    return R * c


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic blood donor dataset (DEMO DATA ONLY).")
    parser.add_argument("--donors", type=int, default=6000, help="Number of synthetic donors to generate")
    parser.add_argument("--requests", type=int, default=1200, help="Number of synthetic emergency requests")
    parser.add_argument("--outdir", type=str, default=None, help="Output directory for CSV files")
    args = parser.parse_args()

    rng = np.random.default_rng(SEED)

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    outdir = args.outdir or os.path.join(base_dir, "data", "raw")
    os.makedirs(outdir, exist_ok=True)

    print(f"[1/4] Generating {args.donors} synthetic donors ...")
    donors_df = generate_donors(args.donors, rng)

    print("[2/4] Generating donation history ...")
    donation_history_df = generate_donation_history(donors_df, rng)

    print(f"[3/4] Generating {args.requests} synthetic emergency requests ...")
    requests_df = generate_emergency_requests(args.requests, rng)

    print("[4/4] Simulating donor responses to requests (this creates the ML training labels) ...")
    response_history_df = generate_donor_response_history(requests_df, donors_df, rng)

    # Drop the hidden trait column before saving donors.csv (it is only used internally
    # to make the simulation behave realistically - it is not a real-world feature).
    donors_out = donors_df.drop(columns=["_response_propensity"])

    donors_out.to_csv(os.path.join(outdir, "donors.csv"), index=False)
    donation_history_df.to_csv(os.path.join(outdir, "donation_history.csv"), index=False)
    requests_df.to_csv(os.path.join(outdir, "emergency_requests.csv"), index=False)
    response_history_df.to_csv(os.path.join(outdir, "donor_response_history.csv"), index=False)

    print("\n=== SYNTHETIC / DEMO DATA GENERATED (NOT REAL PEOPLE) ===")
    print(f"  donors.csv                 -> {len(donors_out):,} rows")
    print(f"  donation_history.csv       -> {len(donation_history_df):,} rows")
    print(f"  emergency_requests.csv     -> {len(requests_df):,} rows")
    print(f"  donor_response_history.csv -> {len(response_history_df):,} rows")
    print(f"Saved to: {outdir}")


if __name__ == "__main__":
    main()
