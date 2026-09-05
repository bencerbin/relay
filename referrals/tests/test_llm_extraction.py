import json
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from referrals.services.llm_extraction import (
    GroqExtractionError,
    extract_fields_with_groq,
)


class GroqExtractionTests(SimpleTestCase):
    """Test the Groq adapter without making network requests."""

    def test_sends_context_and_returns_structured_fields(self):
        extracted_fields = {
            "age": None,
            "county": "Fairfield",
            "city": None,
            "preferred_language": None,
            "insurance_type": None,
            "wheelchair": None,
            "needs": ["food_delivery"],
            "healthcare_specialties": [],
            "population_context": [],
            "service_modalities": ["delivery"],
            "program_purposes": [],
        }
        fake_response = SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        content=json.dumps(extracted_fields),
                    )
                )
            ]
        )

        with (
            patch.dict(
                "os.environ",
                {
                    "GROQ_API_KEY": "test-key",
                    "GROQ_MODEL": "openai/gpt-oss-20b",
                    "GROQ_REASONING_EFFORT": "low",
                },
                clear=False,
            ),
            patch("referrals.services.llm_extraction.Groq") as groq_class,
        ):
            groq_class.return_value.chat.completions.create.return_value = (
                fake_response
            )

            result = extract_fields_with_groq(
                "Stamford.",
                current_draft={"needs": ["food_delivery"]},
                missing_fields=["city"],
            )

        self.assertEqual(result, extracted_fields)
        groq_class.assert_called_once_with(api_key="test-key")

        call_kwargs = (
            groq_class.return_value.chat.completions.create.call_args.kwargs
        )
        self.assertEqual(call_kwargs["model"], "openai/gpt-oss-20b")
        self.assertEqual(call_kwargs["reasoning_effort"], "low")
        user_message = call_kwargs["messages"][1]["content"]
        self.assertEqual(json.loads(user_message)["missing_fields"], ["city"])

    def test_missing_api_key_fails_before_calling_groq(self):
        with patch.dict("os.environ", {"GROQ_API_KEY": ""}, clear=False):
            with self.assertRaises(GroqExtractionError):
                extract_fields_with_groq("I need meals delivered.")

