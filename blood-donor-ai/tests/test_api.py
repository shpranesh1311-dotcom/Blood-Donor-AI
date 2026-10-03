"""
Integration tests for the FastAPI endpoints, using an isolated in-memory
test database (see conftest.py). These exercise the full request/response
cycle: donors, requests, matching, prediction, dashboard, and error handling.
"""

import os
import pytest
from ml import predict as predict_module

MODEL_AVAILABLE = os.path.exists(predict_module.MODEL_PATH)


def test_blood_groups_endpoint(client):
    res = client.get("/api/blood-groups")
    assert res.status_code == 200
    assert "O+" in res.json()["blood_groups"]


def test_list_donors_default(client):
    res = client.get("/api/donors?limit=5")
    assert res.status_code == 200
    donors = res.json()
    assert isinstance(donors, list)
    assert len(donors) <= 5


def test_list_donors_invalid_blood_group(client):
    res = client.get("/api/donors?blood_group=ZZ")
    assert res.status_code == 400
    assert "error" in res.json()


def test_get_donor_not_found(client):
    res = client.get("/api/donors/D99999999")
    assert res.status_code == 404


def test_create_and_fetch_request(client):
    payload = {
        "blood_group_required": "B+",
        "units_required": 2,
        "urgency_level": "High",
        "hospital_area": "Test Hospital",
        "latitude": 11.0016,
        "longitude": 76.9558,
    }
    res = client.post("/api/requests", json=payload)
    assert res.status_code == 201
    created = res.json()
    assert created["blood_group_required"] == "B+"
    assert created["request_status"] == "pending"

    fetch = client.get(f"/api/requests/{created['request_id']}")
    assert fetch.status_code == 200
    assert fetch.json()["request_id"] == created["request_id"]


def test_create_request_invalid_blood_group(client):
    payload = {
        "blood_group_required": "ZZ", "units_required": 1, "urgency_level": "High",
        "hospital_area": "Test", "latitude": 11.0, "longitude": 77.0,
    }
    res = client.post("/api/requests", json=payload)
    assert res.status_code == 422


def test_create_request_invalid_coordinates(client):
    payload = {
        "blood_group_required": "O+", "units_required": 1, "urgency_level": "High",
        "hospital_area": "Test", "latitude": 999, "longitude": 77.0,
    }
    res = client.post("/api/requests", json=payload)
    assert res.status_code == 422


def test_match_on_nonexistent_request_returns_404(client):
    res = client.post("/api/match/REQ_DOES_NOT_EXIST")
    assert res.status_code == 404


@pytest.mark.skipif(not MODEL_AVAILABLE, reason="Trained model not found - run `python ml/train.py` first")
def test_full_match_flow(client):
    payload = {
        "blood_group_required": "O+", "units_required": 2, "urgency_level": "Critical",
        "hospital_area": "Test Hospital", "latitude": 11.0016, "longitude": 76.9558,
    }
    created = client.post("/api/requests", json=payload).json()
    match_res = client.post(f"/api/match/{created['request_id']}?top_n=5")
    assert match_res.status_code == 200
    body = match_res.json()
    assert body["request_id"] == created["request_id"]
    assert "disclaimer" in body
    if body["matches"]:
        first = body["matches"][0]
        assert 0 <= first["overall_score"] <= 100
        assert 0 <= first["ml_response_probability"] <= 1


@pytest.mark.skipif(not MODEL_AVAILABLE, reason="Trained model not found - run `python ml/train.py` first")
def test_predict_endpoint(client):
    payload = {
        "age": 29, "blood_group": "O+", "total_donations": 6,
        "previous_requests_received": 8, "previous_requests_responded": 6,
        "average_response_time_minutes": 25, "current_availability": True,
        "distance_km": 3.2, "urgency_level": "Critical", "units_required": 2,
    }
    res = client.post("/api/predict", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert 0 <= body["response_probability"] <= 1
    assert "disclaimer" in body


def test_dashboard_stats(client):
    res = client.get("/api/dashboard/stats")
    assert res.status_code == 200
    body = res.json()
    for key in ["total_donors", "available_donors", "donors_by_blood_group"]:
        assert key in body


def test_notify_donor_not_found(client):
    res = client.post("/api/notify/D99999999")
    assert res.status_code == 404


def test_login_wrong_password(client):
    res = client.post("/api/login", json={"username": "admin", "password": "wrong"})
    assert res.status_code == 401


def test_login_correct_credentials(client):
    res = client.post("/api/login", json={"username": "admin", "password": "admin123"})
    assert res.status_code == 200
    assert res.json()["username"] == "admin"


def test_dashboard_page_renders(client):
    res = client.get("/")
    assert res.status_code == 200
    assert "text/html" in res.headers["content-type"]


@pytest.mark.parametrize("path", ["/request", "/search", "/donors", "/predict", "/history", "/analytics", "/about", "/login"])
def test_all_pages_render(client, path):
    res = client.get(path)
    assert res.status_code == 200
