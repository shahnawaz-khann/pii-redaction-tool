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


class PIIRedactor:
    """Manages consistent fake replacement generation and DOCX document redaction."""

    def __init__(self, seed: int = 42):
        self.fake = Faker('en_IN')
        Faker.seed(seed)
        self.replacement_map: Dict[str, str] = {}
        self.canonical_person_map: Dict[str, str] = {}
        self.canonical_org_map: Dict[str, str] = {}
        self.canonical_phone_map: Dict[str, str] = {}
        self.canonical_address_map: Dict[str, str] = {}

    def get_replacement(self, original_text: str, entity_type: str) -> str:
        """
        Get or create consistent fake replacement for an entity.
        Normalizes keys by lowercase/strip so casing variations share the same identity.
        """
        if original_text in self.replacement_map:
            return self.replacement_map[original_text]

        norm_key = original_text.strip().lower()
        replacement = ""

        if entity_type == "PERSON":
            if norm_key not in self.canonical_person_map:
                self.canonical_person_map[norm_key] = self.fake.name()
            fake_base = self.canonical_person_map[norm_key]
            replacement = fake_base.upper() if original_text.isupper() else fake_base

        elif entity_type == "EMAIL":
            # Attempt consistent name-email mapping
            parts = original_text.split('@')
            username = parts[0]
            matched_fake_username = None

            for person_norm_key, fake_name in self.canonical_person_map.items():
                first_name = person_norm_key.split()[0]
                if first_name and first_name in username.lower():
                    clean_fake = re.sub(r'[^a-zA-Z]', '', fake_name.lower())
                    matched_fake_username = clean_fake
                    break

            if matched_fake_username:
                replacement = f"{matched_fake_username}@example.com"
            else:
                fake_user = re.sub(r'[^a-zA-Z0-9]', '', self.fake.user_name().lower())
                replacement = f"{fake_user}@example.com"

        elif entity_type == "PHONE":
            # Distinct fake phone number per unique original phone
            if norm_key not in self.canonical_phone_map:
                # Generate unique Indian format mobile/landline
                random_digits = self.fake.msisdn()[-8:]
                self.canonical_phone_map[norm_key] = f"+91 98{random_digits}"
            replacement = self.canonical_phone_map[norm_key]

        elif entity_type == "ORGANIZATION":
            if norm_key not in self.canonical_org_map:
                self.canonical_org_map[norm_key] = f"{self.fake.company()} Private Limited"
            fake_org = self.canonical_org_map[norm_key]
            replacement = fake_org.upper() if original_text.isupper() else fake_org

        elif entity_type == "ADDRESS":
            if norm_key not in self.canonical_address_map:
                self.canonical_address_map[norm_key] = (
                    f"{self.fake.building_number()}, Sample Commercial Complex, MG Road, "
                    f"Pune – 411 001, Maharashtra, India"
                )
            replacement = self.canonical_address_map[norm_key]

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
        Note: When an entity spans multiple formatting runs, text is consolidated
        into the initial run to preserve layout, with a minor tradeoff on intra-entity run styles.
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

        # Fast path: check if single run contains text
        for orig, fake_val in present_items:
            for run in paragraph.runs:
                if orig in run.text:
                    run.text = run.text.replace(orig, fake_val)
                    replacements_made += 1

        # Handle text split across runs
        updated_text = paragraph.text
        for orig, fake_val in present_items:
            if orig in updated_text and paragraph.runs:
                # Merge consolidated text in first run and clear remaining runs
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
