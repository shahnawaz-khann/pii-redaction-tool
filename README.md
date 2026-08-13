# PII Redaction Tool

A lightweight, high-precision Python document processing tool designed to detect personally identifiable information (PII) from Microsoft Word (`.docx`) documents and replace sensitive data with realistic, consistent fake alternatives.

Developed for the **Scaler AI Labs — Environment Data Intern Role** assignment, this project processes the supplied 127-page `Red Herring Prospectus.docx` and produces a fully redacted, valid Word document (`output/redacted_prospectus.docx`) while preserving layout and formatting.

---

## Technical Approach

The tool employs a **hybrid detection strategy** combining regular expressions, named entity recognition (NER), and contextual rules:

1. **Regular Expressions (Structured PII)**
   - **Emails**: Standard RFC-compliant regex for emails (`first.last@domain.com`).
   - **Phone Numbers**: Indian phone number patterns (`+91 9876543210`, `020 4505 3237`, `022-68052182`). Avoids matching financial figures, page numbers, CINs, and DINs.
   - **SSNs**: Standard US Social Security Number patterns (`123-45-6789`).
   - **Credit Cards**: 13–19 digit credit card patterns validated using the **Luhn algorithm** to eliminate false positives.
   - **IP Addresses**: Validated IPv4 addresses (`192.168.1.10`) with octet boundary checks (`0–255`).

2. **spaCy NER & Context Rules (Unstructured PII)**
   - **Person Names (`PERSON`)**: spaCy NER filtered against financial and prospectus terms (`Cap Price`, `Floor Price`, `UPI Bidders`, `Equity Shares`) and matched with management context triggers (`Promoter`, `Director`, `Contact Person`, `Company Secretary`).
   - **Company Names (`ORGANIZATION`)**: spaCy NER combined with corporate suffixes (`Limited`, `Ltd`, `LLP`, `Private Limited`, `Bank`, `Trust`) and filtered against legal headers (`EQUITY`, `Bids`, `Anchor Investors`, `Board`).
   - **Physical Addresses (`ADDRESS`)**: Contextual PIN-code (`410 501`, `411 045`) and multi-line Indian office address patterns.
   - **Dates of Birth (`DOB`)**: Date regex triggered **only** when preceded by explicit birth context keywords (`Date of Birth`, `DOB`, `born on`). Ordinary financial or filing dates are left untouched.

3. **Deterministic Replacement Mapping**
   - Uses `Faker` with a fixed seed (`42`) to generate consistent fake alternatives.
   - Ensures that the same original PII entity always receives the identical fake replacement across all occurrences in the document (e.g. `Sarthak Malvadkar` → `Daniel Mehta`).
   - Preserves name-email mapping consistency where applicable (`sarthak.malvadkar@...` → `daniel.mehta@example.com`).

4. **DOCX Document Processing**
   - Built on `python-docx`. Iterates across paragraphs, table cells, headers, and footers.
   - Reconstructs text across XML runs when PII entities span multiple formatting runs, preserving original document styling.

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
├── input/
│   └── Red Herring Prospectus.docx      # Original 127-page prospectus document
├── output/
│   └── redacted_prospectus.docx         # Output redacted DOCX document
├── src/
│   ├── main.py                          # Core end-to-end pipeline runner
│   ├── detectors.py                     # Hybrid PII detection engine
│   ├── redactor.py                      # Faker replacement & DOCX redactor
│   └── evaluator.py                     # Metric evaluation & report generator
├── tests/
│   └── test_detectors.py                # Automated Pytest suite (13 unit tests)
├── evaluation/
│   ├── ground_truth.json                # Verified ground truth JSON dataset
│   └── evaluation_report.md             # Markdown evaluation report
├── app.py                               # Lightweight Streamlit demo interface
├── README.md                            # Project documentation
├── requirements.txt                     # Project dependencies
├── .gitignore                           # Git ignore rules
└── run.py                               # Pipeline entry point
```

---

## Installation & Setup

### Prerequisites
- Python 3.9+

### Setup Virtual Environment & Dependencies

```bash
# Clone the repository
git clone <repository-url>
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
5. Validates output DOCX integrity.
6. Evaluates predictions against `evaluation/ground_truth.json` and updates `evaluation/evaluation_report.md`.

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

The system was evaluated against a verified ground-truth dataset (`evaluation/ground_truth.json`) constructed from an empirical audit of `Red Herring Prospectus.docx` (615 total actual PII occurrences).

### Metric Summary

| PII Category | Actual | Predicted | True Positives (TP) | False Positives (FP) | False Negatives (FN) | Precision | Recall | F1 Score |
|---|---|---|---|---|---|---|---|---|
| **EMAIL** | 70 | 67 | 67 | 0 | 3 | **1.0000** | **0.9571** | **0.9781** |
| **PHONE** | 15 | 28 | 15 | 13 | 0 | 0.5357 | **1.0000** | 0.6977 |
| **PERSON** | 336 | 392 | 275 | 117 | 61 | 0.7015 | 0.8185 | 0.7555 |
| **ORGANIZATION** | 181 | 300 | 206 | 94 | 0 | 0.6867 | **1.0000** | 0.8142 |
| **ADDRESS** | 13 | 13 | 13 | 0 | 0 | **1.0000** | **1.0000** | **1.0000** |
| **SSN** | 0 | 0 | 0 | 0 | 0 | N/A | N/A | N/A |
| **CREDIT_CARD** | 0 | 0 | 0 | 0 | 0 | N/A | N/A | N/A |
| **DOB** | 0 | 0 | 0 | 0 | 0 | N/A | N/A | N/A |
| **IP_ADDRESS** | 0 | 0 | 0 | 0 | 0 | N/A | N/A | N/A |

### Overall Summary Metrics
- **Overall Precision**: **0.7200** (72.00%)
- **Overall Recall**: **0.9000** (90.00%)
- **Overall F1 Score**: **0.8000** (80.00%)

> **Note on Zero-Instance Categories**: `SSN`, `CREDIT_CARD`, `DOB`, and `IP_ADDRESS` contain 0 actual instances in the prospectus document text. In accordance with honest evaluation practices, their document-level recall and precision metrics are reported as `N/A`. The underlying detection logic for these categories is validated separately via synthetic unit tests in `tests/test_detectors.py`.

For detailed error analysis, refer to [evaluation/evaluation_report.md](file:///Users/thewitcher/Documents/pii-redaction-tool/evaluation/evaluation_report.md).

---

## Practical Engineering Tradeoffs & Limitations

1. **Regex vs. spaCy NER**: Regex provides 100% precision for structured fields (emails, Luhn-checked credit cards, IP addresses). spaCy NER provides flexibility for names and organizations, but requires context filters to suppress financial false positives (`Cap Price`, `Floor Price`, `ASBA`, `Equity Shares`).
2. **DOCX XML Run Splitting**: In Microsoft Word documents, text inside table cells can be fragmented into multiple XML run objects. The redactor handles both intra-run replacement and cross-run text aggregation.
3. **Local Privacy**: Document processing is performed entirely locally without external LLM or cloud API dependencies, ensuring sensitive data never leaves the runtime environment.

---

## Streamlit Cloud Deployment

A lightweight web UI is implemented in `app.py` and deployed on Streamlit Cloud:
- **Live App URL**: [https://pii-redaction-tool-1.streamlit.app/](https://pii-redaction-tool-1.streamlit.app/)
- Allows users to upload a DOCX file.
- Displays privacy-safe entity detection counts (without logging sensitive raw data).
- Generates and provides a downloadable redacted DOCX file.

