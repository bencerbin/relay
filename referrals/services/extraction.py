import re
from collections.abc import Mapping, Sequence
from typing import Any

from django.conf import settings

from .constants import SERVICE_AREA_COUNTY


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
        "nutrition",
        "healthy food",
    ),
    "mental_health": (
        "emotional support",
        "emotional well-being",
        "mental health",
        "behavioral health",
        "counseling",
        "counselor",
        "therapist",
        "grief support",
        "having a rough time",
        "having a hard time",
        "rough time in school",
        "hard time in school",
        "struggling in school",
        "struggling emotionally",
        "talk to someone",
        "talk to somebody",
    ),
    "healthcare": (
        "healthcare",
        "health care",
        "medical care",
        "doctor",
        "pediatrician",
        "dental care",
        "dentist",
        "injury",
        "injured",
        "sprain",
        "fracture",
        "broken bone",
        "sports injury",
        "concussion",
        "medical attention",
        "urgent care",
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
    "education": (
        "education",
        "educational program",
        "school support",
        "tutoring",
        "literacy",
    ),
    "physical_activity": (
        "physical activity",
        "sports program",
        "sports league",
        "workout plan",
        "workout routine",
        "exercise plan",
        "exercise routine",
        "fitness plan",
        "fitness routine",
        "physical fitness",
        "get in shape",
        "fitness",
        "exercise",
    ),
    "childcare": (
        "childcare",
        "child care",
        "daycare",
        "preschool",
        "after-school",
        "after school",
        "summer camp",
    ),
    "parenting": (
        "parenting support",
        "parent education",
        "parenting class",
        "parenting classes",
    ),
    "community_resources": (
        "community resources",
        "community program",
        "local resources",
    ),
    "employment": (
        "employment",
        "job training",
        "career support",
    ),
}

SUBNEED_PHRASES = {
    "sports_league": (
        "sports league",
        "sports team",
        "team sports",
        "youth sports",
        "athletic league",
    ),
    "physical_fitness": (
        "physical fitness",
        "fitness program",
        "fitness class",
        "fitness plan",
        "fitness routine",
        "workout plan",
        "workout routine",
        "exercise plan",
        "exercise class",
        "exercise routine",
    ),
    "swimming_lessons": (
        "swimming lessons",
        "swim lessons",
    ),
    "after_school": (
        "after-school",
        "after school",
    ),
    "summer_camp": (
        "summer camp",
        "day camp",
    ),
    "preschool": (
        "preschool",
        "pre-school",
    ),
    "childcare": (
        "childcare",
        "child care",
        "daycare",
    ),
    "youth_enrichment": (
        "youth enrichment",
        "enrichment program",
    ),
    "food_pantry": (
        "food pantry",
        "food bank",
    ),
    "mobile_pantry": (
        "mobile pantry",
        "mobile food",
    ),
    "food_assistance": (
        "food assistance",
        "food access",
        "food security",
        "groceries",
    ),
    "snap_benefits": (
        "snap",
        "ebt",
    ),
    "nutrition_education": (
        "nutrition education",
        "healthy eating",
        "nutrition counseling",
    ),
    "healthy_eating": (
        "healthy eating",
        "healthy meals",
    ),
    "school_meals": (
        "school meals",
        "school lunch",
    ),
    "groceries": (
        "groceries",
        "grocery help",
    ),
    "pediatric_healthcare": (
        "pediatric care",
        "pediatrician",
        "child healthcare",
        "healthcare for my child",
    ),
    "primary_care": (
        "primary care",
        "primary healthcare",
    ),
    "behavioral_health": (
        "behavioral health",
        "behavioral healthcare",
    ),
    "mental_health_counseling": (
        "mental health counseling",
        "therapy",
        "counseling",
        "counselor",
        "therapist",
        "talk to someone",
        "talk to somebody",
        "someone to talk to",
        "somebody to talk to",
    ),
    "dental_care": (
        "dental care",
        "dentist",
    ),
    "care_coordination": (
        "care coordination",
        "care coordinator",
    ),
    "special_healthcare_needs": (
        "special healthcare needs",
        "special health care needs",
    ),
    "parenting_education": (
        "parenting education",
        "parenting class",
        "parent education",
    ),
    "community_resource_navigation": (
        "resource navigation",
        "help finding resources",
        "community resource guide",
    ),
    "education_support": (
        "education support",
        "academic support",
        "school support",
    ),
    "affordable_housing": (
        "affordable housing",
        "public housing",
    ),
    "housing_assistance": (
        "housing assistance",
        "rent assistance",
    ),
    "transportation_assistance": (
        "transportation assistance",
        "bus pass",
        "ride assistance",
    ),
    "career_support": (
        "career support",
        "career assistance",
        "job training",
    ),
    "scholarships": (
        "scholarship",
        "scholarships",
    ),
    "mentoring": (
        "mentoring",
        "mentorship",
    ),
    "healthcare_referrals": (
        "healthcare referrals",
        "health referral",
    ),
    "breastfeeding_support": (
        "breastfeeding support",
        "breastfeeding help",
    ),
}

SUBNEED_TO_NEEDS = {
    "sports_league": ("physical_activity",),
    "physical_fitness": ("physical_activity",),
    "swimming_lessons": ("physical_activity",),
    "after_school": ("childcare",),
    "summer_camp": ("childcare",),
    "preschool": ("childcare",),
    "childcare": ("childcare",),
    "youth_enrichment": ("education",),
    "food_pantry": ("food",),
    "mobile_pantry": ("food",),
    "food_assistance": ("food",),
    "snap_benefits": ("food",),
    "nutrition_education": ("food",),
    "healthy_eating": ("food",),
    "school_meals": ("food",),
    "groceries": ("food",),
    "pediatric_healthcare": ("healthcare",),
    "primary_care": ("healthcare",),
    "behavioral_health": ("mental_health",),
    "mental_health_counseling": ("mental_health",),
    "dental_care": ("healthcare",),
    "care_coordination": ("healthcare",),
    "special_healthcare_needs": ("healthcare",),
    "parenting_education": ("parenting",),
    "community_resource_navigation": ("community_resources",),
    "education_support": ("education",),
    "affordable_housing": ("housing",),
    "housing_assistance": ("housing",),
    "transportation_assistance": ("transportation",),
    "career_support": ("employment",),
}

SPECIALTY_PHRASES = {
    "oncology": (
        "oncology",
        "cancer treatment",
        "cancer follow-up",
    ),
    "dermatology": (
        "dermatology",
        "suspicious mole",
        "skin lesion",
        "skin rash",
        "severe acne",
    ),
    "pediatrics": (
        "pediatrics",
        "pediatrician",
        "pediatric care",
        "child healthcare",
    ),
    "dentistry": (
        "dentistry",
        "dental care",
        "dentist",
    ),
    "geriatrics": (
        "geriatrics",
        "older adult care",
    ),
    "orthopedics": (
        "orthopedic",
        "orthopaedic",
        "sprain",
        "fracture",
        "broken bone",
        "sports injury",
        "concussion",
    ),
    "primary_care": (
        "primary care",
    ),
}

CONTEXTUAL_SPECIALTY_ANSWERS = {
    "general": "primary_care",
    "general care": "primary_care",
    "general medicine": "primary_care",
    "primary care": "primary_care",
    "pediatric": "pediatrics",
    "pediatrics": "pediatrics",
    "pediatrician": "pediatrics",
    "dental": "dentistry",
    "dental care": "dentistry",
    "dentist": "dentistry",
    "dentistry": "dentistry",
}

SHORT_LOCATION_RE = re.compile(r"^[a-z][a-z .'-]{1,79}$")
LOCATION_ANSWER_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "and",
        "care",
        "delivered",
        "delivery",
        "food",
        "for",
        "help",
        "healthcare",
        "i",
        "need",
        "program",
        "service",
        "services",
        "support",
        "the",
        "want",
        "with",
    }
)
AFFIRMATIVE_LOCATION_ANSWERS = frozenset(
    {"yes", "y", "yeah", "yep", "correct", "that's right", "i am"}
)
AFFIRMATIVE_CLARIFICATION_ANSWERS = frozenset(
    {"yes", "y", "yeah", "yep", "correct", "that's right", "exactly"}
)
NEGATIVE_CLARIFICATION_ANSWERS = frozenset(
    {"no", "n", "nope", "not really", "that's not what i mean"}
)

AMBIGUOUS_FOOD_CONTEXT_PHRASES = (
    "dumpling",
    "meal",
    "meals",
    "hungry",
    "eating",
    "dinner",
    "lunch",
    "breakfast",
    "cooking",
    "on the stove",
)
FINANCIAL_HARDSHIP_PHRASES = (
    "can't afford",
    "cannot afford",
    "broke",
    "no money",
    "short on money",
    "short on cash",
    "struggling financially",
    "need help paying",
)


def detect_ambiguous_intent(message: str) -> dict[str, str] | None:
    """Return a focused confirmation when a message implies, but does not state, a need."""
    text = message.strip().lower()
    has_food_context = any(
        phrase in text for phrase in AMBIGUOUS_FOOD_CONTEXT_PHRASES
    )
    has_financial_hardship = any(
        phrase in text for phrase in FINANCIAL_HARDSHIP_PHRASES
    )

    if has_food_context and has_financial_hardship:
        return {
            "kind": "food_assistance",
            "question": "Do you mean you want food-based assistance?",
        }

    return None


def resolve_clarification_answer(
    message: str,
    clarification: Mapping[str, Any],
) -> str | None:
    """Classify a concise answer to a pending intent confirmation."""
    text = message.strip().lower()
    if clarification.get("kind") == "food_assistance":
        if text in AFFIRMATIVE_CLARIFICATION_ANSWERS:
            return "yes"
        if text in NEGATIVE_CLARIFICATION_ANSWERS:
            return "no"
    return None


def _looks_like_short_location_answer(text: str) -> bool:
    """Recognize a concise answer to a location follow-up question."""
    words = set(text.split())
    return (
        bool(SHORT_LOCATION_RE.fullmatch(text))
        and len(text.split()) <= 4
        and not words.intersection(LOCATION_ANSWER_STOPWORDS)
    )


def extract_fields_deterministic(
    message: str,
    *,
    current_draft: Mapping[str, Any] | None = None,
    missing_fields: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Extract referral fields with the temporary keyword-based fallback.

    This is useful for local development and tests when the LLM backend is
    unavailable.
    """
    if not isinstance(message, str):
        raise TypeError("message must be a string.")

    text = message.strip().lower()
    extracted: dict[str, Any] = {}
    missing = set(missing_fields or ())

    needs = [
        need
        for need, phrases in NEED_PHRASES.items()
        if any(phrase in text for phrase in phrases)
    ]
    if (
        "food_delivery" not in needs
        and re.search(
            r"\b(?:need|want|looking for|help with|assistance with)"
            r"\b[^.?!]{0,24}\bfood\b",
            text,
        )
    ):
        needs.append("food")
    specialties = [
        specialty
        for specialty, phrases in SPECIALTY_PHRASES.items()
        if any(phrase in text for phrase in phrases)
    ]
    if specialties:
        extracted["healthcare_specialties"] = specialties
        if "healthcare" not in needs:
            needs.append("healthcare")

    if (
        "healthcare_specialties" in missing
        and not specialties
        and text in CONTEXTUAL_SPECIALTY_ANSWERS
    ):
        extracted["healthcare_specialties"] = [
            CONTEXTUAL_SPECIALTY_ANSWERS[text]
        ]

    subneeds = [
        subneed
        for subneed, phrases in SUBNEED_PHRASES.items()
        if any(phrase in text for phrase in phrases)
    ]
    if subneeds:
        extracted["subneeds"] = subneeds
        for subneed in subneeds:
            for need in SUBNEED_TO_NEEDS.get(subneed, ()):
                if need not in needs:
                    needs.append(need)

    if needs:
        extracted["needs"] = needs

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
    elif "county" in missing and (
        text in AFFIRMATIVE_LOCATION_ANSWERS
        or "fairfield" in text
    ):
        extracted["county"] = SERVICE_AREA_COUNTY
    elif "county" in missing and _looks_like_short_location_answer(text):
        extracted["county"] = text.title()

    if (
        "city" in missing
        and "city" not in extracted
        and _looks_like_short_location_answer(text)
    ):
        extracted["city"] = text.title()

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

    return extract_fields_deterministic(
        message,
        current_draft=current_draft,
        missing_fields=missing_fields,
    )
