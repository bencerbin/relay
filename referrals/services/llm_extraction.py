import json
import os
from collections.abc import Mapping, Sequence
from typing import Any

from groq import Groq


class GroqExtractionError(RuntimeError):
    """Raised when Groq cannot return a usable intake extraction."""


EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "age": {
            "anyOf": [
                {"type": "integer", "minimum": 0},
                {"type": "null"},
            ]
        },
        "county": {
            "anyOf": [{"type": "string"}, {"type": "null"}]
        },
        "city": {
            "anyOf": [{"type": "string"}, {"type": "null"}]
        },
        "preferred_language": {
            "anyOf": [{"type": "string"}, {"type": "null"}]
        },
        "insurance_type": {
            "anyOf": [{"type": "string"}, {"type": "null"}]
        },
        "wheelchair": {
            "anyOf": [{"type": "boolean"}, {"type": "null"}]
        },
        "needs": {
            "type": "array",
            "items": {
                "type": "string",
                "enum": [
                    "food",
                    "food_delivery",
                    "healthcare",
                    "housing",
                    "transportation",
                    "education",
                    "physical_activity",
                    "mental_health",
                    "childcare",
                    "parenting",
                    "community_resources",
                    "employment",
                ],
            },
        },
        "healthcare_specialties": {
            "type": "array",
            "items": {"type": "string"},
        },
        "population_context": {
            "type": "array",
            "items": {"type": "string"},
        },
        "service_modalities": {
            "type": "array",
            "items": {"type": "string"},
        },
        "program_purposes": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
    "required": [
        "age",
        "county",
        "city",
        "preferred_language",
        "insurance_type",
        "wheelchair",
        "needs",
        "healthcare_specialties",
        "population_context",
        "service_modalities",
        "program_purposes",
    ],
    "additionalProperties": False,
}

SYSTEM_INSTRUCTIONS = """
You extract referral information from one user's message.

Return only the fields in the supplied JSON schema.
Extract only information the user stated or clearly answered. Do not guess.
Use canonical need values: food, food_delivery, healthcare, housing,
transportation, education, physical_activity, mental_health, childcare,
parenting, community_resources, and employment. Use lowercase canonical values
for list fields and languages.
If a value is not present, return null for scalar fields or an empty list for
list fields.

For healthcare specialties, map clear everyday descriptions to canonical
specialties when the mapping is unambiguous. For example:

- suspicious mole, skin lesion, rash, or acne → dermatology
- cancer treatment or cancer follow-up → oncology
- care specifically for older adults → geriatrics

Do not infer a specialty when the description is too vague.

The current draft and missing fields are context. They help interpret short
follow-up answers such as a city name answering a pending city question.
""".strip()


def extract_fields_with_groq(
    message: str,
    *,
    current_draft: Mapping[str, Any] | None = None,
    missing_fields: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Extract canonical referral fields with Groq structured output."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise GroqExtractionError("GROQ_API_KEY is not configured.")

    request_context = {
        "message": message,
        "current_draft": dict(current_draft or {}),
        "missing_fields": list(missing_fields or []),
    }

    client = Groq(api_key=api_key)

    try:
        response = client.chat.completions.create(
            model=os.getenv("GROQ_MODEL", "openai/gpt-oss-20b"),
            messages=[
                {"role": "system", "content": SYSTEM_INSTRUCTIONS},
                {
                    "role": "user",
                    "content": json.dumps(request_context),
                },
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "referral_fields",
                    "strict": True,
                    "schema": EXTRACTION_SCHEMA,
                },
            },
            reasoning_effort=os.getenv("GROQ_REASONING_EFFORT", "low"),
        )
    except Exception as exc:
        raise GroqExtractionError(
            "The Groq extraction request failed."
        ) from exc

    content = response.choices[0].message.content
    if not content:
        raise GroqExtractionError(
            "Groq returned no structured extraction content."
        )

    try:
        extracted_data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise GroqExtractionError(
            "Groq returned invalid extraction JSON."
        ) from exc

    if not isinstance(extracted_data, dict):
        raise GroqExtractionError(
            "Groq extraction output must be a JSON object."
        )

    return extracted_data
