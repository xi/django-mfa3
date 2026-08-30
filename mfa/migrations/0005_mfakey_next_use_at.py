from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('mfa', '0004_alter_mfakey_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='mfakey',
            name='next_use_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
