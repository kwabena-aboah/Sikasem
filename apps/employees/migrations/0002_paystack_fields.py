from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('employees', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='employee',
            name='bank_code',
            field=models.CharField(blank=True, help_text='Paystack bank/institution code', max_length=20),
        ),
        migrations.AddField(
            model_name='employee',
            name='paystack_recipient_code',
            field=models.CharField(blank=True, help_text='Saved Paystack transfer recipient code', max_length=100),
        ),
    ]
