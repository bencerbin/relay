from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("referrals", "0009_use_collaborative_member_descriptions"),
    ]

    operations = [
        migrations.AddField(
            model_name="referralsession",
            name="pending_clarification",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
