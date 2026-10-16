from django.test import SimpleTestCase

from referrals.services.extraction import (
    detect_ambiguous_intent,
    extract_fields,
)


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

    def test_extracts_everyday_description_as_dermatology(self):
        result = extract_fields("I need help with a suspicious mole.")

        self.assertEqual(result["needs"], ["healthcare"])
        self.assertEqual(result["healthcare_specialties"], ["dermatology"])

    def test_extracts_sports_injury_as_orthopedic_healthcare(self):
        result = extract_fields(
            "I suffered a high ankle sprain in a football game."
        )

        self.assertEqual(result["needs"], ["healthcare"])
        self.assertEqual(
            result["healthcare_specialties"],
            ["orthopedics"],
        )

    def test_uses_missing_field_context_for_short_location_answer(self):
        result = extract_fields(
            "Fairfield",
            current_draft={"needs": ["healthcare"]},
            missing_fields=["county", "healthcare_specialties"],
        )

        self.assertEqual(result["county"], "Fairfield")

    def test_extracts_child_health_and_wellbeing_language(self):
        result = extract_fields(
            "I need nutrition and emotional well-being support for my child."
        )

        self.assertEqual(result["needs"], ["food", "mental_health"])

    def test_extracts_specific_sports_subneed(self):
        result = extract_fields(
            "I need to sign up my daughter for a sports league."
        )

        self.assertEqual(result["needs"], ["physical_activity"])
        self.assertEqual(result["subneeds"], ["sports_league"])

    def test_infers_workout_plan_as_physical_fitness_support(self):
        result = extract_fields("I need a workout plan.")

        self.assertEqual(result["needs"], ["physical_activity"])
        self.assertEqual(result["subneeds"], ["physical_fitness"])

    def test_infers_mental_health_support_from_everyday_language(self):
        result = extract_fields(
            "My son has been having a rough time in school and needs to talk "
            "to somebody."
        )

        self.assertEqual(result["needs"], ["mental_health"])
        self.assertEqual(
            result["subneeds"],
            ["mental_health_counseling"],
        )

    def test_accepts_affirmative_answer_to_service_area_question(self):
        result = extract_fields(
            "Yes",
            missing_fields=["county"],
        )

        self.assertEqual(result["county"], "Fairfield")

    def test_rolls_snap_request_up_to_food_need(self):
        result = extract_fields("I need help applying for SNAP.")

        self.assertEqual(result["needs"], ["food"])
        self.assertEqual(result["subneeds"], ["snap_benefits"])

    def test_rolls_child_healthcare_subneeds_up_to_healthcare(self):
        result = extract_fields(
            "My child needs a pediatrician and possibly dental care."
        )

        self.assertEqual(result["needs"], ["healthcare"])
        self.assertEqual(
            result["subneeds"],
            ["pediatric_healthcare", "dental_care"],
        )

    def test_rolls_program_and_parenting_subneeds_up_to_broad_needs(self):
        camp_result = extract_fields(
            "I need affordable summer camps or after school programs."
        )
        parenting_result = extract_fields(
            "I am looking for parenting classes."
        )

        self.assertEqual(camp_result["needs"], ["childcare"])
        self.assertEqual(
            camp_result["subneeds"],
            ["after_school", "summer_camp"],
        )
        self.assertEqual(parenting_result["needs"], ["parenting"])
        self.assertEqual(
            parenting_result["subneeds"],
            ["parenting_education"],
        )

    def test_grocery_request_includes_general_food_assistance(self):
        result = extract_fields("I need help getting groceries.")

        self.assertEqual(result["needs"], ["food"])
        self.assertEqual(
            result["subneeds"],
            ["food_assistance", "groceries"],
        )

    def test_extracts_direct_food_request(self):
        result = extract_fields("I need food.")

        self.assertEqual(result["needs"], ["food"])

    def test_flags_implicit_food_hardship_for_confirmation(self):
        result = detect_ambiguous_intent(
            "I have some dumplings on the stove but I need more dumplings "
            "yet I'm broke so I can't afford them."
        )

        self.assertEqual(
            result,
            {
                "kind": "food_assistance",
                "question": "Do you mean you want food-based assistance?",
            },
        )

    def test_extracts_child_healthcare_specialties(self):
        result = extract_fields(
            "My child needs a pediatrician and possibly dental care."
        )

        self.assertEqual(
            result["healthcare_specialties"],
            ["pediatrics", "dentistry"],
        )

    def test_interprets_short_specialty_answers_in_context(self):
        self.assertEqual(
            extract_fields(
                "general",
                missing_fields=["healthcare_specialties"],
            )["healthcare_specialties"],
            ["primary_care"],
        )
        self.assertEqual(
            extract_fields(
                "dental",
                missing_fields=["healthcare_specialties"],
            )["healthcare_specialties"],
            ["dentistry"],
        )

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
