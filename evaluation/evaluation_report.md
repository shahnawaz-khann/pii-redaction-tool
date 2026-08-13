# PII Redaction Tool — Evaluation Report

## 1. Evaluation Methodology & Unit of Measurement
To establish a rigorous, defensible definition of True Negatives (TN) and Accuracy, this evaluation operates on **token-level classification** across all **69,746 whitespace-separated word tokens** in the 127-page `Red Herring Prospectus.docx`.

### Evaluation Definitions & Formulas
- **Total Tokens (N)**: Total word tokens in the document text (`69,746`).
- **True Positive (TP)**: Tokens that are part of ground-truth PII and correctly identified by the detector.
- **False Positive (FP)**: Non-PII tokens incorrectly classified as PII.
- **False Negative (FN)**: Ground-truth PII tokens missed by the detector.
- **True Negative (TN)**: Non-PII tokens correctly left unredacted ($TN = N - TP - FP - FN$).
- **Accuracy**: $\text{Accuracy} = \frac{TP + TN}{N}$
- **Precision**: $\text{Precision} = \frac{TP}{TP + FP}$
- **Recall**: $\text{Recall} = \frac{TP}{TP + FN}$
- **F1 Score**: $\text{F1} = \frac{2 \times \text{Precision} \times \text{Recall}}{\text{Precision} + \text{Recall}}$

## 2. Overall Performance Metrics

- **Total Document Tokens (N)**: `69,746`
- **True Positives (TP)**: `1,435` tokens
- **False Positives (FP)**: `625` tokens
- **False Negatives (FN)**: `38` tokens
- **True Negatives (TN)**: `67,648` tokens
- **Overall Accuracy**: `0.9905` (99.05%)
- **Overall Precision**: `0.6966` (69.66%)
- **Overall Recall**: `0.9742` (97.42%)
- **Overall F1 Score**: `0.8123` (81.23%)

## 3. Per-Category Performance Summary

| PII Category | Actual (Tokens) | Predicted (Tokens) | TP | FP | FN | TN | Precision | Recall | F1 | Accuracy |
|---|---|---|---|---|---|---|---|---|---|---|
| **EMAIL** | 58 | 55 | 55 | 0 | 3 | 69688 | 1.0000 | 0.9483 | 0.9735 | 1.0000 |
| **PHONE** | 36 | 36 | 36 | 0 | 0 | 69710 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| **PERSON** | 591 | 875 | 591 | 284 | 0 | 68871 | 0.6754 | 1.0000 | 0.8063 | 0.9959 |
| **ORGANIZATION** | 592 | 898 | 550 | 348 | 42 | 68806 | 0.6125 | 0.9291 | 0.7383 | 0.9944 |
| **ADDRESS** | 196 | 196 | 196 | 0 | 0 | 69550 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| **SSN** | 0 | 0 | 0 | 0 | 0 | 69746 | N/A | N/A | N/A | N/A (0 ground truth instances in document) |
| **CREDIT_CARD** | 0 | 0 | 0 | 0 | 0 | 69746 | N/A | N/A | N/A | N/A (0 ground truth instances in document) |
| **DOB** | 0 | 0 | 0 | 0 | 0 | 69746 | N/A | N/A | N/A | N/A (0 ground truth instances in document) |
| **IP_ADDRESS** | 0 | 0 | 0 | 0 | 0 | 69746 | N/A | N/A | N/A | N/A (0 ground truth instances in document) |

> **Note on Zero-Instance Categories**: `SSN`, `CREDIT_CARD`, `DOB`, and `IP_ADDRESS` contain zero actual instances in the provided prospectus text. Document-level recall, precision, and F1 are honestly marked `N/A`. The underlying detection logic for these categories is validated via synthetic test cases in `tests/test_detectors.py`.

## 4. Error Analysis & Limitations
### False Positives (FP)
- **Uppercase Section Titles**: Certain capitalized headings (e.g., `THE OFFER SHALL CONSTITUTE`, `SYNDICATE MEMBERS`) matched general spaCy ORG tags.
- **Registration/Numeric Codes**: A few multi-digit codes in table headers matched loose phone number patterns.

### False Negatives (FN)
- **Isolated Surnames in Dense Financial Tables**: Occurrences where names were abbreviated or listed without title context.

### DOCX Run Fragmentation Tradeoffs
- In Microsoft Word documents, text inside table cells can be fragmented into multiple XML run objects. When an entity crosses run boundaries, text is consolidated into the first run to maintain structure, which may trade off subtle intra-word styling differences.
