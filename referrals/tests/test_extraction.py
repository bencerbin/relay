from django.test import SimpleTestCase

from referrals.services.extraction import extract_fields


class ExtractFieldsTests(SimpleTestCase):
    """Test the temporary deterministic extractor used by the intake flow."""

    def test_extracts_food_delivery_and_county(self):
        result = extract_fields(
            "I need meals delivered in Fairfield County."
        )

        self.assertEqual(result["needs"], ["food_delivery"])
        self.assertEqual(result["county"], "Fairfield")
        self.assertEqual(result["service_modalities"], ["delivery"])

    def test_extracts_healthcare_specialty_and_adds_healthcare_need(self):
        result = extract_fields(
            "I need oncology care in New Haven County."
        )

        self.assertEqual(result["needs"], ["healthcare"])
        self.assertEqual(result["healthcare_specialties"], ["oncology"])
        self.assertEqual(result["county"], "New Haven")

    def test_extracts_scalar_fields(self):
        result = extract_fields(
            "I am age 72, speak Spanish, have Medicaid, and use a wheelchair."
        )

        self.assertEqual(result["age"], 72)
        self.assertEqual(result["preferred_language"], "spanish")
        self.assertEqual(result["insurance_type"], "Medicaid")
        self.assertTrue(result["wheelchair"])

    def test_extracts_negative_wheelchair_answer(self):
        result = extract_fields("I do not need a wheelchair.")

        self.assertFalse(result["wheelchair"])

    def test_extracts_modalities_and_program_purpose(self):
        result = extract_fields(
            "I need urgent telehealth care in person if possible."
        )

        self.assertEqual(result["service_modalities"], ["telehealth"])
        self.assertEqual(result["program_purposes"], ["emergency"])

    def test_normalizes_case_and_primary_care_name(self):
        result = extract_fields("PRIMARY CARE in FAIRFIELD COUNTY")

        self.assertEqual(result["needs"], ["healthcare"])
        self.assertEqual(result["healthcare_specialties"], ["primary_care"])
        self.assertEqual(result["county"], "Fairfield")

    def test_returns_empty_dict_when_no_supported_fields_are_found(self):
        self.assertEqual(extract_fields("Hello, I have a question."), {})

    def test_rejects_non_string_messages(self):
        for invalid_message in (None, 123, ["I need help"]):
            with self.subTest(invalid_message=invalid_message):
                with self.assertRaises(TypeError):
                    extract_fields(invalid_message)
