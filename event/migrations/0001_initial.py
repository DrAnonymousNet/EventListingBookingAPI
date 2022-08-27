# Generated by Django 4.1 on 2022-08-15 09:28

from django.conf import settings
import django.contrib.postgres.fields
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event_uuid', models.UUIDField(default=uuid.UUID('56123934-af4c-44e7-a2c5-571731dbe004'))),
                ('event_name', models.CharField(max_length=40, verbose_name='Event Name')),
                ('event_description', models.TextField(blank=True, null=True, verbose_name='Event Description')),
                ('event_image', models.ImageField(upload_to='')),
                ('event_publsihed_date', models.DateTimeField()),
                ('event_publish_end_date', models.DateTimeField()),
                ('event_date', models.DateField()),
                ('event_time', models.TimeField()),
                ('event_payment_type', models.CharField(choices=[('free', 'Free'), ('paid', 'Paid')], default='free', max_length=20)),
                ('event_attendees', django.contrib.postgres.fields.ArrayField(base_field=models.EmailField(max_length=254, verbose_name='Event Attendees'), size=None)),
                ('event_location_type', models.CharField(choices=[('virtual', 'Viertual'), ('onsite', 'Onsite')], default='onsite', max_length=20)),
                ('event_address', models.CharField(max_length=160, verbose_name='Address of Event Location')),
                ('event_location_latitude', models.FloatField()),
                ('event_location_lognitude', models.FloatField()),
                ('event_url_link', models.URLField()),
                ('event_max_participant_num', models.PositiveBigIntegerField(verbose_name='Maximum Participant')),
                ('event_status', models.CharField(choices=[('draft', 'Draft'), ('open', 'Open'), ('cancled', 'Cancled'), ('closed', 'Closed')], default='draft', max_length=20)),
                ('event_owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
