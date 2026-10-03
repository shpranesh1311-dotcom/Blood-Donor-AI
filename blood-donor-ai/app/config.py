"""
config.py
=========
Central application configuration, loaded from environment variables
(with sensible defaults for zero-setup local development using SQLite).
"""

import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DB_MODE = os.getenv("DB_MODE", "sqlite").lower()

SQLITE_PATH = os.getenv("SQLITE_PATH", os.path.join(BASE_DIR, "data", "processed", "blood_donor.db"))

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "blood_donor_ai")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")

SECRET_KEY = os.getenv("SECRET_KEY", "demo-secret-key-change-me")

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

MODEL_PATH = os.path.join(BASE_DIR, "models", "trained_model.joblib")
MODEL_METADATA_PATH = os.path.join(BASE_DIR, "models", "model_metadata.json")

DATA_RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
DATA_PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")


def get_database_url() -> str:
    if DB_MODE == "postgresql":
        return (
            f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
            f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
        )
    # default: sqlite (zero setup)
    os.makedirs(os.path.dirname(SQLITE_PATH), exist_ok=True)
    return f"sqlite:///{SQLITE_PATH}"
