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
Use canonical need values: food, food_delivery, healthcare, housing, and
transportation. Use lowercase canonical values for list fields and languages.
If a value is not present, return null for scalar fields or an empty list for
list fields.

The current draft and missing fields are context. They help interpret short
follow-up answers such as a city name answering a pending city question.
""".strip()

def extract_fields_with_groq(
    message: str,
    current_draft: Mapping[str, Any] | None = none,
    missing_fields: Sequence[str],
) -> dict[str, Any]:
    
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
            model = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b"),
            messages = [
                {"role": "system", "content": SYSTEM_INSTRUCTIONS}
                {
                    "role" : "user"
                    "content" : json.dumps(request_context)
                },
            ],
            response_format = {
                "type" : "json_schema",
                "json_schema": {
                    "name": "referral_fields",
                    "strict": True,
                    "schema": EXTRACTION_SCHEMA,
                }
            }
        )
