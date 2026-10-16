from django.db import migrations


def add_food_assistance_tag(apps, schema_editor):
    CommunityResource = apps.get_model("referrals", "CommunityResource")
    resource = CommunityResource.objects.filter(
        name="Connecticut Foodshare"
    ).first()

    if resource is not None and "food_assistance" not in resource.subneeds:
        resource.subneeds = [*resource.subneeds, "food_assistance"]
        resource.save(update_fields=["subneeds"])


class Migration(migrations.Migration):

    dependencies = [
        ("referrals", "0006_refine_mental_health_resource_tags"),
    ]

    operations = [
        migrations.RunPython(
            add_food_assistance_tag,
            migrations.RunPython.noop,
        ),
    ]
