import base64

import requests
from allauth.socialaccount.providers.google.provider import GoogleProvider
from django.conf import settings
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from rest_framework.response import Response

from event.googleapi.calendar import event_create_schema

from .adapter import OAuth2Adapter, OAuth2CallbackView, OAuth2GrantView


class GoogleOAuth2Adapter(OAuth2Adapter):
    provider_id = GoogleProvider.id
    access_token_url = "https://accounts.google.com/o/oauth2/token"
    authorize_url = "https://accounts.google.com/o/oauth2/auth"
    # profile_url = "https://www.googleapis.com/oauth2/v1/userinfo"

    def complete_event_insert(self, request, app, token, **kwargs):
        # __import__("ipdb").set_trace()
        scope = request.query_params.get("scope")
        state = self.get_decoded_state(request)
        email = state.get("email")
        event_uuid = state.get("event_uuid")

        creds = Credentials(
            token=token.token,
            refresh_token=token.token_secret,
            client_id=settings.CLIENT_ID,
            client_secret=settings.CLIENT_SECRET,
            token_uri=settings.TOKEN_ENDPOINT,
            scopes=scope,
        )
        service = build("calendar", "v3", credentials=creds)
        event = event_create_schema(event_uuid)
        # __import__("ipdb").set_trace()
        event = service.events().insert(calendarId=email, body=event).execute()
        print("Event created: %s" % event)

        return Response(
            data={"message": "Event Added to Calendar", "event_data": event}, status=200
        )


google_oauth2_grant_view = OAuth2GrantView.adapter_view(GoogleOAuth2Adapter)
google_oauth2_callback_view = OAuth2CallbackView.adapter_view(GoogleOAuth2Adapter)
