"""
Unit tests for the form-validation logic used before any MongoDB write
(event creation/edition and user creation/edition). These run without a
database: they only exercise the pure validation functions.

Run with:  pytest tests/
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "routes"))

from routes.events import validate_event_form  # noqa: E402
from routes.users import validate_user_form  # noqa: E402


def valid_event_form(**overrides):
    form = {
        "title": "Intro to Testing",
        "capacity": "20",
        "startDate": "2026-12-01T10:00",
        "endDate": "2026-12-01T12:00",
        "organizerId": "6aa1d6ad24a9cbb874620f16",
    }
    form.update(overrides)
    return form


def valid_user_form(**overrides):
    form = {
        "firstName": "Ada",
        "lastName": "Lovelace",
        "email": "ada.lovelace@campus.fr",
        "department": "Computer Science",
        "role": "student",
    }
    form.update(overrides)
    return form


# --- events -----------------------------------------------------------

def test_valid_event_form_has_no_errors():
    assert validate_event_form(valid_event_form()) == []


def test_empty_title_is_rejected():
    errors = validate_event_form(valid_event_form(title="   "))
    assert any("title" in e.lower() for e in errors)


def test_zero_capacity_is_rejected():
    errors = validate_event_form(valid_event_form(capacity="0"))
    assert any("capacity" in e.lower() for e in errors)


def test_negative_capacity_is_rejected():
    errors = validate_event_form(valid_event_form(capacity="-5"))
    assert any("capacity" in e.lower() for e in errors)


def test_non_numeric_capacity_is_rejected():
    errors = validate_event_form(valid_event_form(capacity="abc"))
    assert any("capacity" in e.lower() for e in errors)


def test_end_date_before_start_date_is_rejected():
    errors = validate_event_form(valid_event_form(
        startDate="2026-12-05T10:00", endDate="2026-12-04T10:00",
    ))
    assert any("end date" in e.lower() for e in errors)


def test_end_date_equal_to_start_date_is_accepted():
    # end == start is allowed (the rule only forbids end < start)
    errors = validate_event_form(valid_event_form(
        startDate="2026-12-05T10:00", endDate="2026-12-05T10:00",
    ))
    assert errors == []


def test_missing_organizer_is_rejected():
    errors = validate_event_form(valid_event_form(organizerId=""))
    assert any("organizer" in e.lower() for e in errors)


def test_multiple_errors_are_all_reported():
    errors = validate_event_form(valid_event_form(title="", capacity="0", organizerId=""))
    assert len(errors) >= 3


# --- users --------------------------------------------------------------

def test_valid_user_form_has_no_errors():
    assert validate_user_form(valid_user_form()) == []


def test_empty_first_name_is_rejected():
    errors = validate_user_form(valid_user_form(firstName=""))
    assert any("first name" in e.lower() for e in errors)


def test_empty_last_name_is_rejected():
    errors = validate_user_form(valid_user_form(lastName=""))
    assert any("last name" in e.lower() for e in errors)


def test_malformed_email_is_rejected():
    errors = validate_user_form(valid_user_form(email="not-an-email"))
    assert any("email" in e.lower() for e in errors)


def test_empty_email_is_rejected():
    errors = validate_user_form(valid_user_form(email=""))
    assert any("email" in e.lower() for e in errors)


def test_empty_department_is_rejected():
    errors = validate_user_form(valid_user_form(department=""))
    assert any("department" in e.lower() for e in errors)


def test_empty_role_is_rejected():
    errors = validate_user_form(valid_user_form(role=""))
    assert any("role" in e.lower() for e in errors)
