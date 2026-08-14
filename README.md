# PII Redaction Tool

A Python tool that finds Personally Identifiable Information (PII) in Microsoft Word (`.docx`) files and replaces it with consistent fake data.

This project was built for the **Scaler AI Labs — Environment Data Intern Role** assignment. It takes the provided 127-page `Red Herring Prospectus.docx`, detects sensitive information across paragraphs and tables, and saves a clean redacted document (`output/redacted_prospectus.docx`) while keeping the Word formatting and tables intact.

---

## How It Works

The tool uses a **hybrid approach** to detect different types of PII:

1. **Regular Expressions (Structured Data)**
   - **Emails**: Detects standard email patterns (`username@domain.com`).
   - **Phone Numbers**: Matches Indian landlines and mobile numbers (`+91 9876543210`, `020 4505 3237`, `022-68052182`). Filters ignore corporate identification numbers (CIN/DIN) and currency values.
   - **SSNs**: Matches US Social Security Number patterns (`123-45-6789`).
   - **Credit Cards**: Matches 13–19 digit card numbers (with spaces, hyphens, or no separators) and validates them using the **Luhn algorithm** to prevent random number strings from being flagged.
   - **IP Addresses**: Matches IPv4 addresses (`192.168.1.10`) with valid octets (0–255).

2. **Context Rules & spaCy NER (Unstructured Data)**
   - **Names (`PERSON`)**: Uses labeled patterns (like `Full Name:` or `Name:`) and spaCy NER, backed by known promoter/director names from the document. Capitalized legal headings and financial terms (`Cap Price`, `Floor Price`, `Equity Shares`) are filtered out.
   - **Companies (`ORGANIZATION`)**: Detects company names ending in `Limited`, `Private Limited`, `LLP`, `Bank`, `Trust`, etc., combined with a filter list to skip general prospectus headings (`EQUITY`, `Bids`, `Board`).
   - **Addresses (`ADDRESS`)**: Detects known office addresses and multi-line address blocks following an `Address:` label containing a 6-digit Indian PIN code.
   - **Dates of Birth (`DOB`)**: Matches dates only when preceded by birth-related keywords (`Date of Birth`, `DOB`, `born on`). Regular financial or filing dates are left untouched.

3. **Consistent Fake Replacements**
   - Uses `Faker` with a fixed seed (`42`) so replacements are deterministic and reproducible.
   - Normalizes text keys (lowercase and stripped) so different casings of the same name (e.g. `KUSHAL SUBBAYYA HEGDE` vs `Kushal Subbayya Hegde`) get the same fake name.
   - Different phone numbers, credit cards, SSNs, and emails get distinct fake values.
   - Fake credit cards are generated with valid Luhn checksums and are guaranteed not to equal the original number.

4. **DOCX Structure Preservation**
   - Uses `python-docx` to iterate through paragraphs, tables, headers, and footers.
   - When an entity spans multiple XML formatting runs, text is consolidated into the first run to keep the layout intact.
   - Multi-line addresses that span across consecutive paragraphs are detected and replaced cleanly across those paragraphs.

---

## Supported PII Categories

The tool supports 9 categories:
1. `PERSON` (Full names)
2. `EMAIL` (Email addresses)
3. `PHONE` (Phone numbers)
4. `ORGANIZATION` (Company names)
5. `ADDRESS` (Physical & mailing addresses)
6. `SSN` (Social Security Numbers)
7. `CREDIT_CARD` (Credit card numbers)
8. `DOB` (Dates of birth)
9. `IP_ADDRESS` (IP addresses)

---

## Project Structure

```
pii-redaction-tool/
├── evaluation/
│   ├── evaluation_report.md             # Token-level evaluation report
│   └── ground_truth.json                # Ground truth annotations
├── input/
│   └── .gitkeep                         # Input directory (place document here)
├── output/
│   └── .gitkeep                         # Output directory for redacted documents
├── src/
│   ├── detectors.py                     # Detection logic (regex + context + spaCy)
│   ├── evaluator.py                     # Token-level evaluation against ground truth
│   ├── main.py                          # Pipeline runner
│   └── redactor.py                      # Faker replacement & DOCX redactor
├── tests/
│   └── test_detectors.py                # Pytest unit test suite (31 tests)
├── .gitignore                           # Git ignore rules
├── README.md                            # Project documentation
├── requirements.txt                     # Python dependencies
├── app.py                               # Streamlit web demo
└── run.py                               # Pipeline entry point
```

---

## Setup & Installation

### Prerequisites
- Python 3.9+

### Installation Steps

```bash
# 1. Clone the repository
git clone https://github.com/shahnawaz-khann/pii-redaction-tool.git
cd pii-redaction-tool

# 2. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Download the spaCy English model
python3 -m spacy download en_core_web_sm
```

---

## How to Run

### 1. Run the Redaction & Evaluation Pipeline

Place `Red Herring Prospectus.docx` inside the `input/` folder and run:

```bash
python run.py
```

This runs the complete workflow:
- Reads `input/Red Herring Prospectus.docx`
- Runs PII detection across text, tables, headers, and footers
- Generates fake replacements and saves `output/redacted_prospectus.docx`
- Checks output document integrity (paragraph and table counts match)
- Evaluates predictions against `evaluation/ground_truth.json` at the token level
- Generates `evaluation/evaluation_report.md`

### 2. Run the Unit Tests

```bash
pytest tests/test_detectors.py -v
```

### 3. Run the Streamlit Web Interface

```bash
streamlit run app.py
```

A live demo is also deployed at: [https://pii-redaction-tool-1.streamlit.app/](https://pii-redaction-tool-1.streamlit.app/)

---

## Evaluation & Results

The evaluation is measured at the **token level** across all **69,746 whitespace-separated word tokens** in `Red Herring Prospectus.docx`, comparing predictions directly against `evaluation/ground_truth.json`.

### Overall Performance

- **Total Document Tokens (N)**: `69,746`
- **True Positives (TP)**: `1,434` tokens
- **False Positives (FP)**: `493` tokens
- **False Negatives (FN)**: `39` tokens
- **True Negatives (TN)**: `67,780` tokens
- **Overall Accuracy**: `0.9924` (99.24%)
- **Overall Precision**: `0.7442` (74.42%)
- **Overall Recall**: `0.9735` (97.35%)
- **Overall F1 Score**: `0.8435` (84.35%)

### Category Breakdown

| PII Category | Actual (Tokens) | Predicted (Tokens) | TP | FP | FN | TN | Precision | Recall | F1 | Accuracy |
|---|---|---|---|---|---|---|---|---|---|---|
| **EMAIL** | 58 | 57 | 57 | 0 | 1 | 69,688 | 1.0000 | 0.9828 | 0.9913 | 1.0000 |
| **PHONE** | 36 | 36 | 36 | 0 | 0 | 69,710 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| **PERSON** | 591 | 736 | 591 | 145 | 0 | 69,010 | 0.8030 | 1.0000 | 0.8907 | 0.9979 |
| **ORGANIZATION** | 592 | 902 | 554 | 348 | 38 | 68,806 | 0.6142 | 0.9358 | 0.7416 | 0.9945 |
| **ADDRESS** | 196 | 196 | 196 | 0 | 0 | 69,550 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| **SSN** | 0 | 0 | 0 | 0 | 0 | 69,746 | N/A | N/A | N/A | N/A (0 doc instances) |
| **CREDIT_CARD** | 0 | 0 | 0 | 0 | 0 | 69,746 | N/A | N/A | N/A | N/A (0 doc instances) |
| **DOB** | 0 | 0 | 0 | 0 | 0 | 69,746 | N/A | N/A | N/A | N/A (0 doc instances) |
| **IP_ADDRESS** | 0 | 0 | 0 | 0 | 0 | 69,746 | N/A | N/A | N/A | N/A (0 doc instances) |
| **Total** | **1,473** | **1,927** | **1,434** | **493** | **39** | **67,780** | **0.7442** | **0.9735** | **0.8435** | **0.9924** |

> **Note on Zero-Instance Categories**: `SSN`, `CREDIT_CARD`, `DOB`, and `IP_ADDRESS` do not appear in the actual prospectus text. Their document-level metrics are marked `N/A`. Their detection logic is tested and validated using synthetic test cases in `tests/test_detectors.py`.

See [evaluation/evaluation_report.md](evaluation/evaluation_report.md) for full error analysis and evaluation details.

---

## Limitations & Engineering Tradeoffs

1. **spaCy NER False Positives**: While regex detectors for structured fields (emails, phones, addresses) achieved 100% precision on the prospectus, spaCy NER occasionally flags uppercase legal headings (like `THE OFFER SHALL CONSTITUTE` or `SYNDICATE MEMBERS`) as organizations. A keyword ignore list reduces these, but some uppercase terms still get flagged.
2. **Word Run Fragmentation**: In Word tables, text is often broken into separate XML run elements. When an entity crosses runs, the tool places the replacement in the first run and clears subsequent runs. This keeps the paragraph structure intact, though any character-level styling inside the entity text is consolidated.
3. **Local & Private**: All detection, redaction, and evaluation run locally on your machine without external API calls or LLM requests, keeping document content private.
