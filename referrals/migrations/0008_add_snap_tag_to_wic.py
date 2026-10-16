from django.db import migrations


def add_snap_tag_to_wic(apps, schema_editor):
    CommunityResource = apps.get_model("referrals", "CommunityResource")
    resource = CommunityResource.objects.filter(
        name="Women Infant Child Program"
    ).first()

    if resource is not None and "snap_benefits" not in resource.subneeds:
        resource.subneeds = [*resource.subneeds, "snap_benefits"]
        resource.save(update_fields=["subneeds"])


class Migration(migrations.Migration):

    dependencies = [
        ("referrals", "0007_add_food_assistance_tag"),
    ]

    operations = [
        migrations.RunPython(
            add_snap_tag_to_wic,
            migrations.RunPython.noop,
        ),
    ]
