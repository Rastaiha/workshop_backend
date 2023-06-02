# Generated by Django 4.1.7 on 2023-06-02 23:29

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('scoring', '0009_rename_answer_comment_deliverable_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('fsm', '0066_delete_submittedanswer'),
        ('question', '0003_remove_inviteeusernameresponse_question_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Answer',
            fields=[
                ('deliverable_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='scoring.deliverable')),
                ('answer_type', models.CharField(choices=[('SmallAnswer', 'Smallanswer'), ('BigAnswer', 'Biganswer'), ('MultiChoiceAnswer', 'Multichoiceanswer'), ('UploadFileAnswer', 'Uploadfileanswer')], max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('is_final_answer', models.BooleanField(default=False)),
                ('is_correct', models.BooleanField(default=False)),
                ('answer_sheet', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='new_answers', to='fsm.answersheet')),
                ('submitted_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='new_submitted_answers', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
                'base_manager_name': 'objects',
            },
            bases=('scoring.deliverable',),
        ),
        migrations.CreateModel(
            name='Choice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='Question',
            fields=[
                ('widget_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='fsm.widget')),
                ('text', models.TextField()),
                ('is_required', models.BooleanField(default=False)),
                ('solution', models.TextField(blank=True, null=True)),
                ('score', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='scoring.score')),
            ],
            options={
                'abstract': False,
                'base_manager_name': 'objects',
            },
            bases=('fsm.widget',),
        ),
        migrations.CreateModel(
            name='InviteeUsernameQuestion',
            fields=[
                ('question_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='question.question')),
            ],
            options={
                'abstract': False,
                'base_manager_name': 'objects',
            },
            bases=('question.question',),
        ),
        migrations.CreateModel(
            name='LongAnswerQuestion',
            fields=[
                ('question_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='question.question')),
            ],
            options={
                'abstract': False,
                'base_manager_name': 'objects',
            },
            bases=('question.question',),
        ),
        migrations.CreateModel(
            name='MultiChoiceQuestion',
            fields=[
                ('question_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='question.question')),
                ('max_choices', models.IntegerField(default=1, validators=[django.core.validators.MinValueValidator(0)])),
            ],
            options={
                'abstract': False,
                'base_manager_name': 'objects',
            },
            bases=('question.question',),
        ),
        migrations.CreateModel(
            name='ShortAnswerQuestion',
            fields=[
                ('question_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='question.question')),
            ],
            options={
                'abstract': False,
                'base_manager_name': 'objects',
            },
            bases=('question.question',),
        ),
        migrations.CreateModel(
            name='UploadFileQuestion',
            fields=[
                ('question_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='question.question')),
            ],
            options={
                'abstract': False,
                'base_manager_name': 'objects',
            },
            bases=('question.question',),
        ),
        migrations.CreateModel(
            name='ChoiceSelection',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('choice', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='selections', to='question.choice')),
            ],
        ),
        migrations.CreateModel(
            name='UploadFileAnswer',
            fields=[
                ('answer_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='question.answer')),
                ('answer_file', models.FileField(max_length=4000, upload_to='answers')),
                ('problem', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='answers', to='question.uploadfilequestion')),
            ],
            options={
                'abstract': False,
                'base_manager_name': 'objects',
            },
            bases=('question.answer',),
        ),
        migrations.CreateModel(
            name='ShortAnswer',
            fields=[
                ('answer_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='question.answer')),
                ('text', models.TextField()),
                ('problem', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='answers', to='question.shortanswerquestion')),
            ],
            options={
                'abstract': False,
                'base_manager_name': 'objects',
            },
            bases=('question.answer',),
        ),
        migrations.CreateModel(
            name='MultiChoiceAnswer',
            fields=[
                ('answer_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='question.answer')),
                ('choices', models.ManyToManyField(through='question.ChoiceSelection', to='question.choice')),
                ('problem', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='answers', to='question.multichoicequestion')),
            ],
            options={
                'abstract': False,
                'base_manager_name': 'objects',
            },
            bases=('question.answer',),
        ),
        migrations.CreateModel(
            name='LongAnswer',
            fields=[
                ('answer_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='question.answer')),
                ('text', models.TextField()),
                ('problem', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='answers', to='question.longanswerquestion')),
            ],
            options={
                'abstract': False,
                'base_manager_name': 'objects',
            },
            bases=('question.answer',),
        ),
        migrations.CreateModel(
            name='InviteeUsernameAnswer',
            fields=[
                ('answer_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='question.answer')),
                ('username', models.CharField(max_length=15)),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='answers', to='question.inviteeusernamequestion')),
            ],
            options={
                'abstract': False,
                'base_manager_name': 'objects',
            },
            bases=('question.answer',),
        ),
        migrations.AddField(
            model_name='choiceselection',
            name='multi_choice_answer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='question.multichoiceanswer'),
        ),
        migrations.AddField(
            model_name='choice',
            name='problem',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='choices', to='question.multichoicequestion'),
        ),
    ]
