from datetime import datetime, timedelta
from typing import Tuple
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import APIException

# Create your models here.

User = get_user_model()


class EventPaymentType(models.TextChoices):
    """Choices of to choose if the event
    is to be paid for or for free"""

    FREE = "free", _("Free")
    PAID = "paid", _("Paid")


class EventLocationType(models.TextChoices):

    VIRTUAL = "virtual", _("Virtual")
    ONSITE = "onsite", _("Onsite")


class EventStatus(models.TextChoices):
    """choices for cancle events"""

    DRAFT = "draft", _("Draft")
    OPEN = "open", _("Open")
    CANCELD = "cancled", _("Cancled")
    CLOSED = "closed", _("Closed")


class Event(models.Model):

    # General Data
    event_uuid = models.UUIDField(default=uuid4())
    event_owner = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    event_name = models.CharField(
        _("Event Name"), max_length=40, blank=False, null=False
    )
    event_description = models.TextField(_("Event Description"), blank=True, null=True)
    event_image = models.ImageField()
    event_published_date = models.DateTimeField(blank=True, null=True)
    event_publish_end_date = models.DateTimeField(blank=True, null=True)
    event_start_date = models.DateField(blank=True, null=True)
    event_start_time = models.TimeField(blank=True, null=True)
    event_end_date = models.DateField(blank=True, null=True)
    event_end_time = models.TimeField(null=True, blank=True)
    event_payment_type = models.CharField(
        choices=EventPaymentType.choices, default=EventPaymentType.FREE, max_length=20
    )
    event_attendees = ArrayField(
        base_field=models.EmailField(
            _("Event Attendees"), max_length=50, blank=True, null=True
        ),
        default=list,
    )

    event_location_type = models.CharField(
        choices=EventLocationType.choices,
        default=EventLocationType.ONSITE,
        max_length=20,
    )

    # ONSITE DATA
    event_address = models.CharField(
        _("Address of Event Location"), max_length=160, blank=True
    )
    event_location_latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    event_location_lognitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )

    # VIRTUAL DATA
    event_url_link = models.URLField(blank=True)

    event_max_participant_num = models.PositiveBigIntegerField(
        _("Maximum Participant"), blank=True, null=True
    )
    event_status = models.CharField(
        max_length=20, choices=EventStatus.choices, default=EventStatus.DRAFT
    )

    class Meta:
        # constriant = [
        #    models.CheckConstraint(check=models.F("event_publish_date") <= models.F("event_publish_end_date"), name="Publish_date_less_than_end_date"),
        #    models.CheckConstraint(check=models.F("event_date") >= models.F("evnent_publish_date__date"))
        # ]
        pass

    def __str__(self) -> str:
        return f"Event-{self.event_uuid}"

    def save(self, *args, **kwargs) -> None:
        if not self.event_published_date or not self.event_publish_end_date:
            self.event_status = EventStatus.DRAFT

        return super().save(*args, **kwargs)

    def reserve_space(self, email):
        if self.event_max_participant_num:
            if len(self.event_attendees) < self.event_max_participant_num:
                self.event_attendees.append(email)
        self.save()

    def publish_event(self):

        if self.event_status != EventStatus.OPEN:

            if not self.event_publish_end_date:
                raise APIException(
                    {"error": "Set event publish end date before publishing"},
                    status=400,
                )
            self.event_status = EventStatus.OPEN
            self.event_published_date = timezone.now()

        else:
            self.event_status = EventStatus.OPEN
        self.save()

    def cancel_event(self):
        self.event_status = EventStatus.CANCELD
        self.save()

    def close_event(self):
        self.event_status = EventStatus.CLOSED
        self.save()

    def open_event(self):
        self.event_status = EventStatus.OPEN
        self.save()

    def get_absolute_url(self):
        return reverse("event-detail", args=[str(self.event_uuid)])

    def get_event_location(self) -> Tuple:
        if self.event_location_type == EventLocationType.ONSITE:
            destination_lat_n_lng = (
                self.event_location_latitude,
                self.event_location_lognitude,
            )
            if all(destination_lat_n_lng):
                return destination_lat_n_lng
            else:
                return (self.event_address, "")
        else:
            return self.event_url_link


class OuthTokenModel(models.Model):
    token_provider = models.CharField(max_length=250, blank=True, null=True)
    access_token = models.CharField(max_length=250, blank=True)
    refresh_token = models.CharField(max_length=200, blank=True, null=True)
    token_expire_time = models.DateTimeField()
    expires_in = models.IntegerField()
    token_owner = models.CharField(max_length=250, blank=True, null=True)
    scope = models.CharField(max_length=250, blank=True, null=True)
    token_type = models.CharField(max_length=250, blank=True, null=True)

    def is_expired(self):
        return self.token_expire_time < datetime.now()

    def save(self, *args, **kwargs):
        if self._state.adding:
            self.token_expire_time = datetime.now() + timedelta(self.expires_in)
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"Token {self.access_token}"
