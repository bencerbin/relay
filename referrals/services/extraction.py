import re
from collections.abc import Mapping, Sequence
from typing import Any

from django.conf import settings


NEED_PHRASES = {
    "food_delivery": (
        "food delivery",
        "meal delivery",
        "meals delivered",
        "food delivered",
    ),
    "food": (
        "food pantry",
        "food assistance",
        "groceries",
    ),
    "healthcare": (
        "healthcare",
        "health care",
        "medical care",
        "doctor",
    ),
    "housing": (
        "housing",
        "shelter",
        "rent assistance",
    ),
    "transportation": (
        "transportation",
        "a ride",
        "rides",
    ),
}

SPECIALTY_NAMES = (
    "oncology",
    "dermatology",
    "geriatrics",
    "primary_care",
)


def extract_fields_deterministic(message: str) -> dict[str, Any]:
    """Extract referral fields with the temporary keyword-based fallback.

    This is useful for local development and tests when the LLM backend is
    unavailable.
    """
    if not isinstance(message, str):
        raise TypeError("message must be a string.")

    text = message.strip().lower()
    extracted: dict[str, Any] = {}

    needs = [
        need
        for need, phrases in NEED_PHRASES.items()
        if any(phrase in text for phrase in phrases)
    ]
    if needs:
        extracted["needs"] = needs

    specialties = [
        specialty
        for specialty in SPECIALTY_NAMES
        if specialty.replace("_", " ") in text
    ]
    if specialties:
        extracted["healthcare_specialties"] = specialties
        if "needs" not in extracted:
            extracted["needs"] = ["healthcare"]

    county_match = re.search(
        r"\b(?:in|from|located in)\s+([a-z][a-z .'-]*?)\s+county\b",
        text,
    )
    if county_match is None:
        county_match = re.search(
            r"^([a-z][a-z .'-]*?)\s+county\b",
            text,
        )
    if county_match:
        extracted["county"] = county_match.group(1).strip().title()

    age_match = re.search(
        r"\b(?:age[d]?|years? old)\D{0,10}(\d{1,3})\b",
        text,
    )
    if age_match:
        extracted["age"] = int(age_match.group(1))

    for language in ("english", "spanish"):
        if language in text:
            extracted["preferred_language"] = language
            break

    for insurance_type in ("medicaid", "medicare"):
        if insurance_type in text:
            extracted["insurance_type"] = insurance_type.title()
            break

    if "wheelchair" in text:
        extracted["wheelchair"] = not any(
            phrase in text
            for phrase in (
                "do not need a wheelchair",
                "don't need a wheelchair",
                "no wheelchair",
            )
        )

    if "telehealth" in text or "telemedicine" in text:
        extracted["service_modalities"] = ["telehealth"]
    elif "in person" in text or "in-person" in text:
        extracted["service_modalities"] = ["in_person"]
    elif "delivered" in text or "delivery" in text:
        extracted["service_modalities"] = ["delivery"]

    if "emergency" in text or "urgent" in text:
        extracted["program_purposes"] = ["emergency"]
    elif "ongoing" in text or "regular" in text:
        extracted["program_purposes"] = ["ongoing_support"]

    return extracted


def extract_fields(
    message: str,
    *,
    current_draft: Mapping[str, Any] | None = None,
    missing_fields: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Route extraction to the configured backend while keeping one interface."""
    backend = getattr(settings, "EXTRACTION_BACKEND", "deterministic").lower()

    if backend == "groq":
        from .llm_extraction import extract_fields_with_groq

        return extract_fields_with_groq(
            message,
            current_draft=current_draft,
            missing_fields=missing_fields,
        )

    if backend != "deterministic":
        raise ValueError(f"Unknown extraction backend: {backend}")

    return extract_fields_deterministic(message)
