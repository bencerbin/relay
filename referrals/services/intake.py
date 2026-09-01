from collections.abc import Mapping
from typing import Any

from django.db import transaction

from ..models import ReferralRequest, ReferralSession
from ..serializers import ReferralRequestSerializer

from .extraction import extract_fields

Draft = dict[str, Any]

REQUEST_FIELDS = frozenset(
    {
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
    }
)

LIST_FIELDS = frozenset(
    {
        "needs",
        "healthcare_specialties",
        "population_context",
        "service_modalities",
        "program_purposes",
    }
)

STATIC_REQUIRED_FIELDS = frozenset({
    "needs",
    "county",
})

CONTEXT_REQUIRED_FIELDS = {
    "healthcare": frozenset({"healthcare_specialties"}),
    "food_delivery": frozenset({"city"}), #THIS IS SOMETHING THAT MIGHT NEED  TO CHANGE... CAN WE USE ZIP CODE? ADDRESS?
    "housing": frozenset(),
}

FIELD_QUESTIONS = {
    "needs": "What kind of help are you looking for?",
    "county": "What county are you located in?",
    "city": "What city are you located in?",
    "healthcare_specialties": "What type of healthcare specialty do you need?",
}




def _normalize_list(value: Any, field_name: str) -> list[str]:
    """Normalize one extracted list field before it enters the session draft."""
    if isinstance(value, str):
        values = [value]
    elif isinstance(value, (list, tuple)):
        values = value
    else:
        raise TypeError(f"{field_name} must be a string or list of strings.")

    normalized: list[str] = []
    for item in values:
        if not isinstance(item, str):
            raise TypeError(f"Each value in {field_name} must be a string.")

        item = item.strip().lower()
        if item and item not in normalized:
            normalized.append(item)

    return normalized


def merge_extracted_data(
    draft: Mapping[str, Any],
    extracted_data: Mapping[str, Any],
) -> Draft:
    """Merge newly extracted fields into a copy of the current draft.

    List fields are combined without duplicates. Scalar fields are replaced
    by a newer nonempty value. ``None`` and empty strings are ignored so an
    uncertain extraction cannot erase information already collected. This is
    the intake pipeline's bridge from one extraction result to the next draft.
    """
    if not isinstance(draft, Mapping):
        raise TypeError("draft must be a dictionary-like object.")
    if not isinstance(extracted_data, Mapping):
        raise TypeError("extracted_data must be a dictionary-like object.")

    unknown_fields = set(extracted_data) - REQUEST_FIELDS
    if unknown_fields:
        unknown = ", ".join(sorted(unknown_fields))
        raise ValueError(f"Unknown extracted field(s): {unknown}")

    merged: Draft = dict(draft)

    for field_name, value in extracted_data.items():
        if value is None:
            continue

        if field_name in LIST_FIELDS:
            incoming_values = _normalize_list(value, field_name)
            if not incoming_values:
                continue

            existing_values = _normalize_list(
                merged.get(field_name, []),
                field_name,
            )
            merged[field_name] = list(
                dict.fromkeys([*existing_values, *incoming_values])
            )
            continue

        if isinstance(value, str):
            value = value.strip()
            if not value:
                continue

            if field_name == "preferred_language":
                value = value.lower()

        # This deliberately preserves False; checking ``if value`` would
        # incorrectly discard an explicit wheelchair=False answer.
        merged[field_name] = value

    return merged


def finalize_session(session: ReferralSession) -> ReferralRequest:
    """Create and link a ReferralRequest from a completed session draft.

    The operation is idempotent: calling it again for a completed session
    returns the existing referral instead of creating a duplicate.
    """
    with transaction.atomic():
        locked_session = (
            ReferralSession.objects
            .select_for_update()
            .get(pk=session.pk)
        )

        if locked_session.referral_request_id:
            return locked_session.referral_request

        if locked_session.status == ReferralSession.Status.ABANDONED:
            raise ValueError("Cannot finalize an abandoned referral session.")

        missing_fields = get_missing_required_fields(locked_session.draft)
        if missing_fields:
            missing = ", ".join(missing_fields)
            raise ValueError(
                f"Cannot finalize session; missing required field(s): {missing}."
            )

        serializer = ReferralRequestSerializer(data=locked_session.draft)
        serializer.is_valid(raise_exception=True)
        referral = serializer.save()

        locked_session.referral_request = referral
        locked_session.status = ReferralSession.Status.COMPLETED
        locked_session.save(
            update_fields=["referral_request", "status", "updated_at"]
        )

        return referral

def get_contextual_required_fields(
    draft: Mapping[str, Any],
) -> list[str]:
    """Return fields required by the needs currently in the draft.

    The static minimum fields are deliberately not included here. This
    function only answers: "What additional fields does this context need?"
    """
    if not isinstance(draft, Mapping):
        raise TypeError("draft must be a dictionary-like object.")

    needs = _normalize_list(draft.get("needs", []), "needs")
    contextual_fields: set[str] = set()

    for need in needs:
        contextual_fields.update(
            CONTEXT_REQUIRED_FIELDS.get(need, frozenset())
        )

    return sorted(contextual_fields)


def get_required_fields(draft: Mapping[str, Any]) -> list[str]:
    """Return the complete requirement set for the current draft."""
    required_fields = set(STATIC_REQUIRED_FIELDS)
    required_fields.update(get_contextual_required_fields(draft))
    return sorted(required_fields)


def _is_missing(draft: Mapping[str, Any], field_name: str) -> bool:
    """Return whether a draft field lacks a usable answer for intake."""
    if field_name not in draft:
        return True

    value = draft[field_name]
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, (list, tuple)):
        return not value

    # False is a meaningful answer, so it must not count as missing.
    return False


def get_missing_required_fields(draft: Mapping[str, Any]) -> list[str]:
    """Return required fields that have not been answered yet."""
    return [
        field_name
        for field_name in get_required_fields(draft)
        if _is_missing(draft, field_name)
    ]


def process_intake_message(
    session: ReferralSession,
    message: str,
) -> dict[str, Any]:
    """Process one chat turn and persist the updated intake session.

    This function extracts and merges the new message, recalculates missing
    requirements, and returns either the next question or a ready status. It
    deliberately leaves finalization and recommendations to a later search
    action.
    """
    if not isinstance(session, ReferralSession):
        raise TypeError("session must be a ReferralSession instance.")
    if not isinstance(message, str):
        raise TypeError("message must be a string.")

    # Extraction may eventually call a slow local or remote LLM. Run it
    # before opening the transaction so the database row is not locked while
    # waiting for model output.
    extracted_data = extract_fields(message)

    with transaction.atomic():
        locked_session = (
            ReferralSession.objects
            .select_for_update()
            .get(pk=session.pk)
        )

        if locked_session.status == ReferralSession.Status.ABANDONED:
            raise ValueError("Cannot process an abandoned referral session.")

        if locked_session.referral_request_id:
            return {
                "session_id": str(locked_session.id),
                "status": locked_session.status,
                "draft": locked_session.draft,
                "missing_fields": [],
                "question": None,
                "referral_request_id": locked_session.referral_request_id,
            }

        updated_draft = merge_extracted_data(
            locked_session.draft,
            extracted_data,
        )
        missing_fields = get_missing_required_fields(updated_draft)

        locked_session.draft = updated_draft
        locked_session.status = (
            ReferralSession.Status.COLLECTING
            if missing_fields
            else ReferralSession.Status.READY
        )
        locked_session.save(update_fields=["draft", "status", "updated_at"])

        next_question = (
            FIELD_QUESTIONS.get(missing_fields[0])
            if missing_fields
            else None
        )

        return {
            "session_id": str(locked_session.id),
            "status": locked_session.status,
            "draft": locked_session.draft,
            "missing_fields": missing_fields,
            "question": next_question,
        }
