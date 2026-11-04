from dataclasses import dataclass, field

from .models import CommunityResource, ReferralRequest


@dataclass
class EligibilityResult:
    resource_id: int
    resource_name: str
    eligible: bool
    reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    score: int = 0


def normalize(value: str) -> str:
    """Normalize a value so matching is case-insensitive and whitespace-safe."""
    return value.strip().lower()


DISPLAY_LABEL_OVERRIDES = {
    "ebt": "EBT",
    "k-12": "K–12",
    "snap": "SNAP",
    "snap_benefits": "SNAP Benefits",
    "wic": "WIC",
}


def display_label(value: str) -> str:
    """Convert an internal tag into a readable label for users."""
    normalized = normalize(value)
    if normalized in DISPLAY_LABEL_OVERRIDES:
        return DISPLAY_LABEL_OVERRIDES[normalized]
    return normalized.replace("_", " ").replace("-", " ").title()


def display_labels(values: set[str]) -> str:
    """Format a collection of internal tags for recommendation explanations."""
    return ", ".join(display_label(value) for value in sorted(values))


def evaluate_resource(
    referral: ReferralRequest,
    resource: CommunityResource,
) -> EligibilityResult:
    """Score one resource against a finalized referral request."""
    reasons: list[str] = []
    warnings: list[str] = []
    failures: list[str] = []
    score = 0

    referral_needs = {normalize(item) for item in referral.needs}
    resource_needs_addressed = {
        normalize(item) for item in resource.needs_addressed
    }

    matching_needs = referral_needs & resource_needs_addressed

    if matching_needs:
        reasons.append(
            f"Provides requested service: {display_labels(matching_needs)}."
        )
        score += 40
    else:
        requested_service_text = display_labels(referral_needs)
        if requested_service_text:
            failures.append(
                f"Does not provide requested service: {requested_service_text}."
            )
        else:
            failures.append("Does not provide a requested service.")

    requested_subneeds = {
        normalize(item) for item in referral.subneeds
    }
    available_subneeds = {
        normalize(item) for item in resource.subneeds
    }

    if requested_subneeds:
        matching_subneeds = requested_subneeds & available_subneeds
        if matching_subneeds:
            matched_subneed_score = round(
                35 * len(matching_subneeds) / len(requested_subneeds)
            )
            score += matched_subneed_score
            reasons.append(
                "Matches specific request: "
                f"{display_labels(matching_subneeds)}."
            )
        elif available_subneeds:
            service_word = (
                "service"
                if len(requested_subneeds) == 1
                else "services"
            )
            warnings.append(
                f"Does not list requested specific {service_word}: "
                f"{display_labels(requested_subneeds)}."
            )
        else:
            warnings.append("Specific services are not documented.")

    requested_specialties = {
        normalize(item) for item in referral.healthcare_specialties
    }
    available_specialties = {
        normalize(item) for item in resource.healthcare_specialties
    }

    if requested_specialties:
        matching_specialties = requested_specialties & available_specialties
        if matching_specialties:
            reasons.append(
                "Offers requested specialty: "
                f"{display_labels(matching_specialties)}."
            )
            score += 20
        elif available_specialties:
            failures.append("Does not offer a requested healthcare specialty.")
        else:
            warnings.append("Healthcare specialties are not documented.")

    requested_populations = {
        normalize(item) for item in referral.population_context
    }
    available_populations = {
        normalize(item) for item in resource.population_served
    }

    if requested_populations:
        matching_populations = requested_populations & available_populations
        if matching_populations:
            reasons.append(
                "Serves requested population: "
                f"{display_labels(matching_populations)}."
            )
            score += 10
        elif available_populations:
            failures.append("Does not serve the requested population.")
        else:
            warnings.append("Population served is not documented.")

    requested_modalities = {
        normalize(item) for item in referral.service_modalities
    }
    available_modalities = {
        normalize(item) for item in resource.service_modalities
    }

    if requested_modalities:
        matching_modalities = requested_modalities & available_modalities
        if matching_modalities:
            reasons.append(
                "Offers requested service format: "
                f"{display_labels(matching_modalities)}."
            )
            score += 10
        elif available_modalities:
            failures.append("Does not offer a requested service format.")
        else:
            warnings.append("Service format is not documented.")

    requested_purposes = {
        normalize(item) for item in referral.program_purposes
    }
    available_purposes = {
        normalize(item) for item in resource.program_purposes
    }

    if requested_purposes:
        matching_purposes = requested_purposes & available_purposes
        if matching_purposes:
            reasons.append(
                "Supports requested purpose: "
                f"{display_labels(matching_purposes)}."
            )
            score += 10
        elif available_purposes:
            failures.append("Does not support the requested program purpose.")
        else:
            warnings.append("Program purpose is not documented.")

    if referral.county:
        counties = {normalize(item) for item in resource.counties_served}

        if normalize(referral.county) in counties:
            reasons.append(f"Serves {referral.county} County.")
            score += 25
        else:
            failures.append(f"Does not serve {referral.county} County.")

    if referral.city:
        cities = {normalize(item) for item in resource.cities_served}
        if normalize(referral.city) in cities:
            reasons.append(f"Serves {referral.city}.")
            score += 15

    if referral.age is None:
        if resource.minimum_age is not None or resource.maximum_age is not None:
            warnings.append("Age is required to confirm eligibility.")
    else:
        if (
            resource.minimum_age is not None
            and referral.age < resource.minimum_age
        ):
            failures.append(f"Minimum eligible age is {resource.minimum_age}.")
        elif (
            resource.maximum_age is not None
            and referral.age > resource.maximum_age
        ):
            failures.append(f"Maximum eligible age is {resource.maximum_age}.")
        else:
            reasons.append("Meets known requirements")
            score += 10

    if referral.wheelchair:
        if resource.wheelchair_accessible:
            reasons.append("Wheelchair Accessible")
            score += 10
        else:
            failures.append("Wheelchair accessibility is not available.")

    if referral.preferred_language:
        supported_languages = {
            normalize(item) for item in resource.supported_languages
        }

        if normalize(referral.preferred_language) in supported_languages:
            reasons.append(f"Supports {referral.preferred_language}.")
            score += 10
        else:
            warnings.append(
                f"Does not support {referral.preferred_language}."
            )

    if referral.insurance_type:
        accepted_insurance = {
            normalize(item) for item in resource.accepted_insurance
        }

        if not accepted_insurance:
            warnings.append("Insurance requirements are not documented.")
        elif normalize(referral.insurance_type) in accepted_insurance:
            reasons.append(f"Accepts {referral.insurance_type}.")
            score += 5
        else:
            failures.append(
                f"Does not list {referral.insurance_type} as accepted."
            )

    return EligibilityResult(
        resource_id=resource.id,
        resource_name=resource.name,
        eligible=len(failures) == 0,
        reasons=reasons + failures,
        warnings=warnings,
        score=min(score, 100) if not failures else 0,
    )


def recommend_resources(referral: ReferralRequest) -> list[EligibilityResult]:
    """Evaluate and rank all active resources for a finalized referral."""
    resources = CommunityResource.objects.filter(active=True)

    results = [
        evaluate_resource(referral, resource)
        for resource in resources
    ]

    return sorted(
        results,
        key=lambda result: (result.eligible, result.score),
        reverse=True,
    )
