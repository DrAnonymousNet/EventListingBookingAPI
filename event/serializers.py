from dataclasses import field
from statistics import mode
from rest_framework import serializers
from .models import Event

class EventReadSerializer(serializers.ModelSerializer):
    direction_for_user = serializers
    class meta:
        model=Event
        field=[
            "event_url",
            "event_uuid",
            "event_name",
            "event_description",
            "event_image",
            "event_published_date",
            "event_publish_end_date",
            "event_date",
            "event_time",
            "event_type",
            "event_attendees",
            "event_address",
            "event_location_latitude",
            "event_location_lognitude",
            "event_max_participant_num",
            "event_status",
        ]
    