"""
distance.py
===========
Approximate distance calculation utilities using the haversine formula.

This is sufficient for a demo/college project (straight-line "as the crow
flies" distance). It is NOT actual road/travel distance or ETA.
"""

import math


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Return the great-circle distance in kilometers between two
    latitude/longitude points using the haversine formula.
    """
    if None in (lat1, lon1, lat2, lon2):
        raise ValueError("Latitude/longitude values must not be None")

    R = 6371.0  # Earth radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    c = 2 * math.asin(min(1.0, math.sqrt(a)))
    return R * c


def is_within_radius(lat1: float, lon1: float, lat2: float, lon2: float, radius_km: float) -> bool:
    return haversine_km(lat1, lon1, lat2, lon2) <= radius_km
