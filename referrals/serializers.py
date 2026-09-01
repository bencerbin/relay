from rest_framework import serializers

from .models import CommunityResource, ReferralRequest


class StrictStringField(serializers.CharField):
    """A CharField that rejects non-string JSON values instead of coercing them."""

    default_error_messages = {
        "invalid": "Expected a string.",
    }

    def to_internal_value(self, data):
        if not isinstance(data, str):
            self.fail("invalid")

        return super().to_internal_value(data)


class ReferralRequestSerializer(serializers.ModelSerializer):
    needs = serializers.ListField(
        child=StrictStringField(),
        allow_empty=False,
    )

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
        """Ensure a finalized referral contains at least one string need."""
        if not value:
            raise serializers.ValidationError("At least one resource need is required.")
        
        if not all(isinstance(item,str) for item in value):
            raise serializers.ValidationError("Each need must be a string.")
        
        return value
    
class IntakeMessageSerializer(serializers.Serializer):
    session_id = serializers.UUIDField(
        required=False,
        allow_null=True,
    )
    message = serializers.CharField()
    
    
class CommunityResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommunityResource
        fields = "__all__"
