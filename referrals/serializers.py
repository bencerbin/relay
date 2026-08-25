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
            "wheelchair",
            "needs",
            "healthcare_specialties",
            "population_context",
            "service_modalities",
            "program_purposes",
            "created_at",
        ]
        read_only_fields=["id","created_at"]
        
    def validate_needs(self, value: list[str]) -> list[str]:
        if not value:
            raise serializers.ValidationError("At least one resource need is required.")
        
        if not all(isinstance(item,str) for item in value):
            raise serializers.ValidationError("Each need must be a string.")
        
        return value
    
    
    
class CommunityResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommunityResource
        fields = "__all__"
