from django.db import migrations, models


SUBNEEDS_BY_RESOURCE = {
    "American Heart Association": [
        "physical_fitness",
        "nutrition_education",
        "healthy_eating",
    ],
    "Boys & Girls Club of Stamford": [
        "sports_league",
        "after_school",
        "youth_enrichment",
    ],
    "Charter Oak Communities": [
        "affordable_housing",
        "housing_assistance",
    ],
    "Chartwells": [
        "school_meals",
        "food_assistance",
    ],
    "Chelsea Piers Athletic Club": [
        "sports_league",
        "physical_fitness",
        "swimming_lessons",
        "childcare",
        "preschool",
    ],
    "Childcare Learning Centers": [
        "childcare",
        "preschool",
        "youth_enrichment",
    ],
    "Community Health Center": [
        "pediatric_healthcare",
        "primary_care",
        "behavioral_health",
        "dental_care",
    ],
    "Connecticut Foodshare": [
        "food_pantry",
        "mobile_pantry",
        "snap_benefits",
        "nutrition_education",
    ],
    "Fairgate Farm": [
        "food_assistance",
        "nutrition_education",
        "healthy_eating",
    ],
    "Family Centers": [
        "primary_care",
        "mental_health_counseling",
        "career_support",
        "childcare",
        "parenting_education",
    ],
    "Ferguson Library": [
        "education_support",
        "transportation_assistance",
        "food_assistance",
        "career_support",
        "community_resource_navigation",
    ],
    "KIDS’ FANS": [
        "nutrition_education",
        "healthy_eating",
        "physical_fitness",
    ],
    "Medical Home Initiative": [
        "care_coordination",
        "behavioral_health",
        "special_healthcare_needs",
    ],
    "Mill River Park Collaborative": [
        "summer_camp",
        "after_school",
        "youth_enrichment",
    ],
    "Optimus Healthcare": [
        "primary_care",
        "pediatric_healthcare",
        "behavioral_health",
        "dental_care",
    ],
    "ShopRite Supermarket": [
        "groceries",
        "snap_benefits",
        "food_assistance",
    ],
    "Saint Joseph Parenting Center": [
        "parenting_education",
        "community_resource_navigation",
    ],
    "Stamford Health": [
        "pediatric_healthcare",
        "primary_care",
        "community_resource_navigation",
    ],
    "Stamford Public Schools": [
        "mental_health_counseling",
        "food_assistance",
        "transportation_assistance",
    ],
    "Stamford Public Education Foundation": [
        "mentoring",
        "scholarships",
        "youth_enrichment",
    ],
    "Stamford Recreation": [
        "sports_league",
        "summer_camp",
        "swimming_lessons",
        "preschool",
        "after_school",
    ],
    "United Way of Coastal and Western Connecticut": [
        "food_assistance",
        "housing_assistance",
        "community_resource_navigation",
        "career_support",
    ],
    "Women Infant Child Program": [
        "nutrition_education",
        "food_assistance",
        "healthcare_referrals",
        "breastfeeding_support",
    ],
}


def populate_subneeds(apps, schema_editor):
    CommunityResource = apps.get_model("referrals", "CommunityResource")

    for name, subneeds in SUBNEEDS_BY_RESOURCE.items():
        CommunityResource.objects.filter(name=name).update(subneeds=subneeds)


class Migration(migrations.Migration):

    dependencies = [
        ("referrals", "0004_resource_logos_and_stamford_members"),
    ]

    operations = [
        migrations.AddField(
            model_name="communityresource",
            name="subneeds",
            field=models.JSONField(default=list),
        ),
        migrations.AddField(
            model_name="referralrequest",
            name="subneeds",
            field=models.JSONField(default=list),
        ),
        migrations.RunPython(
            populate_subneeds,
            migrations.RunPython.noop,
        ),
    ]
