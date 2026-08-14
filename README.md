# PII Redaction Tool

A Python tool to detect Personally Identifiable Information (PII) in Word documents (`.docx`) and replace sensitive data with realistic, consistent fake values while preserving the document's structure and formatting.

Built for the **Scaler AI Labs — Environment Data Intern Role** assignment.

---

## Project Overview

The goal of this assignment is to process the provided 127-page `Red Herring Prospectus.docx` document, identify sensitive PII (names, emails, phone numbers, addresses, organizations, etc.), and generate a redacted Word document (`output/redacted_prospectus.docx`) where real PII is replaced with consistent fake alternatives.

The project also includes:
- A token-level evaluation script comparing detector output with ground truth annotations.
- A unit test suite covering detection, replacement consistency, and edge cases.
- A Streamlit web application where users can upload any `.docx` file and download the redacted version.

---

## Supported PII Categories

The tool supports 9 PII types:
1. `PERSON` — Names of promoters, directors, key executives
2. `EMAIL` — Email addresses
3. `PHONE` — Indian landlines and mobile numbers
4. `ORGANIZATION` — Company names, banks, law firms, trusts
5. `ADDRESS` — Physical and registered addresses
6. `SSN` — Social Security Numbers
7. `CREDIT_CARD` — Credit card numbers (validated via Luhn algorithm)
8. `DOB` — Dates of birth
9. `IP_ADDRESS` — IPv4 addresses

---

## How It Works

### 1. Detection Strategy
- **Regular Expressions for Structured Data**:
  - Emails: Regex for standard email syntax.
  - Phones: Regex covering Indian mobile formats (`+91 98...`) and STD codes (`020...`, `022...`). Filters out false positives like CIN/DIN numbers and currency values.
  - SSN: Standard US SSN format (`XXX-XX-XXXX`).
  - Credit Cards: Regex for 13–19 digit cards with a **Luhn check** to reject arbitrary numbers that aren't valid card numbers.
  - IP Addresses: Validated against 0–255 octet ranges.

- **Context Rules & spaCy NER for Unstructured Data**:
  - Names & Companies: Handled via labeled patterns (`Full Name:`, `Name:`, `Company:`) and spaCy NER (`en_core_web_sm`), combined with domain lists for key individuals and companies in the prospectus.
  - False Positive Filtering: Custom ignore sets filter out capitalized financial and legal headings (`Cap Price`, `Floor Price`, `Equity Shares`, `Board of Directors`) that spaCy frequently misclassifies as people or organizations.
  - Addresses: Detected via verified full addresses and labeled blocks (`Address:`) with 6-digit Indian PIN codes.
  - Date of Birth: Triggered only when preceded by birth-related keywords (`Date of Birth`, `DOB`, `born on`) to avoid capturing normal filing or financial dates.

### 2. Replacement Consistency
- Uses `Faker` (with `en_IN` locale and a fixed seed `42`) so replacements are reproducible.
- Maintains dictionaries mapping each unique sensitive entity to a single fake replacement.
- Normalizes casing so variations like `KUSHAL HEGDE` and `Kushal Hegde` receive the same fake name in their respective letter cases.
- Fake credit cards are generated with valid Luhn checksums and guaranteed not to equal the original value.

### 3. DOCX Structure Preservation
- Uses `python-docx` to iterate through all body paragraphs, table cells, headers, and footers.
- When an entity spans multiple XML runs inside Word, text is consolidated into the first run and subsequent matched runs are cleared.
- Multi-line addresses that span across consecutive paragraphs are detected and replaced cleanly across those paragraphs.

---

## Project Structure

```
pii-redaction-tool/
├── app.py                               # Streamlit web demo
├── run.py                               # Simple runner script
├── requirements.txt                     # Dependencies
├── README.md                            # Documentation
├── input/
│   └── Red Herring Prospectus.docx      # Input document
├── output/
│   └── redacted_prospectus.docx         # Redacted document output
├── evaluation/
│   ├── ground_truth.json                # Ground truth annotations
│   └── evaluation_report.md             # Token-level evaluation report
├── src/
│   ├── detectors.py                     # Detection logic (regex + context + spaCy)
│   ├── redactor.py                      # Faker replacement & DOCX redactor
│   ├── evaluator.py                     # Token-level evaluation against ground truth
│   └── main.py                          # Pipeline script
└── tests/
    └── test_detectors.py                # Unit test suite (31 tests)
```

---

## Installation & Setup

### Requirements
- Python 3.9 or higher

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/shahnawaz-khann/pii-redaction-tool.git
cd pii-redaction-tool

# 2. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install requirements
pip install -r requirements.txt

# 4. Download the spaCy model
python3 -m spacy download en_core_web_sm
```

---

## How to Run

### 1. Run the Full Redaction Pipeline

Make sure `Red Herring Prospectus.docx` is inside `input/`, then run:

```bash
python run.py
```

This will:
1. Extract text from paragraphs and tables.
2. Run PII detection.
3. Replace sensitive entities with fake data and save `output/redacted_prospectus.docx`.
4. Verify document structure.
5. Run token-level evaluation against `evaluation/ground_truth.json` and generate `evaluation/evaluation_report.md`.

### 2. Run the Unit Tests

```bash
pytest tests/test_detectors.py -v
```

### 3. Run the Streamlit Web App

```bash
streamlit run app.py
```

Live demo URL: [https://pii-redaction-tool-1.streamlit.app/](https://pii-redaction-tool-1.streamlit.app/)

---

## Evaluation Results

The evaluation is calculated at the **token level** over all **69,746 word tokens** in `Red Herring Prospectus.docx`, comparing predictions against `evaluation/ground_truth.json`.

### Overall Summary
- **Total Document Tokens**: `69,746`
- **True Positives (TP)**: `1,436` tokens
- **False Positives (FP)**: `493` tokens
- **False Negatives (FN)**: `37` tokens
- **True Negatives (TN)**: `67,780` tokens
- **Overall Accuracy**: **99.24%** (`0.9924`)
- **Overall Precision**: **74.44%** (`0.7444`)
- **Overall Recall**: **97.49%** (`0.9749`)
- **Overall F1 Score**: **84.42%** (`0.8442`)

### Category Breakdown

| PII Category | Actual (Tokens) | Predicted (Tokens) | TP | FP | FN | TN | Precision | Recall | F1 | Accuracy |
|---|---|---|---|---|---|---|---|---|---|---|
| **EMAIL** | 58 | 57 | 57 | 0 | 1 | 69,688 | 1.0000 | 0.9828 | 0.9913 | 1.0000 |
| **PHONE** | 36 | 36 | 36 | 0 | 0 | 69,710 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| **PERSON** | 591 | 736 | 591 | 145 | 0 | 69,010 | 0.8030 | 1.0000 | 0.8907 | 0.9979 |
| **ORGANIZATION** | 592 | 904 | 556 | 348 | 36 | 68,806 | 0.6150 | 0.9392 | 0.7433 | 0.9945 |
| **ADDRESS** | 196 | 196 | 196 | 0 | 0 | 69,550 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| **SSN** | 0 | 0 | 0 | 0 | 0 | 69,746 | N/A | N/A | N/A | N/A (0 doc instances) |
| **CREDIT_CARD** | 0 | 0 | 0 | 0 | 0 | 69,746 | N/A | N/A | N/A | N/A (0 doc instances) |
| **DOB** | 0 | 0 | 0 | 0 | 0 | 69,746 | N/A | N/A | N/A | N/A (0 doc instances) |
| **IP_ADDRESS** | 0 | 0 | 0 | 0 | 0 | 69,746 | N/A | N/A | N/A | N/A (0 doc instances) |
| **Total** | **1,473** | **1,929** | **1,436** | **493** | **37** | **67,780** | **0.7444** | **0.9749** | **0.8442** | **0.9924** |

> Note: `SSN`, `CREDIT_CARD`, `DOB`, and `IP_ADDRESS` have 0 instances in this specific prospectus document. Their detection logic is tested and verified in `tests/test_detectors.py`.

---

## Known Limitations & Tradeoffs

1. **spaCy Headings as Organizations**: Some all-caps section titles (e.g. `THE OFFER SHALL CONSTITUTE`, `SYNDICATE MEMBERS`) get tagged as ORGs by spaCy NER. An ignore list filters most common ones, but some capitalized phrases are still flagged (contributing to FP).
2. **Word XML Run Fragmentation**: When an entity crosses run boundaries within a paragraph or table cell, text is consolidated into the first run. This keeps paragraph structure intact while standardizing run styling across the entity.
3. **Local Execution**: All processing happens locally on CPU without external API calls.
