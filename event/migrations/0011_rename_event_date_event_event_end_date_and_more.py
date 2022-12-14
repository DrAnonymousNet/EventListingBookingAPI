# Generated by Django 4.1 on 2022-09-28 13:41

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('event', '0010_alter_event_event_uuid_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='event',
            old_name='event_date',
            new_name='event_end_date',
        ),
        migrations.RenameField(
            model_name='event',
            old_name='event_time',
            new_name='event_end_time',
        ),
        migrations.AddField(
            model_name='event',
            name='event_start_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='event',
            name='event_start_time',
            field=models.TimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='event',
            name='event_uuid',
            field=models.UUIDField(default=uuid.UUID('ec31cba8-4adf-412d-9a7c-fa7db81880ee')),
        ),
    ]
