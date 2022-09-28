from datetime import datetime

from event.models import Event


def event_create_schema(event_uuid):
    event = Event.objects.get(event_uuid=event_uuid)

    event = {
        "summary": f"{event.event_name}",
        "location": f"{event.event_address}",
        "description": f"{event.event_description}",
        "start": {
            "dateTime": f"{build_date_time(event.event_date, event.event_time)}",
            "timeZone": "Africa/Lagos",
        },
        #'end': {
        #    'dateTime': '2015-05-28T17:00:00-07:00',
        #    'timeZone': 'America/Los_Angeles',
        # },
        #'recurrence': [
        #    'RRULE:FREQ=DAILY;COUNT=2'
        # ],
        "attendees": [{"email": email} for email in event.event_attendees],
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
