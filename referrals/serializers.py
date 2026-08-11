from rest_framework import serializers

from .models import CommunityResource, ReferralRequest

class ReferralRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReferralRequest
        fields = [
            "id",
            "age",
            "county",
            "city",
            "preferred_language",
            "insurance_type",
            "wheelchair_required",
            "needs",
            "created_at",
        ]
        read_only_fields=["id","created_at"]
        
    def validate_needs(self, value: list[str]) -> list[str]: