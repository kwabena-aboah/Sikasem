from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('payroll', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='paymentrecord',
            name='recipient_code',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='paymentrecord',
            name='transfer_reference',
            field=models.CharField(blank=True, max_length=50, null=True, unique=True),
        ),
    ]
