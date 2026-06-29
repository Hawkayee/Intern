"""Data access layer for the kiosk.

This is the ONLY place that knows where student/bottle data comes from.
Right now it reads local mock JSON files. Later, the bodies of these
functions will be replaced with HTTP calls to the cloud (AWS) API with
no change required in the callers (app.py / templates).

Public API:
    lookup_student(reg_no) -> dict | None
    lookup_bottle(barcode) -> dict | None
"""

import json
from pathlib import Path

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _load(filename):
    with open(_DATA_DIR / filename, "r", encoding="utf-8") as fh:
        return json.load(fh)


def lookup_student(reg_no):
    """Return {"name": ..., "class": ...} for a registration number, or None.

    Lookup is case-insensitive and trims surrounding whitespace so the
    on-screen keypad doesn't have to be strict about casing.
    """
    if not reg_no:
        return None
    students = _load("students.json")
    key = reg_no.strip().upper()
    # students.json keys are stored upper-case; normalise for safety.
    normalised = {k.upper(): v for k, v in students.items()}
    return normalised.get(key)


def lookup_bottle(barcode):
    """Return bottle details for a barcode, or None if unknown."""
    if not barcode:
        return None
    bottles = _load("bottles.json")
    return bottles.get(str(barcode).strip())
