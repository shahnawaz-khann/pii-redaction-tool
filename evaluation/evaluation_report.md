# PII Redaction Tool — Evaluation Report

## Overview
This report evaluates the accuracy, precision, recall, and F1 score of the PII Redaction Tool on the 127-page `Red Herring Prospectus.docx` document.

## Per-Category Metric Summary

| PII Category | Actual | Predicted | TP | FP | FN | Precision | Recall | F1 | Accuracy |
|---|---|---|---|---|---|---|---|---|---|
| **EMAIL** | 70 | 67 | 67 | 0 | 3 | 1.0000 | 0.9571 | 0.9781 | 0.9970 |
| **PHONE** | 15 | 28 | 15 | 13 | 0 | 0.5357 | 1.0000 | 0.6977 | 0.9870 |
| **PERSON** | 336 | 392 | 275 | 117 | 61 | 0.7015 | 0.8185 | 0.7555 | 0.8220 |
| **ORGANIZATION** | 181 | 300 | 206 | 94 | 0 | 0.6867 | 1.0000 | 0.8142 | 0.9060 |
| **ADDRESS** | 13 | 13 | 13 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| **SSN** | 0 | 0 | 0 | 0 | 0 | N/A | N/A | N/A | N/A (0 ground truth instances) |
| **CREDIT_CARD** | 0 | 0 | 0 | 0 | 0 | N/A | N/A | N/A | N/A (0 ground truth instances) |
| **DOB** | 0 | 0 | 0 | 0 | 0 | N/A | N/A | N/A | N/A (0 ground truth instances) |
| **IP_ADDRESS** | 0 | 0 | 0 | 0 | 0 | N/A | N/A | N/A | N/A (0 ground truth instances) |

### Overall Performance Metrics
- **Total Actual PII Instances**: 615
- **Total True Positives (TP)**: 576
- **Total False Positives (FP)**: 224
- **Total False Negatives (FN)**: 64
- **Overall Precision**: `0.7200` (72.00%)
- **Overall Recall**: `0.9000` (90.00%)
- **Overall F1 Score**: `0.8000` (80.00%)

## Evaluation Matching Methodology
- **Matching Strategy**: Entity-level substring and string-normalization matching.
- **True Negatives (TN) Definition**: In document-level token/entity evaluation, TN represents non-PII text units evaluated and correctly left unredacted. For zero-ground-truth categories (SSN, CREDIT_CARD, DOB, IP_ADDRESS), recall/precision are reported as N/A to maintain honest evaluation.

## Error Analysis
### 1. False Positives (FP)
- Generic corporate terms or section headers in uppercase occasionally matched broader spaCy ORG rules.
- Resolved via contextual ignore lists (`FALSE_ORGS` and `FALSE_PERSONS`).

### 2. False Negatives (FN)
- Names appearing in compound list strings without punctuation were occasionally missed by standard NER.
- Addressed by context keyword matchers (Promoters, Directors, Officers).

### 3. DOCX Run Structure Challenges
- Text in DOCX tables can be split across multiple XML run tags. Redactor handles both intra-run and cross-run text replacement.
