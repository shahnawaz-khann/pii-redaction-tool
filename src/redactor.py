"""
redactor.py
Redaction Engine using python-docx and Faker.
Generates consistent fake replacements and applies them across paragraphs, tables, headers, and footers.
"""

import os
import re
from faker import Faker
import docx
from typing import Dict, List, Any

# Initialize deterministic Faker
fake = Faker('en_IN')
Faker.seed(42)


class PIIRedactor:
    """Manages consistent fake replacement generation and DOCX document redaction."""

    def __init__(self, seed: int = 42):
        self.fake = Faker('en_IN')
        Faker.seed(seed)
        self.replacement_map: Dict[str, str] = {}
        self.person_name_map: Dict[str, str] = {}

    def get_replacement(self, original_text: str, entity_type: str) -> str:
        """Get or create consistent fake replacement for original entity."""
        if original_text in self.replacement_map:
            return self.replacement_map[original_text]

        replacement = ""

        if entity_type == "PERSON":
            fake_name = self.fake.name()
            # Retain uppercase if original was uppercase
            if original_text.isupper():
                replacement = fake_name.upper()
            else:
                replacement = fake_name
            self.person_name_map[original_text.lower()] = replacement

        elif entity_type == "EMAIL":
            # Attempt consistent name-email mapping
            parts = original_text.split('@')
            username = parts[0]
            domain = parts[1] if len(parts) > 1 else "example.com"

            matched_fake_username = None
            for orig_name_lower, fake_name in self.person_name_map.items():
                first_name = orig_name_lower.split()[0]
                if first_name in username.lower():
                    clean_fake = re.sub(r'[^a-zA-Z]', '', fake_name.lower())
                    matched_fake_username = clean_fake
                    break

            if matched_fake_username:
                replacement = f"{matched_fake_username}@example.com"
            else:
                fake_user = self.fake.user_name()
                replacement = f"{fake_user}@example.com"

        elif entity_type == "PHONE":
            replacement = "+91 98765 43210"

        elif entity_type == "ADDRESS":
            replacement = "123, Sample Commercial Complex, MG Road, Pune – 411 001, Maharashtra, India"

        elif entity_type == "ORGANIZATION":
            fake_corp = f"{self.fake.company()} Private Limited"
            if original_text.isupper():
                replacement = fake_corp.upper()
            else:
                replacement = fake_corp

        elif entity_type == "SSN":
            replacement = "000-00-0000"

        elif entity_type == "CREDIT_CARD":
            replacement = "4111 1111 1111 1111"

        elif entity_type == "IP_ADDRESS":
            replacement = "10.0.0.1"

        elif entity_type == "DOB":
            replacement = "01/01/1990"

        else:
            replacement = f"[REDACTED_{entity_type}]"

        self.replacement_map[original_text] = replacement
        return replacement

    def build_replacement_map(self, detections: List[Dict[str, Any]]) -> Dict[str, str]:
        """Build replacement map for all detected entities."""
        # Sort by length descending so longer strings get replaced first
        sorted_dets = sorted(detections, key=lambda d: len(d['text']), reverse=True)
        for det in sorted_dets:
            self.get_replacement(det['text'], det['type'])
        return self.replacement_map

    def replace_text_in_paragraph(self, paragraph: Any) -> int:
        """
        Replace mapped PII in a paragraph while preserving DOCX formatting runs.
        Handles both intra-run and cross-run text occurrences.
        """
        if not paragraph.text or not self.replacement_map:
            return 0

        replacements_made = 0
        full_text = paragraph.text

        # Find which mapped items exist in full paragraph text
        present_items = []
        for orig, fake_val in sorted(self.replacement_map.items(), key=lambda item: len(item[0]), reverse=True):
            if orig in full_text:
                present_items.append((orig, fake_val))

        if not present_items:
            return 0

        # Simple & safe approach: check if single run contains text
        for orig, fake_val in present_items:
            for run in paragraph.runs:
                if orig in run.text:
                    run.text = run.text.replace(orig, fake_val)
                    replacements_made += 1

        # Check if text was split across runs and not fully replaced
        updated_text = paragraph.text
        for orig, fake_val in present_items:
            if orig in updated_text:
                # Rebuild paragraph text in first run, clear subsequent runs
                paragraph.runs[0].text = updated_text.replace(orig, fake_val)
                for run in paragraph.runs[1:]:
                    run.text = ""
                replacements_made += 1
                break

        return replacements_made

    def redact_document(self, input_path: str, output_path: str, detections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Redact input DOCX file and save to output_path.
        Returns execution statistics.
        """
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")

        # Build replacement mapping
        self.build_replacement_map(detections)

        doc = docx.Document(input_path)
        total_replacements = 0

        # 1. Process main paragraphs
        for p in doc.paragraphs:
            total_replacements += self.replace_text_in_paragraph(p)

        # 2. Process tables
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for p in cell.paragraphs:
                        total_replacements += self.replace_text_in_paragraph(p)

        # 3. Process headers and footers
        for section in doc.sections:
            if section.header:
                for p in section.header.paragraphs:
                    total_replacements += self.replace_text_in_paragraph(p)
            if section.footer:
                for p in section.footer.paragraphs:
                    total_replacements += self.replace_text_in_paragraph(p)

        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        doc.save(output_path)

        return {
            "output_path": output_path,
            "unique_entities_mapped": len(self.replacement_map),
            "total_replacements_applied": total_replacements
        }
