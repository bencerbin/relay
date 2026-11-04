from django.test import TestCase

from referrals.models import ReferralRequest
from referrals.recommendation import recommend_resources


class RecommendationRankingTests(TestCase):
    def test_specific_sports_request_beats_broad_physical_activity_match(self):
        referral = ReferralRequest.objects.create(
            county="Fairfield",
            needs=["physical_activity"],
            subneeds=["sports_league"],
        )

        results = recommend_resources(referral)
        by_name = {result.resource_name: result for result in results}

        boys_and_girls = by_name["Boys & Girls Club of Stamford"]
        chelsea_piers = by_name["Chelsea Piers Athletic Club"]
        american_heart = by_name["American Heart Association"]

        self.assertGreater(boys_and_girls.score, american_heart.score)
        self.assertGreater(chelsea_piers.score, american_heart.score)
        self.assertIn(
            "Matches specific request: Sports League.",
            boys_and_girls.reasons,
        )

    def test_workout_plan_matches_physical_fitness_resources(self):
        referral = ReferralRequest.objects.create(
            county="Fairfield",
            needs=["physical_activity"],
            subneeds=["physical_fitness"],
        )

        results = recommend_resources(referral)
        by_name = {result.resource_name: result for result in results}

        american_heart = by_name["American Heart Association"]
        boys_and_girls = by_name["Boys & Girls Club of Stamford"]

        self.assertIn(
            "Matches specific request: Physical Fitness.",
            american_heart.reasons,
        )
        self.assertGreater(american_heart.score, boys_and_girls.score)

    def test_nonclinical_youth_program_is_not_a_mental_health_match(self):
        referral = ReferralRequest.objects.create(
            county="Fairfield",
            needs=["mental_health"],
            subneeds=["mental_health_counseling"],
        )

        results = recommend_resources(referral)
        by_name = {result.resource_name: result for result in results}

        self.assertFalse(
            by_name["Boys & Girls Club of Stamford"].eligible
        )
        self.assertGreater(
            by_name["Community Health Center"].score,
            by_name["Boys & Girls Club of Stamford"].score,
        )

    def test_wic_is_a_strong_match_for_snap_assistance(self):
        referral = ReferralRequest.objects.create(
            county="Fairfield",
            needs=["food"],
            subneeds=["snap_benefits"],
        )

        results = recommend_resources(referral)
        by_name = {result.resource_name: result for result in results}

        wic = by_name["Women Infant Child Program"]
        self.assertTrue(wic.eligible)
        self.assertEqual(wic.score, 100)
        self.assertIn(
            "Matches specific request: SNAP Benefits.",
            wic.reasons,
        )

    def test_career_request_matches_resources_with_career_support(self):
        referral = ReferralRequest.objects.create(
            county="Fairfield",
            needs=["employment"],
            subneeds=["career_support"],
        )

        results = recommend_resources(referral)
        by_name = {result.resource_name: result for result in results}

        family_centers = by_name["Family Centers"]
        ferguson_library = by_name["Ferguson Library"]
        american_heart = by_name["American Heart Association"]

        self.assertTrue(family_centers.eligible)
        self.assertTrue(ferguson_library.eligible)
        self.assertIn(
            "Matches specific request: Career Support.",
            family_centers.reasons,
        )
        self.assertIn(
            "Does not provide requested service: Employment.",
            american_heart.reasons,
        )
        self.assertIn(
            "Does not list requested specific service: Career Support.",
            american_heart.warnings,
        )
