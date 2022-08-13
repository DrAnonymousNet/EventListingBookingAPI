import imp
from uuid import uuid4
from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _

# Create your models here.

User = get_user_model()

class EventType(models.TextChoices):
    '''Choices of to choose if the event 
        is to be paid for or for free'''

    FREE = "free", _("Free")
    PAID = "paid", _("Paid")

class EventStatus(models.TextChoices):
    '''choices for cancle events'''

    OPEN = "open", _("Open")
    CANCLED = "cancled", _("Cancled")




class Event(models.Model):

    event_uuid = models.UUIDField(default=uuid4())
    event_owner = models.ForeignKey(User, on_delete=models.CASCADE)
    event_name = models.CharField(_("Event Name"), max_length=40, blank=False, null= False)
    event_description = models.TextField(_("Event Description"), blank=True, null=True)
    event_image = models.ImageField()
    event_publsihed_date = models.DateTimeField(auto_now_add=True)
    event_publish_end_date = models.DateTimeField()
    event_date = models.DateField()
    event_time = models.TimeField()
    event_type = models.CharField(choices=EventType.choices, default=EventType.FREE)
    event_attendees = models.JSONField(_("Event Attendees"))
    event_address = models.CharField(_("Address of Eevnt Location"), max_length=160)
    event_location_latitude = models.FloatField()
    event_location_lognitude = models.FloatField()
    event_max_participant_num = models.PositiveBigIntegerField(_("Maximum Participant"))
    event_status = models.CharField(max_length=20, choices=EventStatus.choices, default=EventStatus.OPEN)


    def __str__(self) -> str:
        return f"Event-{self.event_uuid}"

    

