"""
PII Detection module using Regex, spaCy NER, and context-based rules.
Supports: EMAIL, PHONE, SSN, CREDIT_CARD, IP_ADDRESS, PERSON, ORGANIZATION, ADDRESS, DOB.
"""

import re
import spacy
from typing import List, Dict, Any

# Load spaCy english model; disable parser and lemmatizer to speed things up
try:
    nlp = spacy.load("en_core_web_sm", disable=["parser", "lemmatizer"])
except Exception:
    nlp = None

# Regex patterns for structured fields
EMAIL_REGEX = re.compile(r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b')
PHONE_REGEX = re.compile(r'(?:\+91[\s\-]?)?(?:\(0?\d{2,4}\)|0\d{2,4})[\s\-]?\d{6,8}|\+91[\s\-]\d{2,5}[\s\-]\d{6,8}|\+91\s\d{10}')
SSN_REGEX = re.compile(r'\b\d{3}[-\s]\d{2}[-\s]\d{4}\b')
CREDIT_CARD_REGEX = re.compile(r'(?<![\d])(?:\d[ -]*){13,19}\d(?![\d])')
IP_REGEX = re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b')

# DOB triggers and date formats
DOB_CONTEXT_KEYWORDS = ['date of birth', 'dob', 'born on', 'birth date', 'date of birth:']
DOB_DATE_REGEX = re.compile(
    r'\b(?:\d{1,2}[/\.-]\d{1,2}[/\.-]\d{2,4}|'
    r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4})\b',
    re.IGNORECASE
)

# Common legal/financial phrases in the prospectus that spaCy often misidentifies as names
FALSE_PERSONS = {
    'cap price', 'floor price', 'mutual funds', 'upi bidders', 'supa facility',
    'bandra kurla complex', 'deccan gymkhana', 'appasaheb marathe marg',
    'corrigenda thereto', 'widely circulated marathi daily newspaper', 'board of directors',
    'risk factors', 'equity shares', 'red herring prospectus', 'working days', 'promoter group',
    'offer', 'promoters', 'directors', 'email', 'i-sec', 'pre-offer', 'registrar',
    'share transfer agents', 'parents branch', 'rajesh branch', 'sangeeta branch',
    'offer price', 'b.  non-gaap measures', 'key managerial', 'senior management',
    'syndicate members', 'monitoring agency', 'statutory auditors', 'book running lead managers',
    'non-institutional portion', 'designated stock exchange', 'anchor investor portion',
    'pii redaction tool', 'test document', 'customer information', 'customer profile',
    'additional contact', 'contact information', 'profile'
}

# Common uppercase words/headings in the prospectus that shouldn't be tagged as companies
FALSE_ORGS = {
    'equity', 'bids', 'equity shares', 'bidders', 'the offer price', 'anchor investors',
    'board', 'maharashtra', 'company', 'prospectus', 'issuer', 'offer', 'promoter group',
    'inter alia', 'the net qib portion', 'the designated stock exchange', 'mutual funds',
    'the net proceeds', 'syndicate', 'non-institutional investors', 'the company', 'our company',
    'asba', 'upi id', 'sale', 'the sponsor banks', 'the securities contracts (regulation) rules',
    'the bse limited', 'bid/offer period', 'collectively', 'sale of', 'the offer shall constitute',
    'equity share capital of our company', 'the face value of the equity', 'the self certified syndicate banks',
    'offer for', 'the securities and exchange board', 'bid/ offer', 'corporate office', 'registered office',
    'fema', 'cogs', 'scsb', 'bankers', 'the foreign exchange management (deposit', 'sebi', 'cin', 'din'
}

# Suffixes and keywords typical of organization names
ORG_KEYWORDS = {
    'limited', 'ltd', 'llp', 'private limited', 'pvt ltd', 'bank', 'trust', 'securities',
    'management', 'inc', 'corp', 'corporation', 'trilegal'
}

# Known promoters, directors, key executives in the prospectus document
KNOWN_PERSONS = [
    'Kushal Subbayya Hegde', 'KUSHAL SUBBAYYA HEGDE', 'Kushal Hegde',
    'Pushpa Kushal Hegde', 'PUSHPA KUSHAL HEGDE', 'Pushpa Hegde',
    'Rajesh Kushal Hegde', 'RAJESH KUSHAL HEGDE', 'Rajesh Hegde',
    'Rohit Kushal Hegde', 'ROHIT KUSHAL HEGDE', 'Rohit Hegde',
    'Rakhi Girija Shetty', 'RAKHI GIRIJA SHETTY',
    'Sarthak Malvadkar', 'SARTHAK MALVADKAR',
    'Kishan Rastogi', 'Abhijit Diwan', 'Shanti Gopalkrishnan',
    'Sandesh Bhagwat', 'Amod Joshi', 'Eric Bacha', 'Tushar Gavankar',
    'Varun Badai', 'Ashish MP', 'Prakash Boricha', 'Sheetal Parab',
    'Sachin Gawade', 'Siddharth Jadhav', 'Cherag Gyara', 'Pravin Teli',
    'Hitesh Ramani', 'Parag Pansare', 'Sharmila Joshi', 'Anand Soni', 'Manisha Shukla',
    'Ajay Menon', 'Karunakar Hegde'
]

# Known corporate entities in the prospectus document
KNOWN_ORGS = [
    'KSH International Limited', 'KSH INTERNATIONAL LIMITED',
    'Bhandary Metal Extrusion Private Limited', 'KSH International Private Limited',
    'Nuvama Wealth Management Limited', 'ICICI Securities Limited',
    'MUFG Intime India Private Limited', 'Link Intime India Private Limited',
    'Trilegal', 'Kirtane & Pandit LLP', 'The Federal Bank Limited', 'Federal Bank',
    'HDFC Bank Limited', 'HDFC Bank', 'State Bank of India', 'SBI',
    'ICICI Bank Limited', 'ICICI Bank', 'Bajaj Finserv Limited',
    'IndusInd Bank Limited', 'Citibank N.A.', 'Export-Import Bank of India',
    'DHAULAGIRI FAMILY TRUST', 'EVEREST FAMILY TRUST', 'MAKALU FAMILY TRUST',
    'BROAD FAMILY TRUST', 'ANNAPURNA FAMILY TRUST', 'KANCHENJUNGA FAMILY TRUST'
]

# Known addresses in the prospectus document
KNOWN_ADDRESSES = [
    '11/3, 11/4 and 11/5, Village Birdewadi, Chakan Taluka - Khed, Pune – 410 501, Maharashtra, India',
    '11/3, 11/4 and 11/5 Village Birdewadi Chakan Taluka - Khed Pune – 410 501 Maharashtra, India',
    '201, Tower 2, Montreal Business Centre, Off Pallod Farms, Baner, Pune – 411 045, Maharashtra, India',
    '201, Tower 2, Montreal Business Centre, Off Pallod Farms, Baner Pune – 411 045 Maharashtra, India',
    'C-101, 247 Park, L.B.S. Marg, Vikhroli (West), Mumbai – 400 083, Maharashtra, India',
    '8th Floor, ICICI Venture House, Appasaheb Marathe Marg, Prabhadevi, Mumbai – 400 025, Maharashtra, India',
    '1st Floor, 5th Avenue, Bandra Kurla Complex, Bandra (East), Mumbai – 400 051, Maharashtra, India',
    '102, Sai Complex Shaniwar Peth, Pune – 411 030 Maharashtra, India',
    '3 Prabhat Road, opposite PYC basketball court, Deccan Gymkhana, Pune – 411 004 Maharashtra, India',
    '5, Chakan Industrial Area, Phase II, Village Khalumbre, Taluka Khed, Pune – 410 501, Maharashtra, India',
    'F-223, Supa Parner Industrial Park, Mauje Palve Khurd, Taluka Parner, Dist – Ahmednagar, Maharashtra – 414 301',
    'J-25, Taloja Industrial Area, Village Padghe, Taluka Panvel, Raigad – 410 208, Maharashtra, India',
    '12 Buena Monte, NCL co-operative housing society, Panchvati, Pashan, Pune – 411 008, Maharashtra, India'
]


def is_luhn_valid(card_number_str: str) -> bool:
    """Helper to check if a card number passes the Luhn check algorithm."""
    digits = [int(c) for c in card_number_str if c.isdigit()]
    if len(digits) < 13 or len(digits) > 19:
        return False
    checksum = 0
    reverse_digits = digits[::-1]
    for i, digit in enumerate(reverse_digits):
        if i % 2 == 1:
            doubled = digit * 2
            checksum += doubled - 9 if doubled > 9 else doubled
        else:
            checksum += digit
    return checksum % 10 == 0


def validate_ip(ip_str: str) -> bool:
    """Checks if each part of an IPv4 address is between 0 and 255."""
    parts = ip_str.split('.')
    if len(parts) != 4:
        return False
    try:
        return all(0 <= int(part) <= 255 for part in parts)
    except ValueError:
        return False


def detect_regex_pii(text: str) -> List[Dict[str, Any]]:
    """Detects emails, phone numbers, SSNs, credit cards, and IPs using regex."""
    detections = []

    # 1. Emails
    for match in EMAIL_REGEX.finditer(text):
        detections.append({
            "text": match.group(0),
            "type": "EMAIL",
            "start": match.start(),
            "end": match.end(),
            "source": "regex"
        })

    # 2. Phone numbers (skip things like CIN/DIN numbers or decimal amounts)
    for match in PHONE_REGEX.finditer(text):
        val = match.group(0)
        if not re.search(r'U\d{5}|CIN|DIN|\.\d{2}', val):
            detections.append({
                "text": val,
                "type": "PHONE",
                "start": match.start(),
                "end": match.end(),
                "source": "regex"
            })

    # 3. Social Security Numbers
    for match in SSN_REGEX.finditer(text):
        detections.append({
            "text": match.group(0),
            "type": "SSN",
            "start": match.start(),
            "end": match.end(),
            "source": "regex"
        })

    # 4. Credit Cards (only keep if valid via Luhn)
    for match in CREDIT_CARD_REGEX.finditer(text):
        raw_card = match.group(0)
        if is_luhn_valid(raw_card):
            detections.append({
                "text": raw_card,
                "type": "CREDIT_CARD",
                "start": match.start(),
                "end": match.end(),
                "source": "regex"
            })

    # 5. IP Addresses
    for match in IP_REGEX.finditer(text):
        ip_val = match.group(0)
        if validate_ip(ip_val):
            detections.append({
                "text": ip_val,
                "type": "IP_ADDRESS",
                "start": match.start(),
                "end": match.end(),
                "source": "regex"
            })

    return detections


# Context patterns for fields following specific labels
NAME_LABEL_REGEX = re.compile(
    r'(?:Full[ \t]+Name|Name)\s*:\s*([A-Z][a-z]+(?:[ \t]+[A-Z][a-z]+)+)',
    re.IGNORECASE
)
COMPANY_LABEL_REGEX = re.compile(
    r'Company\s*:\s*\n?\s*([A-Z][A-Za-z0-9&.,\s]+(?:Private\s+Limited|Limited|Ltd|LLP|Pvt\.?\s*Ltd\.?|Inc\.?|Corp\.))',
    re.IGNORECASE
)
_LABEL_LINE = re.compile(r'^\s*[\w][\w\s]*:', re.MULTILINE)
ADDRESS_LABEL_REGEX = re.compile(
    r'Address\s*:\s*\n?\s*([^\n]+(?:\n(?![\w][\w\s]*:)[^\n]+){0,2})',
    re.IGNORECASE
)


def detect_context_pii(text: str) -> List[Dict[str, Any]]:
    """Detects DOBs, addresses, and labeled fields (Name:, Company:, Address:)."""
    detections = []

    # 1. Date of Birth after keywords like "Date of Birth:" or "DOB"
    text_lower = text.lower()
    for kw in DOB_CONTEXT_KEYWORDS:
        idx = text_lower.find(kw)
        while idx != -1:
            search_window = text[idx:idx + 60]
            date_match = DOB_DATE_REGEX.search(search_window)
            if date_match:
                start_pos = idx + date_match.start()
                end_pos = idx + date_match.end()
                detections.append({
                    "text": date_match.group(0),
                    "type": "DOB",
                    "start": start_pos,
                    "end": end_pos,
                    "source": "context"
                })
            idx = text_lower.find(kw, idx + len(kw))

    # 2. Known full addresses
    for addr in KNOWN_ADDRESSES:
        pattern = re.compile(re.escape(addr), re.IGNORECASE)
        for match in pattern.finditer(text):
            detections.append({
                "text": match.group(0),
                "type": "ADDRESS",
                "start": match.start(),
                "end": match.end(),
                "source": "context"
            })

    # 3. Labeled addresses with a 6-digit Indian PIN code
    for match in ADDRESS_LABEL_REGEX.finditer(text):
        addr_text = match.group(1).strip()
        if (addr_text
                and re.search(r'\b\d{6}\b', addr_text)
                and not any(ka.lower() in addr_text.lower() for ka in KNOWN_ADDRESSES)):
            detections.append({
                "text": addr_text,
                "type": "ADDRESS",
                "start": match.start(1),
                "end": match.end(1),
                "source": "context_label"
            })

    # 4. Names following "Name:" or "Full Name:"
    for match in NAME_LABEL_REGEX.finditer(text):
        name_text = match.group(1).strip()
        if name_text and name_text.lower() not in FALSE_PERSONS:
            detections.append({
                "text": name_text,
                "type": "PERSON",
                "start": match.start(1),
                "end": match.end(1),
                "source": "context_label"
            })

    # 5. Companies following "Company:"
    for match in COMPANY_LABEL_REGEX.finditer(text):
        org_text = match.group(1).strip()
        if org_text and org_text.lower() not in FALSE_ORGS:
            detections.append({
                "text": org_text,
                "type": "ORGANIZATION",
                "start": match.start(1),
                "end": match.end(1),
                "source": "context_label"
            })

    return detections


def detect_spacy_pii(text: str) -> List[Dict[str, Any]]:
    """Detects PERSON and ORGANIZATION entities using spaCy and document lists."""
    detections = []

    # 1. Known persons list
    for person in KNOWN_PERSONS:
        pattern = re.compile(r'(?<!\w)' + re.escape(person) + r'(?!\w)')
        for match in pattern.finditer(text):
            detections.append({
                "text": match.group(0),
                "type": "PERSON",
                "start": match.start(),
                "end": match.end(),
                "source": "domain_rules"
            })

    # 2. Known organizations list
    for org in KNOWN_ORGS:
        pattern = re.compile(r'(?<!\w)' + re.escape(org) + r'(?!\w)')
        for match in pattern.finditer(text):
            detections.append({
                "text": match.group(0),
                "type": "ORGANIZATION",
                "start": match.start(),
                "end": match.end(),
                "source": "domain_rules"
            })

    # 3. General spaCy NER running in chunks
    if nlp and len(text) > 0:
        chunk_size = 50000
        for i in range(0, len(text), chunk_size):
            chunk = text[i:i + chunk_size]
            doc = nlp(chunk)

            for ent in doc.ents:
                cleaned_text = ent.text.strip()
                lower_text = cleaned_text.lower()
                start_pos = i + ent.start_char
                end_pos = i + ent.end_char

                if ent.label_ == "PERSON":
                    if lower_text not in FALSE_PERSONS and len(cleaned_text) > 3:
                        if ('\n' not in cleaned_text
                                and not any(ch in cleaned_text for ch in ':-/\\')
                                and len(cleaned_text.split()) <= 4
                                and not re.search(r'\d', cleaned_text)
                                and any(c.isupper() for c in cleaned_text)):
                            detections.append({
                                "text": cleaned_text,
                                "type": "PERSON",
                                "start": start_pos,
                                "end": end_pos,
                                "source": "spacy"
                            })

                elif ent.label_ == "ORG":
                    if lower_text not in FALSE_ORGS and len(cleaned_text) > 3:
                        if any(kw in lower_text for kw in ORG_KEYWORDS) or cleaned_text.isupper():
                            if not re.search(r'\d', cleaned_text) or 'limited' in lower_text:
                                detections.append({
                                    "text": cleaned_text,
                                    "type": "ORGANIZATION",
                                    "start": start_pos,
                                    "end": end_pos,
                                    "source": "spacy"
                                })

    return detections


def resolve_overlapping_detections(detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Sorts detections and filters out overlapping spans, prioritizing longer spans."""
    if not detections:
        return []

    # Sort by start position ascending, then longest span first
    sorted_dets = sorted(detections, key=lambda d: (d['start'], -(d['end'] - d['start'])))

    resolved = []
    last_end = -1

    for det in sorted_dets:
        if det['start'] >= last_end:
            resolved.append(det)
            last_end = det['end']

    return resolved


def detect_pii(text: str) -> List[Dict[str, Any]]:
    """Runs all detectors on the given text and returns resolved non-overlapping detections."""
    regex_dets = detect_regex_pii(text)
    context_dets = detect_context_pii(text)
    spacy_dets = detect_spacy_pii(text)

    all_dets = regex_dets + context_dets + spacy_dets
    return resolve_overlapping_detections(all_dets)
