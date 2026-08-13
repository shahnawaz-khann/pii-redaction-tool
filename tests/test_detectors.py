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


# --- Tests for previously-failing synthetic document cases ---

def test_label_based_name_detection():
    """Names after 'Full Name:' or 'Name:' labels must be detected."""
    text = "Full Name: Rahul Sharma\nName: Priya Mehta"
    detections = detect_pii(text)
    person_texts = [d['text'] for d in detections if d['type'] == 'PERSON']
    assert any("Rahul Sharma" in t for t in person_texts), "Rahul Sharma not detected"
    assert any("Priya Mehta" in t for t in person_texts), "Priya Mehta not detected"


def test_label_based_organization_detection():
    """Company name after 'Company:' label must be detected."""
    text = "Company:\nSharma Technologies Private Limited"
    detections = detect_pii(text)
    org_texts = [d['text'] for d in detections if d['type'] == 'ORGANIZATION']
    assert any("Sharma Technologies" in t for t in org_texts), "Sharma Technologies not detected"


def test_label_based_address_detection():
    """Address with Indian PIN code after 'Address:' label must be detected."""
    text = "Address:\n42 Green Park Road, Sector 18,\nNoida, Uttar Pradesh 201301, India"
    detections = detect_pii(text)
    addr_texts = [d['text'] for d in detections if d['type'] == 'ADDRESS']
    assert len(addr_texts) >= 1, "Address not detected"
    assert any("201301" in t for t in addr_texts), "PIN code not found in detected address"


def test_credit_card_with_spaces():
    """Credit card number with spaces must pass Luhn and be detected."""
    text = "Credit Card: 4111 1111 1111 1111"
    assert is_luhn_valid("4111 1111 1111 1111")
    detections = detect_pii(text)
    card_dets = [d for d in detections if d['type'] == 'CREDIT_CARD']
    assert len(card_dets) == 1, f"Credit card not detected. Got: {detections}"


def test_all_9_categories_synthetic():
    """Synthetic document must produce detections for all 9 PII categories."""
    text = (
        "Full Name: Rahul Sharma\n"
        "Email: rahul.sharma@example.com\n"
        "Phone: +91 9876543210\n"
        "Date of Birth: 15/08/2001\n"
        "Address:\n"
        "42 Green Park Road, Sector 18,\n"
        "Noida, Uttar Pradesh 201301, India\n"
        "Company:\n"
        "Sharma Technologies Private Limited\n"
        "SSN: 123-45-6789\n"
        "Credit Card: 4111 1111 1111 1111\n"
        "IP Address: 192.168.1.25\n"
    )
    detections = detect_pii(text)
    found_types = {d['type'] for d in detections}
    required = {"PERSON", "EMAIL", "PHONE", "DOB", "ADDRESS", "ORGANIZATION", "SSN", "CREDIT_CARD", "IP_ADDRESS"}
    missing = required - found_types
    assert not missing, f"Missing categories: {missing}"


# --- v2 regression tests ---

def test_name_label_does_not_cross_newline_into_next_label():
    """Person name captured by 'Full Name:' label must not include the next label line."""
    text = "Full Name: Aarav Mehta\nEmail: aarav.mehta@example.com"
    detections = detect_pii(text)
    person_texts = [d['text'] for d in detections if d['type'] == 'PERSON']
    assert any(t == "Aarav Mehta" for t in person_texts), f"Got: {person_texts}"
    # Must not swallow 'Email' from the next line
    assert not any("Email" in t for t in person_texts), f"Name crossed into next label: {person_texts}"


def test_address_does_not_swallow_next_section_label():
    """Address detection must stop before the next 'Label: value' line."""
    text = (
        "Address:\n"
        "28 MG Road, Andheri West,\n"
        "Mumbai, Maharashtra 400058, India\n"
        "Credit Card: 5555 5555 5555 4444"
    )
    detections = detect_pii(text)
    addr_texts = [d['text'] for d in detections if d['type'] == 'ADDRESS']
    assert len(addr_texts) >= 1, "Address not detected"
    assert all("Credit Card" not in t for t in addr_texts), f"Address swallowed next section: {addr_texts}"


def test_second_credit_card_not_lost_due_to_address_overlap():
    """Both credit cards must be detected independently when they follow separate address blocks."""
    text = (
        "Address:\n"
        "17 Lake View Road, Sector 15,\n"
        "Gurugram, Haryana 122001, India\n"
        "Credit Card: 4111 1111 1111 1111\n"
        "Address:\n"
        "28 MG Road, Andheri West,\n"
        "Mumbai, Maharashtra 400058, India\n"
        "Credit Card: 5555 5555 5555 4444"
    )
    detections = detect_pii(text)
    card_dets = [d for d in detections if d['type'] == 'CREDIT_CARD']
    card_texts = [d['text'] for d in card_dets]
    assert any("4111" in t for t in card_texts), f"First card missing: {card_texts}"
    assert any("5555" in t for t in card_texts), f"Second card missing: {card_texts}"


def test_v2_full_synthetic_all_9_categories():
    """Full v2 synthetic document must detect all 9 PII categories cleanly."""
    text = (
        "Full Name: Aarav Mehta\n"
        "Email: aarav.mehta@example.com\n"
        "Phone: +91 9876543210\n"
        "Date of Birth: 15/08/2001\n"
        "Address:\n"
        "17 Lake View Road, Sector 15,\n"
        "Gurugram, Haryana 122001, India\n"
        "Company:\n"
        "Sharma Technologies Private Limited\n"
        "SSN: 123-45-6789\n"
        "Credit Card: 4111 1111 1111 1111\n"
        "IP Address: 192.168.1.25\n"
        "Name: Neha Kapoor\n"
        "Email: neha.kapoor@example.com\n"
        "Phone: +91 9123456789\n"
        "Address:\n"
        "28 MG Road, Andheri West,\n"
        "Mumbai, Maharashtra 400058, India\n"
        "Credit Card: 5555 5555 5555 4444\n"
    )
    detections = detect_pii(text)
    found_types = {d['type'] for d in detections}
    # All 9 required categories
    required = {"PERSON", "EMAIL", "PHONE", "DOB", "ADDRESS", "ORGANIZATION", "SSN", "CREDIT_CARD", "IP_ADDRESS"}
    missing = required - found_types
    assert not missing, f"Missing categories in v2: {missing}"
    # Specific names detected
    person_texts = [d['text'] for d in detections if d['type'] == 'PERSON']
    assert any("Aarav Mehta" in t for t in person_texts), "Aarav Mehta not found"
    assert any("Neha Kapoor" in t for t in person_texts), "Neha Kapoor not found"
    # Both credit cards detected
    card_texts = [d['text'] for d in detections if d['type'] == 'CREDIT_CARD']
    assert any("4111" in t for t in card_texts), "First card (4111) not detected"
    assert any("5555" in t for t in card_texts), "Second card (5555) not detected"

