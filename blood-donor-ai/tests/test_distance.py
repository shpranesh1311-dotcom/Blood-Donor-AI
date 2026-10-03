"""Tests for app/services/distance.py"""

import pytest
from app.services.distance import haversine_km, is_within_radius


def test_distance_to_self_is_zero():
    assert haversine_km(11.0016, 76.9558, 11.0016, 76.9558) == pytest.approx(0, abs=1e-6)


def test_known_distance_coimbatore_to_chennai():
    # Coimbatore (~11.0168, 76.9558) to Chennai (~13.0827, 80.2707) is a
    # straight-line ("as the crow flies") distance of roughly 420-435 km.
    dist = haversine_km(11.0168, 76.9558, 13.0827, 80.2707)
    assert 415 < dist < 435


def test_distance_is_symmetric():
    d1 = haversine_km(11.0, 77.0, 11.05, 77.05)
    d2 = haversine_km(11.05, 77.05, 11.0, 77.0)
    assert d1 == pytest.approx(d2, rel=1e-9)


def test_is_within_radius_true():
    assert is_within_radius(11.0016, 76.9558, 11.005, 76.96, radius_km=5)


def test_is_within_radius_false():
    assert not is_within_radius(11.0016, 76.9558, 13.0827, 80.2707, radius_km=5)


def test_distance_raises_on_missing_coordinates():
    with pytest.raises(ValueError):
        haversine_km(None, 76.9558, 11.0, 77.0)
