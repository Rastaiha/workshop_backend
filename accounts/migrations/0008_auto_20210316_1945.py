# Generated by Django 3.0.8 on 2021-03-16 16:15

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0007_discountcode'),
    ]

    operations = [
        migrations.AlterField(
            model_name='discountcode',
            name='participant',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='discount_code', to='accounts.Participant'),
        ),
    ]
