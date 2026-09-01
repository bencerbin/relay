from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from referrals.models import CommunityResource, ReferralRequest


class RecommendationAPITests(APITestCase):
    """Test the public API contract for structured recommendations."""

    def setUp(self):
        self.url = reverse("recommendations")

        CommunityResource.objects.create(
            name="Stamford Meal Delivery",
            city="Stamford",
            state="Connecticut",
            description="Meal delivery for Fairfield County residents.",
            counties_served=["Fairfield"],
            cities_served=["Stamford"],
            needs_addressed=["food_delivery"],
            service_modalities=["delivery"],
            accepted_insurance=["Medicaid"],
            supported_languages=["English"],
            wheelchair_accessible=True,
            active=True,
        )
        CommunityResource.objects.create(
            name="New Haven Meal Delivery",
            city="New Haven",
            state="Connecticut",
            description="Meal delivery for New Haven County residents.",
            counties_served=["New Haven"],
            cities_served=["New Haven"],
            needs_addressed=["food_delivery"],
            service_modalities=["delivery"],
            active=True,
        )
        CommunityResource.objects.create(
            name="Inactive Fairfield Pantry",
            city="Stamford",
            state="Connecticut",
            description="An inactive food resource for testing.",
            counties_served=["Fairfield"],
            cities_served=["Stamford"],
            needs_addressed=["food_delivery"],
            active=False,
        )

    def valid_payload(self):
        return {
            "age": 72,
            "county": "Fairfield",
            "city": "Stamford",
            "preferred_language": "english",
            "insurance_type": "Medicaid",
            "wheelchair": False,
            "needs": ["food_delivery"],
            "healthcare_specialties": [],
            "population_context": [],
            "service_modalities": ["delivery"],
            "program_purposes": [],
        }

    def test_valid_request_returns_referral_and_recommendations(self):
        response = self.client.post(
            self.url,
            self.valid_payload(),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ReferralRequest.objects.count(), 1)
        self.assertIn("referral", response.data)
        self.assertIn("recommendations", response.data)
        self.assertEqual(response.data["referral"]["county"], "Fairfield")

        recommendations = response.data["recommendations"]
        names = [recommendation["resource_name"] for recommendation in recommendations]
        self.assertIn("Stamford Meal Delivery", names)
        self.assertIn("New Haven Meal Delivery", names)
        self.assertNotIn("Inactive Fairfield Pantry", names)

        eligible_result = next(
            recommendation
            for recommendation in recommendations
            if recommendation["resource_name"] == "Stamford Meal Delivery"
        )
        self.assertTrue(eligible_result["eligible"])
        self.assertGreater(eligible_result["score"], 0)

    def test_invalid_request_returns_bad_request_and_creates_no_referral(self):
        payload = self.valid_payload()
        payload.pop("county")

        response = self.client.post(
            self.url,
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("county", response.data)
        self.assertEqual(ReferralRequest.objects.count(), 0)

    def test_empty_needs_returns_bad_request(self):
        payload = self.valid_payload()
        payload["needs"] = []

        response = self.client.post(
            self.url,
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("needs", response.data)
        self.assertEqual(ReferralRequest.objects.count(), 0)

    def test_missing_needs_returns_bad_request(self):
        payload = self.valid_payload()
        payload.pop("needs")

        response = self.client.post(
            self.url,
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("needs", response.data)
        self.assertEqual(ReferralRequest.objects.count(), 0)

    def test_string_needs_returns_bad_request(self):
        payload = self.valid_payload()
        payload["needs"] = "food_delivery"

        response = self.client.post(
            self.url,
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("needs", response.data)
        self.assertEqual(ReferralRequest.objects.count(), 0)

    def test_non_string_need_item_returns_bad_request(self):
        payload = self.valid_payload()
        payload["needs"] = [123]

        response = self.client.post(
            self.url,
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("needs", response.data)
        self.assertEqual(ReferralRequest.objects.count(), 0)

    def test_mismatched_county_resource_is_ineligible(self):
        response = self.client.post(
            self.url,
            self.valid_payload(),
            format="json",
        )

        new_haven_result = next(
            recommendation
            for recommendation in response.data["recommendations"]
            if recommendation["resource_name"] == "New Haven Meal Delivery"
        )
        self.assertFalse(new_haven_result["eligible"])
        self.assertEqual(new_haven_result["score"], 0)
