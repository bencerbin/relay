from django.db import migrations


NON_CLINICAL_MENTAL_HEALTH_RESOURCES = [
    "Boys & Girls Club of Stamford",
    "Childcare Learning Centers",
    "Stamford Public Education Foundation",
]


def refine_resource_tags(apps, schema_editor):
    CommunityResource = apps.get_model("referrals", "CommunityResource")

    for name in NON_CLINICAL_MENTAL_HEALTH_RESOURCES:
        resource = CommunityResource.objects.filter(name=name).first()
        if resource is None:
            continue

        resource.needs_addressed = [
            need
            for need in resource.needs_addressed
            if need != "mental_health"
        ]
        resource.save(update_fields=["needs_addressed"])

    for name in (
        "Community Health Center",
        "Optimus Healthcare",
        "Connecticut Foodshare",
    ):
        resource = CommunityResource.objects.filter(name=name).first()
        if resource is None:
            continue

        tag = (
            "mental_health_counseling"
            if name != "Connecticut Foodshare"
            else "food_assistance"
        )
        if tag not in resource.subneeds:
            resource.subneeds = [
                *resource.subneeds,
                tag,
            ]
            resource.save(update_fields=["subneeds"])


class Migration(migrations.Migration):

    dependencies = [
        ("referrals", "0005_subneeds"),
    ]

    operations = [
        migrations.RunPython(
            refine_resource_tags,
            migrations.RunPython.noop,
        ),
    ]
