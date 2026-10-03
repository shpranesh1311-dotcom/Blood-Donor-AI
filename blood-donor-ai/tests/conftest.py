"""
conftest.py
===========
Shared pytest fixtures. Configures an isolated SQLite test database (never
touches the developer's real data/processed/blood_donor.db) BEFORE any
`app.*` module is imported, then exposes a ready-to-use FastAPI TestClient.
"""

import os
import sys
import tempfile

import pytest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

# --- Point the app at a throwaway SQLite file for the whole test session ---
_TEST_DB_FD, _TEST_DB_PATH = tempfile.mkstemp(suffix=".db")
os.close(_TEST_DB_FD)
os.environ["DB_MODE"] = "sqlite"
os.environ["SQLITE_PATH"] = _TEST_DB_PATH

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


def pytest_sessionfinish(session, exitstatus):
    try:
        os.remove(_TEST_DB_PATH)
    except OSError:
        pass
