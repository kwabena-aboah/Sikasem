from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('companies', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='companysettings',
            name='paystack_secret_key',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='companysettings',
            name='paystack_public_key',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='companysettings',
            name='paystack_base_url',
            field=models.URLField(default='https://api.paystack.co'),
        ),
    ]
