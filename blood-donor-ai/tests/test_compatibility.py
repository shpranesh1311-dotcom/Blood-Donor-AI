"""Tests for app/services/compatibility.py"""

import pytest
from app.services.compatibility import (
    is_valid_blood_group, is_compatible, get_compatible_donor_groups, VALID_BLOOD_GROUPS,
)


def test_all_blood_groups_valid():
    for bg in VALID_BLOOD_GROUPS:
        assert is_valid_blood_group(bg)


def test_invalid_blood_group():
    assert not is_valid_blood_group("XX")
    assert not is_valid_blood_group("")


def test_o_negative_is_universal_donor():
    for recipient in VALID_BLOOD_GROUPS:
        assert is_compatible("O-", recipient)


def test_ab_positive_is_universal_recipient():
    compatible = get_compatible_donor_groups("AB+")
    assert set(compatible) == set(VALID_BLOOD_GROUPS)


def test_o_positive_cannot_donate_to_o_negative():
    assert not is_compatible("O+", "O-")


def test_a_positive_can_donate_to_a_positive():
    assert is_compatible("A+", "A+")


def test_a_negative_cannot_donate_to_b_negative():
    assert not is_compatible("A-", "B-")


def test_get_compatible_donor_groups_invalid_raises():
    with pytest.raises(ValueError):
        get_compatible_donor_groups("INVALID")


def test_is_compatible_handles_invalid_groups_gracefully():
    assert not is_compatible("INVALID", "O+")
    assert not is_compatible("O+", "INVALID")
