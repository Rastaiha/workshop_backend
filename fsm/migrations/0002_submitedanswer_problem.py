# Generated by Django 3.1 on 2020-08-29 21:43

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('fsm', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='submitedanswer',
            name='problem',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='submited_answers', to='fsm.problem'),
        ),
    ]
