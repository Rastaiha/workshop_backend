# Generated by Django 4.1.3 on 2024-01-02 10:57

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0003_alter_paper_creation_date_alter_paper_update_date_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='paper',
            name='creator',
        ),
        migrations.RemoveField(
            model_name='paper',
            name='criteria',
        ),
        migrations.RemoveField(
            model_name='paper',
            name='polymorphic_ctype',
        ),
        migrations.RemoveField(
            model_name='widget',
            name='creator',
        ),
        migrations.RemoveField(
            model_name='widget',
            name='polymorphic_ctype',
        ),
        migrations.DeleteModel(
            name='Hint',
        ),
        migrations.DeleteModel(
            name='Paper',
        ),
        migrations.DeleteModel(
            name='Widget',
        ),
    ]
