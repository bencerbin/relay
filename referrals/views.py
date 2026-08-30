from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import ReferralRequestSerializer
from .recommendation import recommend_resources

from .models import ReferralSession
from .serializers import IntakeMessageSerializer
from .services.intake import process_intake_message


class RecommendationView(APIView):
    def post(self, request):
        """Validate a structured referral and return ranked recommendations."""
        serializer = ReferralRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        referral = serializer.save()
        results = recommend_resources(referral)

        response_data = {
            "referral": serializer.data,
            "recommendations": [
                {
                    "resource_id": result.resource_id,
                    "resource_name": result.resource_name,
                    "eligible": result.eligible,
                    "score": result.score,
                    "reasons": result.reasons,
                    "warnings": result.warnings,
                }
                for result in results
            ],
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
        
        if session_id:
            session = get_object_or_404(
                ReferralSession,
                pk=session_id,
            )
        else:
            session = ReferralSession.objects.create()
            
        result = process_intake_message(
            session=session,
            message=serializer.validated_data.get("message")
            )
        
        return Response(
            result,
            status = status.HTTP_200_OK,
        )