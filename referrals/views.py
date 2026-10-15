from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import CommunityResource, ReferralSession
from .recommendation import recommend_resources
from .serializers import IntakeMessageSerializer, ReferralRequestSerializer
from .services.intake import (
    finalize_session,
    get_missing_required_fields,
    process_intake_message,
)
from .services.llm_extraction import GroqExtractionError


class RecommendationView(APIView):
    def post(self, request):
        """Validate a structured referral and return ranked recommendations."""
        serializer = ReferralRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        referral = serializer.save()
        results = recommend_resources(referral)

        response_data = {
            "referral": serializer.data,
            "recommendations": _recommendation_payload(results),
        }

        return Response(
            response_data,
            status=status.HTTP_201_CREATED,
        )


class IntakeView(APIView):
    def post(self, request):
        serializer = IntakeMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        session_id = serializer.validated_data.get("session_id")

        is_new_session = session_id is None

        if session_id:
            session = get_object_or_404(
                ReferralSession,
                pk=session_id,
            )
        else:
            session = ReferralSession.objects.create()

        try:
            result = process_intake_message(
                session=session,
                message=serializer.validated_data["message"],
            )
        except GroqExtractionError:
            if is_new_session:
                session.delete()

            return Response(
                {
                    "detail": (
                        "Intake extraction is temporarily unavailable. "
                        "Please try again."
                    )
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response(
            result,
            status=status.HTTP_200_OK,
        )


class SessionSearchView(APIView):
    def post(self, request, session_id):
        session = get_object_or_404(
            ReferralSession,
            pk=session_id,
        )

        missing_fields = get_missing_required_fields(session.draft)

        if missing_fields:
            return Response(
                {
                    "detail": "This session is not ready for searching.",
                    "missing_fields": missing_fields,
                },
                status=status.HTTP_409_CONFLICT,
            )

        referral = finalize_session(session)
        results = recommend_resources(referral)

        return Response(
            {
                "session_id": str(session.id),
                "referral": ReferralRequestSerializer(referral).data,
                "recommendations": _recommendation_payload(results),
            },
            status=status.HTTP_200_OK,
        )


def _recommendation_payload(results):
    """Add the resource context needed by clients to present a referral."""
    resources = CommunityResource.objects.in_bulk(
        [result.resource_id for result in results]
    )

    return [
        {
            "resource_id": result.resource_id,
            "resource_name": result.resource_name,
            "eligible": result.eligible,
            "score": result.score,
            "reasons": result.reasons,
            "warnings": result.warnings,
            "description": resources[result.resource_id].description,
            "logo_url": (
                resources[result.resource_id].logo.url
                if resources[result.resource_id].logo
                else None
            ),
            "city": resources[result.resource_id].city,
            "state": resources[result.resource_id].state,
            "source_url": resources[result.resource_id].source_url,
            "last_verified_at": (
                resources[result.resource_id].last_verified_at.isoformat()
                if resources[result.resource_id].last_verified_at
                else None
            ),
        }
        for result in results
    ]


class HomeView(TemplateView):
    template_name = "referrals/home.html"
