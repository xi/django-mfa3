from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("mfa", "0003_alter_mfakey_method"),
    ]

    operations = [
        migrations.AlterField(
            model_name="mfakey",
            name="id",
            field=models.BigAutoField(
                primary_key=True, serialize=False, verbose_name="ID"
            ),
        ),
    ]
