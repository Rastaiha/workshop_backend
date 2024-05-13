# Generated by Django 4.1.3 on 2024-05-13 13:57

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('fsm', '0119_alter_playerstatehistory_end_time_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='PlayerTransitionHistory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('time', models.DateTimeField(auto_now=True)),
                ('is_edge_transited_in_reverse', models.BooleanField(blank=True, null=True)),
                ('source_state', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='source_of_player_transitions', to='fsm.state')),
                ('target_state', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='target_of_player_transitions', to='fsm.state')),
                ('transited_edge', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='player_transition_histories', to='fsm.edge')),
            ],
        ),
    ]
