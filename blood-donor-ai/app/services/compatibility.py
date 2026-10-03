"""
compatibility.py
=================
Blood-group compatibility module.

This module implements STANDARD, well-known ABO/Rh donor-recipient
compatibility rules for whole blood / red-cell donation.

IMPORTANT MEDICAL DISCLAIMER:
    This module encodes textbook ABO/Rh compatibility only. It does NOT
    account for cross-matching, antibody screening, component-specific
    rules (plasma vs platelets vs whole blood), or patient-specific
    medical factors. Actual transfusion compatibility and donor
    eligibility MUST be confirmed by qualified medical professionals
    and the hospital blood bank before any transfusion occurs.

The module is intentionally isolated in its own file so it can be
reviewed, audited, or replaced independently of the rest of the system.
"""

from typing import List

VALID_BLOOD_GROUPS = ["O+", "O-", "A+", "A-", "B+", "B-", "AB+", "AB-"]

# Recipient blood group -> list of donor blood groups that can safely donate to them.
# (Standard whole-blood / red cell compatibility chart.)
COMPATIBLE_DONORS_FOR_RECIPIENT = {
    "O-": ["O-"],
    "O+": ["O-", "O+"],
    "A-": ["O-", "A-"],
    "A+": ["O-", "O+", "A-", "A+"],
    "B-": ["O-", "B-"],
    "B+": ["O-", "O+", "B-", "B+"],
    "AB-": ["O-", "A-", "B-", "AB-"],
    "AB+": ["O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"],
}


def is_valid_blood_group(blood_group: str) -> bool:
    return blood_group in VALID_BLOOD_GROUPS


def get_compatible_donor_groups(recipient_blood_group: str) -> List[str]:
    """
    Return the list of donor blood groups that are compatible with the given
    recipient blood group, according to standard ABO/Rh rules.

    Raises ValueError if the recipient blood group is not recognised.
    """
    if not is_valid_blood_group(recipient_blood_group):
        raise ValueError(
            f"Invalid blood group '{recipient_blood_group}'. "
            f"Expected one of: {', '.join(VALID_BLOOD_GROUPS)}"
        )
    return COMPATIBLE_DONORS_FOR_RECIPIENT[recipient_blood_group]


def is_compatible(donor_blood_group: str, recipient_blood_group: str) -> bool:
    """
    Check whether a donor's blood group is compatible with a given
    recipient's blood group under standard ABO/Rh rules.
    """
    if not is_valid_blood_group(donor_blood_group) or not is_valid_blood_group(recipient_blood_group):
        return False
    return donor_blood_group in COMPATIBLE_DONORS_FOR_RECIPIENT[recipient_blood_group]


COMPATIBILITY_DISCLAIMER = (
    "This tool applies standard ABO/Rh donor-recipient compatibility rules only. "
    "It does not perform cross-matching or antibody screening. Final transfusion "
    "compatibility and donor eligibility must always be confirmed by qualified "
    "medical professionals and the hospital blood bank."
)
