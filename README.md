# PII Redaction Tool

A lightweight Python document processing tool designed to detect personally identifiable information (PII) from Microsoft Word (`.docx`) documents and replace sensitive data with realistic, consistent fake alternatives.

Developed for the **Scaler AI Labs — Environment Data Intern Role** assignment, this project processes the supplied 127-page `Red Herring Prospectus.docx` and produces a fully redacted Word document (`output/redacted_prospectus.docx`) while preserving document structure and tables.

---

## Technical Approach

The tool employs a **hybrid detection strategy** combining regular expressions, named entity recognition (NER), and contextual rules:

1. **Regular Expressions (Structured PII)**
   - **Emails**: Regex-based detection for common email address formats such as `first.last@domain.com`.
   - **Phone Numbers**: Indian phone number patterns (`+91 9876543210`, `020 4505 3237`, `022-68052182`). Filters avoid matching financial figures, page numbers, CINs, and DINs.
   - **SSNs**: Standard US Social Security Number patterns (`123-45-6789`).
   - **Credit Cards**: 13–19 digit credit card patterns validated using the **Luhn algorithm** to eliminate false positives.
   - **IP Addresses**: Validated IPv4 addresses (`192.168.1.10`) with octet boundary checks (`0–255`).

2. **spaCy NER, Domain Rules & Filtering (Unstructured PII)**
   - **Person Names (`PERSON`)**: spaCy NER candidate extraction supplemented by domain entity lists and filtered against financial/prospectus terminology (`Cap Price`, `Floor Price`, `UPI Bidders`, `Equity Shares`, `Mutual Funds`).
   - **Company Names (`ORGANIZATION`)**: spaCy NER combined with corporate suffixes (`Limited`, `Ltd`, `LLP`, `Private Limited`, `Bank`, `Trust`) and filtered against legal document headers (`EQUITY`, `Bids`, `Anchor Investors`, `Board`, `Maharashtra`).
   - **Physical Addresses (`ADDRESS`)**: Verified full office address patterns and multi-line Indian office structures with PIN codes.
   - **Dates of Birth (`DOB`)**: Date regex triggered **only** when preceded by explicit birth context keywords (`Date of Birth`, `DOB`, `born on`). Ordinary financial or filing dates are left untouched.

3. **Deterministic Replacement Mapping**
   - Uses `Faker` with a fixed seed (`42`) to generate consistent fake alternatives.
   - Normalized keys (lowercase/strip) ensure that capitalization variants of the same entity receive the same fake identity (e.g. `KUSHAL SUBBAYYA HEGDE` and `Kushal Subbayya Hegde` → `Aryan Maharaj`).
   - Distinct phone replacements per unique original phone number.
   - Preserves name-email mapping consistency where applicable (`sarthak.malvadkar@...` → `daniel.mehta@example.com`).

4. **DOCX Document Processing**
   - Built on `python-docx`. Iterates across paragraphs, table cells, headers, and footers.
   - When an entity spans multiple XML runs in a cell or paragraph, text is consolidated into the first run to maintain structure, with a documented tradeoff on intra-entity run styling.

---

## Supported PII Categories

The system detects and redacts 9 PII categories:
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
│   └── ground_truth.json                # Verified ground truth JSON dataset
├── input/
│   └── .gitkeep                         # Placeholder (prospectus kept locally)
├── output/
│   └── .gitkeep                         # Placeholder (redacted docx kept locally)
├── src/
│   ├── detectors.py                     # Hybrid PII detection engine
│   ├── redactor.py                      # Faker replacement & DOCX redactor
│   ├── main.py                          # Core end-to-end pipeline runner
│   └── evaluator.py                     # Token-level evaluation & report generator
├── tests/
│   └── test_detectors.py                # Automated Pytest suite (31 unit tests)
├── .gitignore                           # Git ignore rules
├── README.md                            # Project documentation
├── app.py                               # Lightweight Streamlit demo interface
├── requirements.txt                     # Project dependencies
└── run.py                               # Pipeline entry point
```

---

## Installation & Setup

### Prerequisites
- Python 3.9+

### Setup Virtual Environment & Dependencies

```bash
# Clone the repository
git clone https://github.com/shahnawaz-khann/pii-redaction-tool.git
cd pii-redaction-tool

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install required packages
pip install -r requirements.txt

# Download spaCy English model
python3 -m spacy download en_core_web_sm
```

---

## Usage

### 1. Run the Main Redaction & Evaluation Pipeline

Place `Red Herring Prospectus.docx` inside the `input/` directory and execute:

```bash
python run.py
```

This runs the complete workflow:
1. Loads `input/Red Herring Prospectus.docx`.
2. Runs hybrid detectors across all paragraphs, tables, headers, and footers.
3. Generates consistent fake replacements using `Faker`.
4. Saves the redacted file to `output/redacted_prospectus.docx`.
5. Validates output DOCX integrity (paragraphs and table counts match).
6. Evaluates predictions against `evaluation/ground_truth.json` at the token level and generates `evaluation/evaluation_report.md`.

### 2. Run Automated Unit Tests

```bash
pytest tests/test_detectors.py
```

### 3. Run Streamlit Cloud / Web Demo Interface

```bash
streamlit run app.py
```

---

## Evaluation & Benchmark Results

The evaluation is calculated via **token-level classification** across all **69,746 whitespace-separated word tokens** in `Red Herring Prospectus.docx` compared against verified ground truth ([evaluation/ground_truth.json](evaluation/ground_truth.json)).

### Overall Performance Metrics

- **Total Document Tokens (N)**: `69,746`
- **True Positives (TP)**: `1,434` tokens
- **False Positives (FP)**: `493` tokens
- **False Negatives (FN)**: `39` tokens
- **True Negatives (TN)**: `67,780` tokens
- **Overall Accuracy**: `0.9924` (99.24%)
- **Overall Precision**: `0.7442` (74.42%)
- **Overall Recall**: `0.9735` (97.35%)
- **Overall F1 Score**: `0.8435` (84.35%)

### Per-Category Token Summary

| PII Category | Actual (Tokens) | Predicted (Tokens) | TP | FP | FN | TN | Precision | Recall | F1 | Accuracy |
|---|---|---|---|---|---|---|---|---|---|---|
| **EMAIL** | 58 | 57 | 57 | 0 | 1 | 69,688 | **1.0000** | 0.9828 | 0.9913 | 1.0000 |
| **PHONE** | 36 | 36 | 36 | 0 | 0 | 69,710 | **1.0000** | **1.0000** | **1.0000** | 1.0000 |
| **PERSON** | 591 | 736 | 591 | 145 | 0 | 69,010 | 0.8030 | **1.0000** | 0.8907 | 0.9979 |
| **ORGANIZATION** | 592 | 902 | 554 | 348 | 38 | 68,806 | 0.6142 | 0.9358 | 0.7416 | 0.9945 |
| **ADDRESS** | 196 | 196 | 196 | 0 | 0 | 69,550 | **1.0000** | **1.0000** | **1.0000** | 1.0000 |
| **SSN** | 0 | 0 | 0 | 0 | 0 | 69,746 | N/A | N/A | N/A | N/A (0 doc instances) |
| **CREDIT_CARD** | 0 | 0 | 0 | 0 | 0 | 69,746 | N/A | N/A | N/A | N/A (0 doc instances) |
| **DOB** | 0 | 0 | 0 | 0 | 0 | 69,746 | N/A | N/A | N/A | N/A (0 doc instances) |
| **IP_ADDRESS** | 0 | 0 | 0 | 0 | 0 | 69,746 | N/A | N/A | N/A | N/A (0 doc instances) |
| **Total** | **1,473** | **1,927** | **1,434** | **493** | **39** | **67,780** | **0.7442** | **0.9735** | **0.8435** | **0.9924** |

> **Note on Zero-Instance Categories**: `SSN`, `CREDIT_CARD`, `DOB`, and `IP_ADDRESS` contain 0 actual instances in the prospectus document text. Document-level recall, precision, and F1 are marked `N/A`. The underlying detection logic for these categories is validated via synthetic unit tests in `tests/test_detectors.py`.

For detailed error analysis and formulas, refer to [evaluation/evaluation_report.md](evaluation/evaluation_report.md).

---

## Practical Engineering Tradeoffs & Limitations

1. **Regex vs. spaCy NER**: In the evaluated prospectus, the structured PII detectors achieved 100% precision for the detected EMAIL, PHONE, and ADDRESS categories. Additional synthetic unit tests validate the remaining structured detectors. spaCy NER identifies broader entities like names and organizations, but incurs false positives from uppercase legal headings (`THE OFFER SHALL CONSTITUTE`, `SYNDICATE MEMBERS`).
2. **DOCX XML Run Splitting**: In Microsoft Word documents, text inside table cells can be fragmented into multiple XML run objects. When an entity crosses run boundaries, text is merged into the first run to maintain document layout, which may trade off subtle intra-word styling differences.
3. **Local Privacy**: Document processing is performed entirely locally without external LLM or cloud API dependencies, ensuring sensitive data never leaves the runtime environment.

---

## Streamlit Cloud Deployment

A lightweight web UI is implemented in `app.py` and deployed on Streamlit Cloud:
- **Live App URL**: [https://pii-redaction-tool-1.streamlit.app/](https://pii-redaction-tool-1.streamlit.app/)
- Allows users to upload a DOCX file.
- Displays privacy-safe entity detection counts (without logging sensitive raw data).
- Generates and provides a downloadable redacted DOCX file.
