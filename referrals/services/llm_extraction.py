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
        "subneeds": {
            "type": "array",
            "items": {
                "type": "string",
                "enum": [
                    "sports_league",
                    "physical_fitness",
                    "swimming_lessons",
                    "after_school",
                    "summer_camp",
                    "preschool",
                    "childcare",
                    "youth_enrichment",
                    "food_pantry",
                    "mobile_pantry",
                    "food_assistance",
                    "snap_benefits",
                    "nutrition_education",
                    "healthy_eating",
                    "school_meals",
                    "groceries",
                    "pediatric_healthcare",
                    "primary_care",
                    "behavioral_health",
                    "mental_health_counseling",
                    "dental_care",
                    "care_coordination",
                    "special_healthcare_needs",
                    "parenting_education",
                    "community_resource_navigation",
                    "education_support",
                    "affordable_housing",
                    "housing_assistance",
                    "transportation_assistance",
                    "career_support",
                    "scholarships",
                    "mentoring",
                    "healthcare_referrals",
                    "breastfeeding_support",
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
        "clarification": {
            "anyOf": [
                {
                    "type": "object",
                    "properties": {
                        "kind": {"type": "string"},
                        "question": {"type": "string"},
                    },
                    "required": ["kind", "question"],
                    "additionalProperties": False,
                },
                {"type": "null"},
            ]
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
        "subneeds",
        "healthcare_specialties",
        "population_context",
        "service_modalities",
        "program_purposes",
        "clarification",
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
Use canonical subneed values to capture the specific service being requested.
For example, sports league, youth sports, or signing a child up for a team
sport → sports_league; after-school care → after_school; swimming or swim
lessons → swimming_lessons; workout plan, exercise routine, or fitness plan
→ physical_fitness; food pantry or food bank → food_pantry; SNAP or
EBT → snap_benefits; groceries or grocery help → groceries and
food_assistance; summer camp → summer_camp; parenting classes →
parenting_education; pediatrician or dental care → pediatric_healthcare or
dental_care. When a subneed clearly implies a broad need, include both. For
example, SNAP includes food and snap_benefits, and a pediatrician includes
healthcare and pediatric_healthcare.
Only return subneeds that are stated or clearly implied by the user's message.
If a child is having a rough time, struggling, or the parent wants the child
to talk to somebody, interpret that as a mental_health need and use
mental_health_counseling when the message asks for someone to talk to.
For the current deployment, all listed resources serve Fairfield County. If
the missing county field is answered with a confirmation such as "yes" to the
Fairfield County question, set county to Fairfield.
If a value is not present, return null for scalar fields or an empty list for
list fields.

If the message strongly implies a type of assistance without stating it
clearly, return a concise clarification object with a specific question, and
do not guess a need. For example, if someone describes being unable to afford
food without explicitly asking for food assistance, return a question such as
"Do you mean you want food-based assistance?". Return null when the user's
need is clear. Never use a generic question such as "What kind of help are you
looking for?" when a more specific confirmation is possible.

For healthcare specialties, map clear everyday descriptions to canonical
specialties when the mapping is unambiguous. For example:

- suspicious mole, skin lesion, rash, or acne → dermatology
- cancer treatment or cancer follow-up → oncology
- sprain, fracture, broken bone, concussion, or sports injury → orthopedics
- care specifically for older adults → geriatrics
- pediatrician or pediatric care → pediatrics
- dental care, dentist, or dentistry → dentistry
- general medicine or primary care → primary_care

When the missing field is healthcare_specialties, interpret concise answers
such as "general", "pediatrics", or "dental" using those mappings rather
than asking the same specialty question again.

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
