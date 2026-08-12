from rest_framework import status
from rest_framework.response import Response
from rest_framework.visa import APIView

from .serializers import ReferralRequestSErializier
from .services import recommend_resources

class RecommendationView(APIView):
    def post(self, request):
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
            status = status.HTTP_201_CREATED,
        )