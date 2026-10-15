from django.db import migrations, models


FAKE_RESOURCE_NAMES = [
    "Fairfield Senior Meal Delivery",
    "Stamford Community Pantry",
    "New Haven Meal Support",
    "Fairfield Senior Oncology Center",
    "New Haven Dermatology Access",
]


STAMFORD_MEMBERS = [
    {
        "name": "American Heart Association",
        "description": "A nonprofit resource for cardiovascular research, physical fitness education, healthy eating, CPR training, and school programs.",
        "needs_addressed": ["healthcare", "food", "physical_activity"],
        "logo": "resource_logos/american-heart-association.png",
        "source_url": "https://www.heart.org/en/",
    },
    {
        "name": "Boys & Girls Club of Stamford",
        "description": "Youth-focused after-school and enrichment programs for children in grades K–12, including STEM, emotional intelligence, and career preparation.",
        "needs_addressed": ["education", "physical_activity", "mental_health"],
        "logo": "resource_logos/boys-girls-club-of-stamford.png",
        "source_url": "https://www.bgcastamford.org/",
    },
    {
        "name": "Charter Oak Communities",
        "description": "Affordable and equitable housing for Stamford residents, including family-friendly communities across 21 properties.",
        "needs_addressed": ["housing"],
        "logo": "resource_logos/charter-oak-communities.png",
        "source_url": "https://charteroakcommunities.org/",
    },
    {
        "name": "Chartwells",
        "description": "Stamford Public Schools food and dining services, with information about free school meals and food assistance programs.",
        "needs_addressed": ["food"],
        "logo": "resource_logos/chartwells.png",
        "source_url": "https://www.stamfordpublicschools.org/departments/chartwells-dining-services",
    },
    {
        "name": "Chelsea Piers Athletic Club",
        "description": "Sports, fitness, education, daycare, and preschool programming, with scholarship opportunities through the Chelsea Piers Foundation.",
        "needs_addressed": ["physical_activity", "childcare"],
        "logo": "resource_logos/chelsea-piers-athletic-club.png",
        "source_url": "https://sports.chelseapiers.com/connecticut/stamford/cp-kids",
    },
    {
        "name": "Childcare Learning Centers",
        "description": "Nonprofit early childhood education with curriculum and programming that support children’s social and emotional development.",
        "needs_addressed": ["childcare", "education", "mental_health"],
        "logo": "resource_logos/childrens-learning-centers.png",
        "source_url": "https://clcfc.org/",
    },
    {
        "name": "Community Health Center",
        "description": "Community-based medical, dental, behavioral, and school-based healthcare, with insurance assistance and child guidance services.",
        "needs_addressed": ["healthcare", "mental_health"],
        "logo": "resource_logos/community-health-center.jpg",
        "source_url": "https://www.chc1.com/locations/stamford-fifth-street/",
    },
    {
        "name": "Connecticut Foodshare",
        "description": "Food distribution and long-term food security support, including a mobile pantry locator, SNAP applications, and nutritious recipes.",
        "needs_addressed": ["food"],
        "logo": "resource_logos/connecticut-foodshare.png",
        "source_url": "https://www.ctfoodshare.org/",
    },
    {
        "name": "Fairgate Farm",
        "description": "Locally grown produce, pay-what-you-can food access, food security support, and volunteer and educational opportunities.",
        "needs_addressed": ["food", "education", "physical_activity"],
        "logo": "resource_logos/fairgate-farm.png",
        "source_url": "https://fairgatefarm.com/",
    },
    {
        "name": "Family Centers",
        "description": "Education, health, and human services for children, adults, and families, including healthcare, mental health, career, and education programs.",
        "needs_addressed": ["healthcare", "mental_health", "education", "childcare", "parenting"],
        "logo": "resource_logos/family-centers.png",
        "source_url": "https://familycenters.org/",
    },
    {
        "name": "Ferguson Library",
        "description": "Workshops, educational resources, and a local resource guide covering healthcare, transportation, food, career assistance, and more.",
        "needs_addressed": ["education", "transportation", "food", "community_resources"],
        "logo": "resource_logos/ferguson-library.jpg",
        "source_url": "https://www.fergusonlibrary.org/",
    },
    {
        "name": "KIDS’ FANS",
        "description": "A Stamford Health childhood wellness program promoting healthy nutrition, obesity prevention, physical activity, and pediatric counseling.",
        "needs_addressed": ["food", "physical_activity", "healthcare"],
        "logo": "resource_logos/kids-fans.png",
        "source_url": "https://www.stamfordhealth.org/care-treatment/pediatrics/kids-fans/",
    },
    {
        "name": "Medical Home Initiative",
        "description": "Care coordination for children with physical, developmental, behavioral, emotional, or special healthcare needs, ages 0–21.",
        "needs_addressed": ["healthcare", "mental_health", "community_resources"],
        "logo": "resource_logos/medical-home-initiative.png",
        "source_url": "https://www.stamfordhealth.org/care-treatment/pediatrics/mhisouthwest/",
    },
    {
        "name": "Mill River Park Collaborative",
        "description": "A public-private park conservancy offering day camps, after-school programs, ecological workshops, and youth opportunities.",
        "needs_addressed": ["physical_activity", "education", "childcare"],
        "logo": "resource_logos/mill-river-park-collaborative.png",
        "source_url": "https://millriverpark.org/",
    },
    {
        "name": "Optimus Healthcare",
        "description": "A patient-centered medical home offering primary, pediatric, behavioral, reproductive, and dental healthcare, especially for uninsured and underserved patients.",
        "needs_addressed": ["healthcare", "mental_health"],
        "logo": "resource_logos/optimus-healthcare.png",
        "source_url": "https://optimushealthcare.org/",
    },
    {
        "name": "ShopRite Supermarket",
        "description": "Stamford grocery locations offering food assistance information and guidance for ordering groceries with SNAP benefits.",
        "needs_addressed": ["food"],
        "logo": "resource_logos/shoprite.png",
        "source_url": "https://cingarifamilymarkets.com/",
    },
    {
        "name": "Saint Joseph Parenting Center",
        "description": "Parent education, case management, and community resource support through a nonsectarian primary prevention nonprofit.",
        "needs_addressed": ["parenting", "education", "community_resources"],
        "logo": "resource_logos/saint-joseph-parenting-center.png",
        "source_url": "https://sjpcenter.org/",
    },
    {
        "name": "Stamford Health",
        "description": "Medical care, pediatric services, classes, and a provider directory connecting families with healthcare across the region.",
        "needs_addressed": ["healthcare"],
        "logo": "resource_logos/stamford-health.png",
        "source_url": "https://www.stamfordhealth.org/",
    },
    {
        "name": "Stamford Public Schools",
        "description": "District resources including mental health, homelessness, food assistance, transportation, technology, registration, and family information.",
        "needs_addressed": ["education", "mental_health", "food", "transportation"],
        "logo": "resource_logos/stamford-public-schools.png",
        "source_url": "https://www.stamfordpublicschools.org/",
    },
    {
        "name": "Stamford Public Education Foundation",
        "description": "Mentorship, guidance, scholarships, events, and volunteer opportunities that help Stamford students thrive academically, socially, and emotionally.",
        "needs_addressed": ["education", "mental_health", "community_resources"],
        "logo": "resource_logos/stamford-public-education-foundation.png",
        "source_url": "https://spefct.org/",
    },
    {
        "name": "Stamford Recreation",
        "description": "Youth camps, preschool and after-school programs, swimming lessons, sports leagues, parks, beaches, and recreation permits.",
        "needs_addressed": ["physical_activity", "childcare", "education"],
        "logo": "resource_logos/stamford-recreation.png",
        "source_url": "https://www.stamfordrecreation.com/",
    },
    {
        "name": "United Way of Coastal and Western Connecticut",
        "description": "Free local resources that help families address critical needs and build financial stability, with connections to community advocacy and nonprofit partners.",
        "needs_addressed": ["food", "housing", "healthcare", "community_resources", "employment"],
        "logo": "resource_logos/united-way-coastal-and-western-connecticut.png",
        "source_url": "https://www.unitedwaycwc.org/blog/free-community-resources-greater-norwalk",
    },
    {
        "name": "Women Infant Child Program",
        "description": "Nutrition education, supplemental foods, healthcare referrals, breastfeeding support, and connections to food, housing, utility, and public benefit assistance.",
        "needs_addressed": ["food", "healthcare", "housing"],
        "logo": "resource_logos/women-infant-child-program.png",
        "source_url": "https://connecticut.wicresources.org/",
    },
]


def seed_stamford_members(apps, schema_editor):
    CommunityResource = apps.get_model("referrals", "CommunityResource")
    CommunityResource.objects.filter(name__in=FAKE_RESOURCE_NAMES).delete()

    for resource in STAMFORD_MEMBERS:
        CommunityResource.objects.update_or_create(
            name=resource["name"],
            defaults={
                "city": "Stamford",
                "state": "CT",
                "description": resource["description"],
                "logo": resource["logo"],
                "counties_served": ["Fairfield"],
                "cities_served": ["Stamford"],
                "needs_addressed": resource["needs_addressed"],
                "healthcare_specialties": [],
                "population_served": ["children", "families"],
                "service_modalities": ["in_person", "community"],
                "program_purposes": ["prevention", "ongoing_support"],
                "provider_metadata": {
                    "source_document": "Children's Health Collaborative.docx",
                    "source_section": "Our Members",
                },
                "minimum_age": None,
                "maximum_age": None,
                "accepted_insurance": [],
                "supported_languages": [],
                "wheelchair_accessible": False,
                "active": True,
                "source_url": resource["source_url"],
                "source_excerpt": resource["description"],
                "last_verified_at": None,
            },
        )


class Migration(migrations.Migration):
    dependencies = [
        ("referrals", "0003_referralsession"),
    ]

    operations = [
        migrations.AlterField(
            model_name="communityresource",
            name="description",
            field=models.TextField(),
        ),
        migrations.AddField(
            model_name="communityresource",
            name="logo",
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to="resource_logos/",
            ),
        ),
        migrations.RunPython(
            seed_stamford_members,
            migrations.RunPython.noop,
        ),
    ]
