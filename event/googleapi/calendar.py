from datetime import datetime, timedelta

from google.oauth2.credentials import Credentials

from event.models import Event


def event_create_schema(event_uuid):
    event = Event.objects.get(event_uuid=event_uuid)

    event = {
        "summary": f"{event.event_name}",
        "location": f"{event.event_address}",
        "description": f"{event.event_description}",
        "start": {
            "dateTime": f"{build_date_time(event.event_start_date, event.event_start_time)}",
            "timeZone": "Africa/Lagos",
        },
        "end": {
            "dateTime": f"{build_date_time(event.event_start_date, event.event_end_time)}",
            "timeZone": "Africa/Lagos",
        },
        "conferenceData": {
            "createRequest": {
                "requestId": "sample123",
                "conferenceSolutionKey": {"type": "hangoutsMeet"},
            }
        },
        #'recurrence': [
        #    'RRULE:FREQ=DAILY;COUNT=2'
        # ],
        # "creator":{"email":event.event_owner.email},
        # "organizer":{"email":event.event_owner.email},
        # "attendees": [{"email": email, "organizer":True if str(email) == event.event_owner else False,
        #               "self":True if str(email) == event.event_owner else False
        #                } for email in event.event_attendees],
        "reminders": {
            "useDefault": False,
            "overrides": [
                {"method": "email", "minutes": 24 * 60},
                {"method": "popup", "minutes": 10},
            ],
        },
    }
    return event


def build_date_time(date, time):
    date_time = datetime(
        year=date.year,
        day=date.day,
        month=date.month,
        hour=time.hour,
        minute=time.minute,
    )
    return date_time.isoformat()


def get_credetials():
    pass
