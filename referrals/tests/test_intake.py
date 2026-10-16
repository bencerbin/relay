from unittest.mock import patch

from django.test import SimpleTestCase, TestCase, override_settings

from referrals.models import ReferralRequest, ReferralSession
from referrals.services.intake import (
    finalize_session,
    get_contextual_required_fields,
    get_missing_required_fields,
    get_required_fields,
    merge_extracted_data,
    process_intake_message,
)


class IntakeHelperTests(SimpleTestCase):
    """Test draft merging and contextual requirement calculations."""

    def test_merge_combines_list_fields_without_duplicates(self):
        draft = {
            "needs": ["food"],
            "wheelchair": False,
        }
        extracted_data = {
            "needs": ["food", "food_delivery"],
            "wheelchair": True,
        }

        merged = merge_extracted_data(draft, extracted_data)

        self.assertEqual(merged["needs"], ["food", "food_delivery"])
        self.assertTrue(merged["wheelchair"])
        self.assertEqual(draft, {"needs": ["food"], "wheelchair": False})

    def test_merge_normalizes_list_values(self):
        merged = merge_extracted_data(
            {"needs": [" Food "]},
            {"needs": "FOOD_DELIVERY"},
        )

        self.assertEqual(merged["needs"], ["food", "food_delivery"])

    def test_merge_ignores_empty_and_none_values(self):
        draft = {
            "county": "Fairfield",
            "city": "Stamford",
        }

        merged = merge_extracted_data(
            draft,
            {"county": "", "city": None},
        )

        self.assertEqual(merged, draft)

    def test_merge_rejects_unknown_fields(self):
        with self.assertRaises(ValueError):
            merge_extracted_data({}, {"unknown_field": "value"})

    def test_merge_rejects_non_string_list_items(self):
        with self.assertRaises(TypeError):
            merge_extracted_data({}, {"needs": ["food", 123]})

    def test_contextual_requirements_depend_on_needs(self):
        self.assertEqual(
            get_contextual_required_fields(
                {"needs": ["healthcare", "food_delivery"]}
            ),
            ["city", "healthcare_specialties"],
        )

    def test_required_fields_include_static_and_contextual_requirements(self):
        self.assertEqual(
            get_required_fields({"needs": ["healthcare"]}),
            ["needs", "healthcare_specialties", "county"],
        )

    def test_missing_fields_are_recalculated_from_the_current_draft(self):
        self.assertEqual(
            get_missing_required_fields({"needs": ["food_delivery"]}),
            ["city", "county"],
        )
        self.assertEqual(
            get_missing_required_fields(
                {
                    "needs": ["food_delivery"],
                    "county": "Fairfield",
                    "city": "Stamford",
                }
            ),
            [],
        )


class IntakeSessionTests(TestCase):
    """Test the database-backed intake session workflow."""

    def test_process_message_saves_an_incomplete_draft(self):
        session = ReferralSession.objects.create()

        result = process_intake_message(session, "I need meals delivered")

        session.refresh_from_db()
        self.assertEqual(session.status, ReferralSession.Status.COLLECTING)
        self.assertEqual(session.draft["needs"], ["food_delivery"])
        self.assertEqual(set(result["missing_fields"]), {"city", "county"})
        self.assertEqual(result["question"], "What city are you located in?")

    def test_unknown_need_uses_category_disambiguation_question(self):
        session = ReferralSession.objects.create()

        result = process_intake_message(
            session,
            "I need something that can help me feel more prepared.",
        )

        self.assertEqual(
            result["question"],
            "I can’t quite find a resource category for that yet. Do you "
            "mean you need help with food and nutrition, physical activity, "
            "emotional well-being, or healthcare?",
        )

    @override_settings(EXTRACTION_BACKEND="groq")
    @patch("referrals.services.intake.extract_fields")
    def test_llm_follow_up_question_is_used_when_ready(self, extract_fields):
        extract_fields.return_value = {
            "needs": ["mental_health"],
            "county": "Fairfield",
            "follow_up_question": (
                "Would counseling or school-based emotional support be more "
                "helpful?"
            ),
        }
        session = ReferralSession.objects.create()

        result = process_intake_message(
            session,
            "My son is having a hard time in school.",
        )

        self.assertEqual(result["status"], ReferralSession.Status.READY)
        self.assertEqual(
            result["question"],
            "Would counseling or school-based emotional support be more "
            "helpful?",
        )

    def test_process_message_returns_county_follow_up_question(self):
        session = ReferralSession.objects.create(
            draft={
                "needs": ["food_delivery"],
                "city": "Stamford",
            }
        )

        result = process_intake_message(
            session,
            "I still need help with meals delivered.",
        )

        self.assertEqual(result["missing_fields"], ["county"])
        self.assertEqual(
            result["question"],
            "Are you located in Fairfield County?",
        )

    def test_ambiguous_food_hardship_gets_confirmation_before_location(self):
        session = ReferralSession.objects.create()

        first_result = process_intake_message(
            session,
            "I have some dumplings on the stove but I need more dumplings "
            "yet I'm broke so I can't afford them.",
        )
        second_result = process_intake_message(session, "Yes")

        self.assertEqual(
            first_result["question"],
            "Do you mean you want food-based assistance?",
        )
        self.assertEqual(
            second_result["question"],
            "Are you located in Fairfield County?",
        )
        self.assertEqual(second_result["missing_fields"], ["county"])

        third_result = process_intake_message(session, "Yes")

        self.assertEqual(third_result["status"], ReferralSession.Status.READY)
        self.assertEqual(third_result["draft"]["needs"], ["food"])
        self.assertEqual(
            third_result["draft"]["subneeds"],
            ["food_assistance"],
        )

    def test_clear_food_answer_skips_ambiguous_confirmation(self):
        session = ReferralSession.objects.create()

        result = process_intake_message(
            session,
            "I need food in Fairfield County.",
        )

        self.assertEqual(result["status"], ReferralSession.Status.READY)
        self.assertIsNone(result["question"])
        self.assertEqual(result["draft"]["needs"], ["food"])

    def test_rough_time_language_collects_mental_health_referral(self):
        session = ReferralSession.objects.create()

        first_result = process_intake_message(
            session,
            "My son is having a rough time and I want him to talk to somebody.",
        )
        second_result = process_intake_message(session, "Yes")

        self.assertEqual(first_result["missing_fields"], ["county"])
        self.assertEqual(second_result["status"], ReferralSession.Status.READY)
        self.assertEqual(second_result["draft"]["needs"], ["mental_health"])
        self.assertEqual(
            second_result["draft"]["subneeds"],
            ["mental_health_counseling"],
        )

    def test_process_message_returns_healthcare_specialty_question(self):
        session = ReferralSession.objects.create()

        result = process_intake_message(
            session,
            "I need healthcare in Fairfield County.",
        )

        self.assertEqual(
            result["missing_fields"],
            ["healthcare_specialties"],
        )
        self.assertEqual(
            result["question"],
            "What type of healthcare specialty do you need?",
        )

    def test_sports_injury_infers_healthcare_and_asks_location_last(self):
        session = ReferralSession.objects.create()

        result = process_intake_message(
            session,
            "I suffered a high ankle sprain in a football game.",
        )

        self.assertEqual(result["missing_fields"], ["county"])
        self.assertEqual(
            result["question"],
            "Are you located in Fairfield County?",
        )
        self.assertEqual(result["draft"]["needs"], ["healthcare"])
        self.assertEqual(
            result["draft"]["healthcare_specialties"],
            ["orthopedics"],
        )

    def test_short_healthcare_specialty_answer_is_not_reasked(self):
        session = ReferralSession.objects.create(
            draft={
                "needs": ["healthcare"],
                "county": "Fairfield",
            }
        )

        result = process_intake_message(session, "dental care")

        self.assertEqual(result["status"], ReferralSession.Status.READY)
        self.assertEqual(result["missing_fields"], [])
        self.assertEqual(
            result["draft"]["healthcare_specialties"],
            ["dentistry"],
        )

    def test_process_message_marks_complete_healthcare_intake_ready(self):
        session = ReferralSession.objects.create()

        result = process_intake_message(
            session,
            "I need oncology care in Fairfield County",
        )

        session.refresh_from_db()
        self.assertEqual(session.status, ReferralSession.Status.READY)
        self.assertEqual(result["missing_fields"], [])
        self.assertIsNone(result["question"])
        self.assertEqual(session.draft["healthcare_specialties"], ["oncology"])

    def test_everyday_healthcare_description_accepts_short_county_answer(self):
        session = ReferralSession.objects.create()

        first_result = process_intake_message(
            session,
            "I need help with a suspicious mole",
        )
        second_result = process_intake_message(session, "Fairfield")

        self.assertEqual(first_result["missing_fields"], ["county"])
        self.assertEqual(second_result["status"], ReferralSession.Status.READY)
        self.assertEqual(second_result["missing_fields"], [])
        self.assertEqual(second_result["draft"]["county"], "Fairfield")
        self.assertEqual(
            second_result["draft"]["healthcare_specialties"],
            ["dermatology"],
        )

    def test_multiple_messages_accumulate_information(self):
        session = ReferralSession.objects.create()

        process_intake_message(session, "I need oncology care")
        result = process_intake_message(session, "I am in Fairfield County")

        self.assertEqual(result["status"], ReferralSession.Status.READY)
        self.assertEqual(result["missing_fields"], [])

    def test_abandoned_session_cannot_receive_messages(self):
        session = ReferralSession.objects.create(
            status=ReferralSession.Status.ABANDONED,
        )

        with self.assertRaises(ValueError):
            process_intake_message(session, "I need food assistance")


class SessionFinalizationTests(TestCase):
    """Test conversion from a session draft to a finalized referral."""

    def test_finalize_creates_and_links_a_referral_request(self):
        session = ReferralSession.objects.create(
            status=ReferralSession.Status.READY,
            draft={
                "needs": ["healthcare"],
                "healthcare_specialties": ["oncology"],
                "county": "Fairfield",
            },
        )

        referral = finalize_session(session)

        session.refresh_from_db()
        self.assertIsInstance(referral, ReferralRequest)
        self.assertEqual(session.status, ReferralSession.Status.COMPLETED)
        self.assertEqual(session.referral_request_id, referral.id)
        self.assertEqual(ReferralRequest.objects.count(), 1)

    def test_finalize_is_idempotent(self):
        session = ReferralSession.objects.create(
            draft={
                "needs": ["food"],
                "county": "Fairfield",
            },
        )

        first_referral = finalize_session(session)
        second_referral = finalize_session(session)

        self.assertEqual(first_referral.id, second_referral.id)
        self.assertEqual(ReferralRequest.objects.count(), 1)

    def test_incomplete_contextual_draft_cannot_be_finalized(self):
        session = ReferralSession.objects.create(
            draft={
                "needs": ["healthcare"],
                "county": "Fairfield",
            },
        )

        with self.assertRaises(ValueError):
            finalize_session(session)

        session.refresh_from_db()
        self.assertIsNone(session.referral_request_id)
        self.assertEqual(session.status, ReferralSession.Status.COLLECTING)
        self.assertEqual(ReferralRequest.objects.count(), 0)

    def test_abandoned_session_cannot_be_finalized(self):
        session = ReferralSession.objects.create(
            status=ReferralSession.Status.ABANDONED,
            draft={"needs": ["food"], "county": "Fairfield"},
        )

        with self.assertRaises(ValueError):
            finalize_session(session)

    def test_correct_question(self):
        session = ReferralSession.objects.create()

        result = process_intake_message(
            session,
            "I need meals delivered.",
        )

        self.assertEqual(result["missing_fields"], ["city", "county"])
        self.assertEqual(result["question"], "What city are you located in?")
