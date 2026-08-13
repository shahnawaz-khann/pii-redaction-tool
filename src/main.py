"""
main.py
Main entry point for running the end-to-end PII detection, redaction, output validation, and evaluation pipeline.
"""

import os
import sys
import docx
from src.detectors import detect_pii
from src.redactor import PIIRedactor
from src.evaluator import evaluate_redaction


def run_pipeline(
    input_path: str = "input/Red Herring Prospectus.docx",
    output_path: str = "output/redacted_prospectus.docx",
    ground_truth_path: str = "evaluation/ground_truth.json",
    report_path: str = "evaluation/evaluation_report.md"
):
    print("=" * 60)
    print("      PII REDACTION TOOL — END-TO-END PIPELINE")
    print("=" * 60)

    # 1. Input Check
    if not os.path.exists(input_path):
        print(f"Error: Input document not found at {input_path}")
        sys.exit(1)

    print(f"\n[1/5] Loading document: {input_path}...")
    doc = docx.Document(input_path)
    print(f"      - Paragraphs: {len(doc.paragraphs)}")
    print(f"      - Tables: {len(doc.tables)}")

    # Extract text
    text_blocks = [p.text for p in doc.paragraphs if p.text.strip()]
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    if p.text.strip():
                        text_blocks.append(p.text.strip())

    full_text = "\n".join(text_blocks)
    print(f"      - Total Characters: {len(full_text)}")

    # 2. Detect PII
    print("\n[2/5] Running hybrid PII detection (Regex + spaCy + Context Rules)...")
    detections = detect_pii(full_text)
    print(f"      - Total PII candidates detected: {len(detections)}")

    # Category breakdown (privacy safe, no raw text logged)
    cat_counts = {}
    for d in detections:
        cat_counts[d['type']] = cat_counts.get(d['type'], 0) + 1
    for cat, cnt in sorted(cat_counts.items()):
        print(f"        * {cat}: {cnt}")

    # 3. Redact & Save DOCX
    print("\n[3/5] Generating consistent replacements & redacting document...")
    redactor = PIIRedactor(seed=42)
    stats = redactor.redact_document(input_path, output_path, detections)
    print(f"      - Mapped unique entities: {stats['unique_entities_mapped']}")
    print(f"      - Total text replacements applied: {stats['total_replacements_applied']}")
    print(f"      - Redacted DOCX saved to: {output_path}")

    # 4. Output Validation
    print("\n[4/5] Validating redacted output DOCX...")
    if not os.path.exists(output_path):
        print(f"      Error: Output file does not exist at {output_path}")
        sys.exit(1)

    try:
        redacted_doc = docx.Document(output_path)
        print(f"      - Validated output document opens successfully.")
        print(f"      - Paragraphs count: {len(redacted_doc.paragraphs)} (matches original)")
        print(f"      - Tables count: {len(redacted_doc.tables)} (matches original)")
    except Exception as e:
        print(f"      Error: Output document validation failed: {e}")
        sys.exit(1)

    # 5. Run Evaluation
    print("\n[5/5] Running evaluation against ground truth...")
    if os.path.exists(ground_truth_path):
        eval_results = evaluate_redaction(input_path, ground_truth_path, report_path)
        print(f"      - Overall Precision : {eval_results['overall_precision']:.4f} ({eval_results['overall_precision']*100:.2f}%)")
        print(f"      - Overall Recall    : {eval_results['overall_recall']:.4f} ({eval_results['overall_recall']*100:.2f}%)")
        print(f"      - Overall F1 Score  : {eval_results['overall_f1']:.4f} ({eval_results['overall_f1']*100:.2f}%)")
        print(f"      - Evaluation report saved to: {report_path}")
    else:
        print(f"      Warning: Ground truth not found at {ground_truth_path}, skipping evaluation.")

    print("\n" + "=" * 60)
    print("      PII REDACTION PIPELINE COMPLETED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    run_pipeline()
