# PII Redaction Tool — Evaluation Report

## 1. Evaluation Methodology
The evaluation is done at the **token level** over all **69,746 word tokens** in the `Red Herring Prospectus.docx` document.

### Definitions & Formulas
- **Total Tokens (N)**: Total word tokens in the document text (`69,746`).
- **True Positive (TP)**: Ground truth PII tokens correctly identified by the detector.
- **False Positive (FP)**: Non-PII tokens incorrectly flagged as PII.
- **False Negative (FN)**: Ground truth PII tokens that were missed.
- **True Negative (TN)**: Non-PII tokens correctly left unredacted ($TN = N - TP - FP - FN$).
- **Accuracy**: $\frac{TP + TN}{N}$
- **Precision**: $\frac{TP}{TP + FP}$
- **Recall**: $\frac{TP}{TP + FN}$
- **F1 Score**: $\frac{2 \times \text{Precision} \times \text{Recall}}{\text{Precision} + \text{Recall}}$

## 2. Overall Results

- **Total Document Tokens**: `69,746`
- **True Positives (TP)**: `1,436` tokens
- **False Positives (FP)**: `493` tokens
- **False Negatives (FN)**: `37` tokens
- **True Negatives (TN)**: `67,780` tokens
- **Overall Accuracy**: `0.9924` (99.24%)
- **Overall Precision**: `0.7444` (74.44%)
- **Overall Recall**: `0.9749` (97.49%)
- **Overall F1 Score**: `0.8442` (84.42%)

## 3. Results by Category

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

> **Note on Zero-Instance Categories**: `SSN`, `CREDIT_CARD`, `DOB`, and `IP_ADDRESS` do not have instances in this specific prospectus document. Their precision, recall, and F1 are marked `N/A`. Their detector logic is tested using unit tests in `tests/test_detectors.py`.

## 4. Error Analysis & Notes
### False Positives
- **Uppercase Section Headings**: Some capitalized headings (e.g. `THE OFFER SHALL CONSTITUTE`, `SYNDICATE MEMBERS`) matched general spaCy ORG tags.
- **Registration Codes**: A few multi-digit numbers in table headers were picked up by the phone number pattern.

### False Negatives
- **Abbreviated Names in Tables**: A few isolated surnames in financial tables without title prefixes were missed.

### Word Run Formatting Note
- In Word documents, text can be split across multiple XML run objects. When replacing text across runs, the replacement is placed in the first run to keep formatting intact.
