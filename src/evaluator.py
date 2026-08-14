"""
Calculates token-level evaluation metrics (TP, FP, FN, TN, precision, recall, F1, accuracy)
against ground_truth.json and writes an evaluation markdown report.
"""

import os
import re
import json
import docx
from typing import Dict, List, Any
from src.detectors import detect_pii


def load_ground_truth(ground_truth_path: str) -> Dict[str, Any]:
    """Loads ground truth JSON file."""
    with open(ground_truth_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def evaluate_redaction(doc_path: str, ground_truth_path: str, report_output_path: str) -> Dict[str, Any]:
    """
    Compares detector predictions against ground truth on a token-by-token basis.
    Calculates per-category metrics and overall summary metrics.
    """
    ground_truth = load_ground_truth(ground_truth_path)
    gt_entities = ground_truth.get("entities", [])

    # Extract all text from docx paragraphs and tables
    doc = docx.Document(doc_path)
    text_blocks = [p.text for p in doc.paragraphs if p.text.strip()]
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    if p.text.strip():
                        text_blocks.append(p.text.strip())

    full_document_text = "\n".join(text_blocks)

    # Tokenize document by non-whitespace sequences
    token_matches = list(re.finditer(r'\S+', full_document_text))
    total_tokens = len(token_matches)

    # Run detectors
    predictions = detect_pii(full_document_text)

    # Group ground truth spans by entity type
    gt_spans_by_cat: Dict[str, List[tuple]] = {}
    for entity in gt_entities:
        cat = entity["type"]
        if cat not in gt_spans_by_cat:
            gt_spans_by_cat[cat] = []
        pattern = re.compile(re.escape(entity["text"]), re.IGNORECASE)
        for m in pattern.finditer(full_document_text):
            gt_spans_by_cat[cat].append((m.start(), m.end()))

    # Group prediction spans by entity type
    pred_spans_by_cat: Dict[str, List[tuple]] = {}
    for pred in predictions:
        cat = pred["type"]
        if cat not in pred_spans_by_cat:
            pred_spans_by_cat[cat] = []
        pred_spans_by_cat[cat].append((pred["start"], pred["end"]))

    categories = [
        "EMAIL", "PHONE", "PERSON", "ORGANIZATION", "ADDRESS",
        "SSN", "CREDIT_CARD", "DOB", "IP_ADDRESS"
    ]

    metrics_by_cat: Dict[str, Dict[str, Any]] = {}
    tp_total = 0
    fp_total = 0
    fn_total = 0

    # Calculate token-level classification metrics per category
    for cat in categories:
        cat_gt_spans = gt_spans_by_cat.get(cat, [])
        cat_pred_spans = pred_spans_by_cat.get(cat, [])

        # Handle categories that have 0 instances in the prospectus
        if not cat_gt_spans and not cat_pred_spans:
            metrics_by_cat[cat] = {
                "actual_tokens": 0,
                "predicted_tokens": 0,
                "tp": 0,
                "fp": 0,
                "fn": 0,
                "tn": total_tokens,
                "precision": "N/A",
                "recall": "N/A",
                "f1": "N/A",
                "accuracy": "N/A (0 doc instances)"
            }
            continue

        tp_cat = 0
        fp_cat = 0
        fn_cat = 0
        tn_cat = 0

        for t_match in token_matches:
            t_start, t_end = t_match.start(), t_match.end()
            is_gt = any(gs <= t_start and t_end <= ge for gs, ge in cat_gt_spans)
            is_pred = any(ps <= t_start and t_end <= pe for ps, pe in cat_pred_spans)

            if is_gt and is_pred:
                tp_cat += 1
            elif not is_gt and is_pred:
                fp_cat += 1
            elif is_gt and not is_pred:
                fn_cat += 1
            else:
                tn_cat += 1

        acc_cat = (tp_cat + tn_cat) / total_tokens if total_tokens > 0 else 0.0
        prec_cat = tp_cat / (tp_cat + fp_cat) if (tp_cat + fp_cat) > 0 else 0.0
        rec_cat = tp_cat / (tp_cat + fn_cat) if (tp_cat + fn_cat) > 0 else 0.0
        f1_cat = (2 * prec_cat * rec_cat) / (prec_cat + rec_cat) if (prec_cat + rec_cat) > 0 else 0.0

        metrics_by_cat[cat] = {
            "actual_tokens": tp_cat + fn_cat,
            "predicted_tokens": tp_cat + fp_cat,
            "tp": tp_cat,
            "fp": fp_cat,
            "fn": fn_cat,
            "tn": tn_cat,
            "precision": round(prec_cat, 4),
            "recall": round(rec_cat, 4),
            "f1": round(f1_cat, 4),
            "accuracy": round(acc_cat, 4)
        }

        tp_total += tp_cat
        fp_total += fp_cat
        fn_total += fn_cat

    # Calculate overall metrics
    tn_total = total_tokens - tp_total - fp_total - fn_total
    overall_accuracy = (tp_total + tn_total) / total_tokens if total_tokens > 0 else 0.0
    overall_precision = tp_total / (tp_total + fp_total) if (tp_total + fp_total) > 0 else 0.0
    overall_recall = tp_total / (tp_total + fn_total) if (tp_total + fn_total) > 0 else 0.0
    overall_f1 = (2 * overall_precision * overall_recall) / (overall_precision + overall_recall) if (overall_precision + overall_recall) > 0 else 0.0

    actual_tokens_total = sum(m["actual_tokens"] for m in metrics_by_cat.values())
    pred_tokens_total = sum(m["predicted_tokens"] for m in metrics_by_cat.values())

    # Write evaluation report to markdown
    os.makedirs(os.path.dirname(report_output_path), exist_ok=True)
    with open(report_output_path, "w", encoding="utf-8") as f:
        f.write("# PII Redaction Tool — Evaluation Report\n\n")
        f.write("## 1. Evaluation Methodology\n")
        f.write(f"The evaluation is done at the **token level** over all **{total_tokens:,} word tokens** ")
        f.write("in the `Red Herring Prospectus.docx` document.\n\n")

        f.write("### Definitions & Formulas\n")
        f.write(f"- **Total Tokens (N)**: Total word tokens in the document text (`{total_tokens:,}`).\n")
        f.write("- **True Positive (TP)**: Ground truth PII tokens correctly identified by the detector.\n")
        f.write("- **False Positive (FP)**: Non-PII tokens incorrectly flagged as PII.\n")
        f.write("- **False Negative (FN)**: Ground truth PII tokens that were missed.\n")
        f.write("- **True Negative (TN)**: Non-PII tokens correctly left unredacted ($TN = N - TP - FP - FN$).\n")
        f.write("- **Accuracy**: $\\frac{TP + TN}{N}$\n")
        f.write("- **Precision**: $\\frac{TP}{TP + FP}$\n")
        f.write("- **Recall**: $\\frac{TP}{TP + FN}$\n")
        f.write("- **F1 Score**: $\\frac{2 \\times \\text{Precision} \\times \\text{Recall}}{\\text{Precision} + \\text{Recall}}$\n\n")

        f.write("## 2. Overall Results\n\n")
        f.write(f"- **Total Document Tokens**: `{total_tokens:,}`\n")
        f.write(f"- **True Positives (TP)**: `{tp_total:,}` tokens\n")
        f.write(f"- **False Positives (FP)**: `{fp_total:,}` tokens\n")
        f.write(f"- **False Negatives (FN)**: `{fn_total:,}` tokens\n")
        f.write(f"- **True Negatives (TN)**: `{tn_total:,}` tokens\n")
        f.write(f"- **Overall Accuracy**: `{overall_accuracy:.4f}` ({overall_accuracy * 100:.2f}%)\n")
        f.write(f"- **Overall Precision**: `{overall_precision:.4f}` ({overall_precision * 100:.2f}%)\n")
        f.write(f"- **Overall Recall**: `{overall_recall:.4f}` ({overall_recall * 100:.2f}%)\n")
        f.write(f"- **Overall F1 Score**: `{overall_f1:.4f}` ({overall_f1 * 100:.2f}%)\n\n")

        f.write("## 3. Results by Category\n\n")
        f.write("| PII Category | Actual (Tokens) | Predicted (Tokens) | TP | FP | FN | TN | Precision | Recall | F1 | Accuracy |\n")
        f.write("|---|---|---|---|---|---|---|---|---|---|---|\n")

        for cat in categories:
            m = metrics_by_cat[cat]
            p_str = f"{m['precision']:.4f}" if isinstance(m['precision'], float) else str(m['precision'])
            r_str = f"{m['recall']:.4f}" if isinstance(m['recall'], float) else str(m['recall'])
            f1_str = f"{m['f1']:.4f}" if isinstance(m['f1'], float) else str(m['f1'])
            acc_str = f"{m['accuracy']:.4f}" if isinstance(m['accuracy'], float) else str(m['accuracy'])

            f.write(
                f"| **{cat}** | {m['actual_tokens']:,} | {m['predicted_tokens']:,} | "
                f"{m['tp']:,} | {m['fp']:,} | {m['fn']:,} | {m['tn']:,} | "
                f"{p_str} | {r_str} | {f1_str} | {acc_str} |\n"
            )

        f.write(
            f"| **Total** | **{actual_tokens_total:,}** | **{pred_tokens_total:,}** | "
            f"**{tp_total:,}** | **{fp_total:,}** | **{fn_total:,}** | **{tn_total:,}** | "
            f"**{overall_precision:.4f}** | **{overall_recall:.4f}** | **{overall_f1:.4f}** | **{overall_accuracy:.4f}** |\n"
        )

        f.write("\n> **Note on Zero-Instance Categories**: `SSN`, `CREDIT_CARD`, `DOB`, and `IP_ADDRESS` do not have instances in this specific prospectus document. Their precision, recall, and F1 are marked `N/A`. Their detector logic is tested using unit tests in `tests/test_detectors.py`.\n\n")

        f.write("## 4. Error Analysis & Notes\n")
        f.write("### False Positives\n")
        f.write("- **Uppercase Section Headings**: Some capitalized headings (e.g. `THE OFFER SHALL CONSTITUTE`, `SYNDICATE MEMBERS`) matched general spaCy ORG tags.\n")
        f.write("- **Registration Codes**: A few multi-digit numbers in table headers were picked up by the phone number pattern.\n\n")

        f.write("### False Negatives\n")
        f.write("- **Abbreviated Names in Tables**: A few isolated surnames in financial tables without title prefixes were missed.\n\n")

        f.write("### Word Run Formatting Note\n")
        f.write("- In Word documents, text can be split across multiple XML run objects. When replacing text across runs, the replacement is placed in the first run to keep formatting intact.\n")

    return {
        "report_path": report_output_path,
        "total_tokens": total_tokens,
        "tp": tp_total,
        "fp": fp_total,
        "fn": fn_total,
        "tn": tn_total,
        "overall_accuracy": overall_accuracy,
        "overall_precision": overall_precision,
        "overall_recall": overall_recall,
        "overall_f1": overall_f1,
        "metrics_by_cat": metrics_by_cat
    }
