"""
test_detectors.py
Pytest unit tests for PII detectors, false positive suppression, and replacement consistency.
"""

import pytest
from src.detectors import detect_pii, is_luhn_valid, validate_ip
from src.redactor import PIIRedactor


def test_email_detection():
    text = "Contact us at john.doe@example.com for inquiries."
    detections = detect_pii(text)
    email_dets = [d for d in detections if d['type'] == 'EMAIL']
    assert len(email_dets) == 1
    assert email_dets[0]['text'] == "john.doe@example.com"


def test_phone_detection():
    text = "Call our hotline at +91 9876543210 or 020 4505 3237."
    detections = detect_pii(text)
    phone_dets = [d for d in detections if d['type'] == 'PHONE']
    assert len(phone_dets) >= 1
    assert any("9876543210" in d['text'] for d in phone_dets)


def test_ssn_detection():
    text = "Social Security Number: 123-45-6789."
    detections = detect_pii(text)
    ssn_dets = [d for d in detections if d['type'] == 'SSN']
    assert len(ssn_dets) == 1
    assert ssn_dets[0]['text'] == "123-45-6789"


def test_credit_card_detection():
    valid_card = "4111 1111 1111 1111"
    text = f"Payment method: {valid_card}"
    assert is_luhn_valid(valid_card)
    detections = detect_pii(text)
    card_dets = [d for d in detections if d['type'] == 'CREDIT_CARD']
    assert len(card_dets) == 1


def test_invalid_credit_card_rejected():
    invalid_card = "1111 1111 1111 1111"
    text = f"Invalid card: {invalid_card}"
    assert not is_luhn_valid(invalid_card)
    detections = detect_pii(text)
    card_dets = [d for d in detections if d['type'] == 'CREDIT_CARD']
    assert len(card_dets) == 0


def test_ip_address_detection():
    text = "Server IP: 192.168.1.10"
    detections = detect_pii(text)
    ip_dets = [d for d in detections if d['type'] == 'IP_ADDRESS']
    assert len(ip_dets) == 1
    assert ip_dets[0]['text'] == "192.168.1.10"


def test_invalid_ip_address_rejected():
    assert not validate_ip("999.999.999.999")
    text = "Invalid IP: 999.999.999.999"
    detections = detect_pii(text)
    ip_dets = [d for d in detections if d['type'] == 'IP_ADDRESS']
    assert len(ip_dets) == 0


def test_dob_detection():
    text = "Candidate Date of Birth: 15/08/1999."
    detections = detect_pii(text)
    dob_dets = [d for d in detections if d['type'] == 'DOB']
    assert len(dob_dets) == 1
    assert dob_dets[0]['text'] == "15/08/1999"


def test_ordinary_date_not_dob():
    text = "The prospectus was filed on December 10, 2025."
    detections = detect_pii(text)
    dob_dets = [d for d in detections if d['type'] == 'DOB']
    assert len(dob_dets) == 0


def test_person_detection():
    text = "The Managing Director is Rashi Patil."
    detections = detect_pii(text)
    person_dets = [d for d in detections if d['type'] == 'PERSON']
    assert len(person_dets) == 1
    assert "Rashi Patil" in person_dets[0]['text']


def test_organization_detection():
    text = "The audit was conducted by Example Technologies Private Limited."
    detections = detect_pii(text)
    org_dets = [d for d in detections if d['type'] == 'ORGANIZATION']
    assert len(org_dets) == 1
    assert "Example Technologies" in org_dets[0]['text']


def test_non_pii_order_id_not_redacted():
    text = "Order ID: 123456 with 50 shares."
    detections = detect_pii(text)
    assert len(detections) == 0


def test_replacement_consistency():
    redactor = PIIRedactor(seed=42)
    rep1 = redactor.get_replacement("Rashi Patil", "PERSON")
    rep2 = redactor.get_replacement("Rashi Patil", "PERSON")
    assert rep1 == rep2
    assert rep1 != "Rashi Patil"


def test_replacement_case_normalization():
    redactor = PIIRedactor(seed=42)
    rep_title = redactor.get_replacement("Rashi Patil", "PERSON")
    rep_upper = redactor.get_replacement("RASHI PATIL", "PERSON")
    assert rep_title.upper() == rep_upper


def test_distinct_phones_have_different_replacements():
    redactor = PIIRedactor(seed=42)
    phone1_rep = redactor.get_replacement("+91 9876543210", "PHONE")
    phone2_rep = redactor.get_replacement("+91 20 45053237", "PHONE")
    assert phone1_rep != phone2_rep
