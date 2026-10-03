"""
seed.py
=======
Loads the synthetic CSV data (data/raw/*.csv, produced by
ml/generate_dataset.py) into the application database. Runs automatically
on application startup if the donors table is empty, so a beginner just
needs to run the dataset generator once and then start the app.

Also creates the default demo admin account (see .env / app/config.py)
if no admin user exists yet.
"""

import os
import pandas as pd
from sqlalchemy.orm import Session

from app import config
from app.models.db_models import Donor, DonationHistory, EmergencyRequest, DonorResponse, AdminUser
from app.utils.security import hash_password


def _csv_path(name: str) -> str:
    return os.path.join(config.DATA_RAW_DIR, name)


def seed_if_empty(db: Session):
    donor_count = db.query(Donor).count()
    if donor_count == 0:
        _seed_donors(db)
        _seed_donation_history(db)
        _seed_requests(db)
        _seed_responses(db)
        db.commit()
        print(f"[seed] Loaded synthetic demo data into the database.")
    else:
        print(f"[seed] Database already has {donor_count:,} donors - skipping data seed.")

    _ensure_admin_user(db)


def _seed_donors(db: Session):
    path = _csv_path("donors.csv")
    if not os.path.exists(path):
        print(f"[seed] WARNING: {path} not found. Run `python ml/generate_dataset.py` first.")
        return
    df = pd.read_csv(path)
    objs = [
        Donor(
            donor_id=row["donor_id"],
            name=row["name"],
            age=int(row["age"]),
            gender=row["gender"],
            blood_group=row["blood_group"],
            city=row["city"],
            latitude=float(row["latitude"]),
            longitude=float(row["longitude"]),
            last_donation_date=str(row["last_donation_date"]) if pd.notna(row["last_donation_date"]) else None,
            total_donations=int(row["total_donations"]),
            previous_requests_received=int(row["previous_requests_received"]),
            previous_requests_responded=int(row["previous_requests_responded"]),
            average_response_time_minutes=float(row["average_response_time_minutes"]),
            availability_preference=row["availability_preference"],
            current_availability=bool(row["current_availability"]),
            donor_status=row["donor_status"],
        )
        for _, row in df.iterrows()
    ]
    db.bulk_save_objects(objs)
    print(f"[seed] Inserted {len(objs):,} donors.")


def _seed_donation_history(db: Session):
    path = _csv_path("donation_history.csv")
    if not os.path.exists(path):
        return
    df = pd.read_csv(path)
    objs = [
        DonationHistory(
            donation_id=row["donation_id"],
            donor_id=row["donor_id"],
            donation_date=row["donation_date"],
            donation_status=row["donation_status"],
            response_time_minutes=float(row["response_time_minutes"]) if pd.notna(row["response_time_minutes"]) else None,
        )
        for _, row in df.iterrows()
    ]
    db.bulk_save_objects(objs)
    print(f"[seed] Inserted {len(objs):,} donation history records.")


def _seed_requests(db: Session):
    path = _csv_path("emergency_requests.csv")
    if not os.path.exists(path):
        return
    df = pd.read_csv(path)
    objs = [
        EmergencyRequest(
            request_id=row["request_id"],
            blood_group_required=row["blood_group_required"],
            units_required=int(row["units_required"]),
            urgency_level=row["urgency_level"],
            hospital_area=row["hospital_area"],
            latitude=float(row["latitude"]),
            longitude=float(row["longitude"]),
            request_datetime=row["request_datetime"],
            request_status=row["request_status"],
        )
        for _, row in df.iterrows()
    ]
    db.bulk_save_objects(objs)
    print(f"[seed] Inserted {len(objs):,} historical emergency requests.")


def _seed_responses(db: Session):
    path = _csv_path("donor_response_history.csv")
    if not os.path.exists(path):
        return
    df = pd.read_csv(path)
    objs = [
        DonorResponse(
            request_id=row["request_id"],
            donor_id=row["donor_id"],
            distance_km=float(row["distance_km"]) if pd.notna(row["distance_km"]) else None,
            response=bool(row["response"]),
            response_time_minutes=float(row["response_time_minutes"]) if pd.notna(row["response_time_minutes"]) and row["response_time_minutes"] != "" else None,
            timestamp=row["timestamp"],
            will_respond=int(row["will_respond"]),
        )
        for _, row in df.iterrows()
    ]
    db.bulk_save_objects(objs)
    print(f"[seed] Inserted {len(objs):,} donor response history records.")


def _ensure_admin_user(db: Session):
    existing = db.query(AdminUser).filter(AdminUser.username == config.ADMIN_USERNAME).first()
    if existing is None:
        admin = AdminUser(
            username=config.ADMIN_USERNAME,
            hashed_password=hash_password(config.ADMIN_PASSWORD),
        )
        db.add(admin)
        db.commit()
        print(f"[seed] Created default demo admin user '{config.ADMIN_USERNAME}'.")
