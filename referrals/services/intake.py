from collections.abc import Mapping
from typing import Any

from django.db import transaction

from ..models import ReferralRequest, ReferralSession
from ..serializers import ReferralRequestSerializer


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


def _normalize_list(value: Any, field_name: str) -> list[str]:
    """Convert one extracted list field into a clean, canonical list."""
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
    uncertain extraction cannot erase information already collected.
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

        serializer = ReferralRequestSerializer(data=locked_session.draft)
        serializer.is_valid(raise_exception=True)
        referral = serializer.save()

        locked_session.referral_request = referral
        locked_session.status = ReferralSession.Status.COMPLETED
        locked_session.save(
            update_fields=["referral_request", "status", "updated_at"]
        )

        return referral
