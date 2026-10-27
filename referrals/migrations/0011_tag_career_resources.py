from django.db import migrations


CAREER_RESOURCE_NAMES = (
    "Boys & Girls Club of Stamford",
    "Family Centers",
    "Ferguson Library",
    "United Way of Coastal and Western Connecticut",
)


def tag_career_resources(apps, schema_editor):
    CommunityResource = apps.get_model("referrals", "CommunityResource")

    for resource in CommunityResource.objects.filter(
        name__in=CAREER_RESOURCE_NAMES,
    ):
        needs = list(resource.needs_addressed or [])
        subneeds = list(resource.subneeds or [])

        if "employment" not in needs:
            needs.append("employment")
        if "career_support" not in subneeds:
            subneeds.append("career_support")

        resource.needs_addressed = needs
        resource.subneeds = subneeds
        resource.save(update_fields=["needs_addressed", "subneeds"])


class Migration(migrations.Migration):
    dependencies = [
        ("referrals", "0010_referralsession_pending_clarification"),
    ]

    operations = [
        migrations.RunPython(
            tag_career_resources,
            migrations.RunPython.noop,
        ),
    ]
