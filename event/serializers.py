from dataclasses import dataclass, field
from os import stat
from statistics import mode
from rest_framework import serializers
from rest_framework.exceptions import APIException
from rest_framework import status
from .models import Event, EventStatus, EventLocationType, EventPaymentType
from django.db.models import QuerySet
from rest_framework.fields import empty

@dataclass
class EventReadSerializer(serializers.ModelSerializer):

    event_url = serializers.SerializerMethodField() #URLField(source="get_absolute_url", read_only = True)

    
    def __init__(self, instance=None, data=empty, **kwargs):
        super().__init__(instance,data, **kwargs)
        
        if isinstance(instance, QuerySet) or [instance]:
            if not isinstance(instance, QuerySet):
                instance_list = [instance]
            for instance_obj in  instance if isinstance(instance, QuerySet) else instance_list:
                if instance_obj.event_location_type == EventLocationType.ONSITE:
                    self.on_site_fields = ["event_location_lognitude","event_location_latitude",
                                        "event_address"]
                    self.Meta.fields += self.on_site_fields
                        

                    self.fields["user_location"] = serializers.CharField(read_only=True)
                    self.fields["event_address"] = serializers.CharField()
                    self.fields["event_location_latitude"] = serializers.FloatField()
                    self.fields["event_location_lognitude"] = serializers.FloatField()

                   

                elif instance_obj.event_location_type == EventLocationType.VIRTUAL:
                    self.virtual_field = ["event_url_link"]
                    self.Meta.fields += self.virtual_field      
                    self.fields["event_url_link"] = serializers.CharField()
    


    

    
    
    class Meta:
        model=Event
        fields=[
            "event_url",
            "event_uuid",
            "event_name",
            "event_description",
            "event_image",
            "event_published_date",
            "event_publish_end_date",
            "event_date",
            "event_time",
            "event_payment_type",
            "event_attendees",
            "event_max_participant_num",
            "event_status",
            "event_location_type"
        ]

        read_only_fields = ["event_uuid", "event_attendees"]

    def get_event_url(self, event):
        request = self.context.get("request")
        return request.build_absolute_uri(event.get_absolute_url())

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.event_location_type == EventLocationType.ONSITE:
            data.pop(self.virtual_field[0])
        elif instance.event_location_type == EventLocationType.VIRTUAL:
            for field in self.on_site_fields:
                data.pop(field)
        
        #TODO GetLocation
        return data

    def to_internal_value(self, data):
        return super().to_internal_value(data)
        

class EventCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model=Event
        fields = "__all__"
        read_only_fields = ["event_uuid", "event_attendees"]
    
        on_site_fields = ["event_location_lognitude",
                        "event_location_latitude",
                        "event_address"]
        virtual_fields= ["event_url_link"]

    def validate(self, attrs):
        if attrs.get("event_location_type") == EventLocationType.ONSITE:
            if any([attrs.get(field) for field in self.Meta.virtual_fields]):
                raise serializers.ValidationError({"error":"On site Events cannot have event_url_link"})
        
        elif attrs.get("event_location_type") == EventLocationType.VIRTUAL:
            if any([attrs.get(field) for field in self.Meta.on_site_fields]):
                raise serializers.ValidationError({"error":"Virtual Events cannot have location related fields"}, status=status.HTTP_400_BAD_REQUEST)

        publish_start_date = attrs.get("event_published_date")
        publish_end_date = attrs.get("event_publish_end_date")
        if publish_start_date < publish_end_date:
            raise serializers.ValidationError({"error":"Publish startdate cannot be less than publish end date"},status=status.HTTP_400_BAD_REQUEST)
        
        if attrs.get("event_status_type") == EventStatus.OPEN and not (publish_end_date and publish_start_date):
            raise serializers.ValidationError({"error":"You cannot set event status to OPEN without publish end date and publish start_date"}, status=status.HTTP_400_BAD_REQUEST)
    
        return super().validate(attrs)




    
class EventBookingSerializer(serializers.Serializer):
    attendee_email = serializers.EmailField()

    def save(self, **kwargs):
        event_uuid = self.context.get("event_uuid")
        event_obj = Event.objects.get(event_uuid=event_uuid)
        if event_obj.event_status not in [EventStatus.CLOSED, EventStatus.CANCELD]:
            email = self.validated_data.get("attendee_email")
            event_obj.reserve_space(email=email)

            #TODO send Email
            return event_obj

        else:
            raise APIException({"error":"Event is closed"}, status=status.HTTP_400_BAD_REQUEST)

