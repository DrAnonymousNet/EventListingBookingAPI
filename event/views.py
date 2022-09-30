import base64
import json
from urllib.parse import unquote, urlencode

import requests
from allauth.socialaccount.providers.oauth2.client import OAuth2Error
from allauth.socialaccount.providers.oauth2.views import OAuth2View
from django.conf import settings
from django.http import Http404
from django.shortcuts import redirect
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from rest_framework import permissions, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ViewSet

from event.googleapi.calendar import event_create_schema
from event.models import (
    Event,
    EventLocationType,
    EventPaymentType,
    EventStatus,
    OuthTokenModel,
)
from event.permissions import IsOwnerorReadonly
from event.serializers import (
    EventBookingSerializer,
    EventCreateSerializer,
    EventReadSerializer,
    OnSiteEventDirectionSerializer,
)
from Event.settings import CLIENT_ID, CLIENT_SECRET


class EventAPIViewSet(ModelViewSet):
    serializer_class = EventReadSerializer
    queryset = Event.objects.all()
    filterset_fields = ["event_status", "event_payment_type"]

    lookup_field = "event_uuid"

    def list(self, request, *args, **kwargs):
        # serializer_class = self.get_serializer_class(*args, **kwargs)
        queryset = self.filter_queryset(self.get_queryset())

        # __import__("ipdb").set_trace()
        serializer = EventReadSerializer(
            queryset, many=True, context={"request": self.request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        event_obj = self.get_object()

        serializer = EventReadSerializer(
            instance=event_obj, context={"request": self.request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=["post"], detail=True)
    def reserve(self, request, event_uuid):
        event_obj = self.get_object()
        # __import__("ipdb").set_trace()
        error = {}
        if (
            event_obj.event_payment_type == EventPaymentType.FREE
            and event_obj.event_status == EventStatus.OPEN
        ):

            serializer = self.get_serializer(instance=event_obj, data=self.request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            add_to_calendar = self.request.build_absolute_uri(
                reverse(
                    "event-add-to-calendar",
                    kwargs={"event_uuid": str(event_obj.event_uuid)},
                )
            )
            email = self.request.data.get("attendee_email")
            return Response(
                data={
                    "message": f"You have Booked for a sit successfully, if you want to add to Calender, click on the link below: {add_to_calendar}?{urlencode({'email':email})}"
                },
                status=status.HTTP_200_OK,
            )

        elif event_obj.event_status in [EventStatus.CANCELD, EventStatus.CLOSED]:
            error = {"error": "This Event is not accepting attendees anymore"}
        elif event_obj.event_status == EventStatus.DRAFT:
            error = {"error": "This Event is still in draft mode"}
        return Response(data=error, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=["get"], detail=True)
    def publish_event(self, request, event_uuid=None):
        event = self.get_object()
        event.publish_event()
        serializer = self.get_serializer(instance=event)
        response = Response(
            {
                "message": "Event has been published successfully",
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )
        response["location"] = event.get_absolute_url()
        return response

    @action(methods=["get"], detail=True)
    def cancel_event(self, request, event_uuid=None):
        event = self.get_object()
        event.cancel_event()
        serializer = self.get_serializer(instance=event)
        # TODO send Email to all those that have registered
        return Response(
            {"message": "Event has been Cancled successfully", "data": serializer.data},
            status=status.HTTP_200_OK,
        )

    @action(methods=["get"], detail=True)
    def open_event(self, request, **kwargs):
        event = self.get_object()
        event.open_event()
        serializer = self.get_serializer(instance=event)
        # TODO send Email
        return Response(
            {"message": "Event has been opened successfully", "data": serializer.data},
            status=status.HTTP_200_OK,
        )

    @action(methods=["get"], detail=True)
    def close_event(self, request, **kwargs):
        # __import__("ipdb").set_trace()
        event = self.get_object()
        event.close_event()
        serializer = self.get_serializer(instance=event)
        # TODO send Email
        return Response(
            {"message": "Event has been closed successfully", "data": serializer.data},
            status=status.HTTP_200_OK,
        )

    @action(methods=["post"], detail=True)
    def direction(self, request, **kwargs):
        event = self.get_object()
        if event.event_location_type == EventLocationType.ONSITE:
            serializer = OnSiteEventDirectionSerializer(
                data=self.request.data, context={"event": event}
            )
            serializer.is_valid(raise_exception=True)
            return Response(data=serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(
                data={
                    "direction": f"Download Google Meet or Access it via Gmail and Join via {event.event_url_link}"
                }
            )

    @action(detail=True, methods=["get", "post"])
    def add_to_calendar(self, request, **kwargs):
        if self.request.method == "GET":
            email = unquote(self.request.query_params.get("email"))
            event_uuid = self.kwargs.get("event_uuid")
            event = Event.objects.get(event_uuid=event_uuid)

            if email not in event.event_attendees:
                return Response(
                    {"error": "You have not reserved a sit in this event"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            grant_end_point = f"{self.request.build_absolute_uri(reverse('google_grant'))}?{urlencode({'action':'event_insert','email':email, 'event_uuid':event_uuid})}"
            return redirect(grant_end_point)

        token = OuthTokenModel.objects.last()
        creds = Credentials(
            token=token.access_token,
            refresh_token=token.refresh_token,
            client_id=settings.CLIENT_ID,
            client_secret=settings.CLIENT_SECRET,
            token_uri=settings.TOKEN_ENDPOINT,
            scopes=token.scopes.split(" "),
            expiry=token.expires_in,
        )
        service = build("calendar", "v3", credentials=creds)
        event = event_create_schema(event_uuid)
        event = service.events().insert(calendarId="primary", body=event).execute()
        print("Event created: %s" % event)

        return Response(
            data={
                "message": "Event Added to Calendar",
                "event_data": json.dumps(event),
            },
            status=200,
        )

    def get_object(self):
        event_uuid = self.kwargs.get("event_uuid")
        try:
            obj = self.get_queryset().get(event_uuid=event_uuid)
        except Event.DoesNotExist:
            raise Http404
        return obj

    def get_serializer(self, *args, **kwargs):
        if self.action == "reserve":
            serializer = EventBookingSerializer
            kwargs.setdefault("context", self.get_serializer_context())
            return serializer(*args, **kwargs)
        elif self.action == "create":
            serializer = EventCreateSerializer
            kwargs.setdefault("context", self.get_serializer_context())
            return serializer(*args, **kwargs)
        elif self.action == "direction":
            serializer = OnSiteEventDirectionSerializer
            kwargs.setdefault("context", self.get_serializer_context())
            return serializer(*args, **kwargs)

        return super().get_serializer(*args, **kwargs)

    def get_serializer_context(self):

        event_uuid = self.kwargs.get("event_uuid")
        context = super().get_serializer_context()
        context.update({"event_uuid": event_uuid, "request": self.request})
        return context

    def get_permissions(self):
        if self.action in ["create", "retrieve", "update", "partial-update", "list"]:
            self.permission_classes = [IsOwnerorReadonly]
        else:
            self.permission_classes = [permissions.AllowAny]

        return super().get_permissions()


# from __future__ import absolute_import

# from datetime import timedelta
# from requests import RequestException

# from django.core.exceptions import PermissionDenied
# from django.http import HttpResponseRedirect
# from django.urls import reverse
# from django.utils import timezone

# from allauth.exceptions import ImmediateHttpResponse
# from allauth.socialaccount import providers
# from allauth.socialaccount.helpers import (
#     complete_social_login,
#     render_authentication_error,
# )
# from allauth.socialaccount.providers.base import ProviderException
# from allauth.socialaccount.providers.base.constants import (
#     AuthError,
# )
# from allauth.socialaccount.providers.oauth2.client import (
#     OAuth2Error,
# )
# from .models import Event
# from django.http import HttpResponseRedirect
# from django.urls import reverse
# from rest_framework.response import Response
# from allauth.account.adapter import get_adapter as get_account_adapter

# from allauth.exceptions import ImmediateHttpResponse

# from allauth.socialaccount.providers.base import AuthError
# from event.utils import render_authentication_error

# class OuthCallBackView(ViewSet, OAuth2View):
#     #SCOPES = [
#     #    "https://www.googleapis.com/auth/calendar.readonly",
#     #    "https://www.googleapis.com/auth/calendar.events",
#     #    "https://www.googleapis.com/auth/calendar",
#     #]
#     #CODE_URL = "https://accounts.google.com/o/oauth2/auth"
#     #TOKEN_URL = "https://oauth2.googleapis.com/token"
#     #client_id = settings.CLIENT_ID
#     #client_secret = settings.CLIENT_SECRET
#     #access_type = "offline"
#     #response_type = "code"
#     #code_redirect_uri = "http://localhost:8000/api/v1/code"
#     #token_redirect_uri = "http://localhost:8000/api/v1/token"
#     #logic_redirect_uri = "http://localhost:8000"
#     #grant_type = "authorization_code"

#     def dispatch(self, request, *args, **kwargs):
#         if "error" in request.GET or "code" not in request.GET:
#             # Distinguish cancel from error
#             auth_error = request.GET.get("error", None)
#             if auth_error == self.adapter.login_cancelled_error:
#                 error = AuthError.CANCELLED
#             else:
#                 error = AuthError.UNKNOWN
#             return render_authentication_error(
#                 request, self.adapter.provider_id, error=error
#             )
#         app = self.adapter.get_provider().get_app(self.request)
#         client = self.get_client(self.request, app)

#         try:
#             access_token = self.adapter.get_access_token_data(request, app, client)
#             token = self.adapter.parse_token(access_token)
#             token.app = app
#             action = getattr(self.adapter, action)()

#             #return handler(request)

#         except (
#             PermissionDenied,
#             OAuth2Error,
#             requests.RequestException,
#             ProviderException,
#         ) as e:
#             return render_authentication_error(
#                 request, self.adapter.provider_id, exception=e
#             )


#     @action(methods=["get"], detail=False)
#     def grant(self, request, **kwargs):
#         print(request.data, request.query_params)
#         # __import__("ipdb").set_trace()
#         return redirect(self.construct_grant_url())

#     @action(methods=["get"], detail=False)
#     def code(self, request, **kwargs):
#         print(request.query_params, request.data)
#         token_endpoint_params = self.construct_token_params()
#         full_url = f"{self.TOKEN_URL}"

#         headers = {
#             "Accept": "application/json",
#             "Content-Type": "application/json",  # "application/x-www-form-urlencoded;charset=UTF-8",
#         }
#         # __import__("ipdb").set_trace()
#         response = requests.post(full_url, data=token_endpoint_params, headers=headers)

#         self.request.data.update({"token": response.json()})
#         token_data = dict(response.json())
#         print(token_data)
#         email, event_uuid = self.get_state_params()
#         # __import__("ipdb").set_trace()

#         # email = unquote(email)
#         token = OuthTokenModel.objects.create(
#             token_provider="Google", token_owner=email, **token_data
#         )
#         creds = Credentials(
#             token=token.access_token,
#             refresh_token=token.refresh_token,
#             client_id=settings.CLIENT_ID,
#             client_secret=settings.CLIENT_SECRET,
#             token_uri=settings.TOKEN_ENDPOINT,
#             scopes=token.scope.split(" "),
#         )
#         service = build("calendar", "v3", credentials=creds)
#         event = event_create_schema(event_uuid)
#         # __import__("ipdb").set_trace()
#         event = service.events().insert(calendarId=email, body=event).execute()
#         print("Event created: %s" % event)

#         return Response(
#             data={"message": "Event Added to Calendar", "event_data": event}, status=200
#         )
#         # return Response(data=response.json() ,status=200)

#     @action(methods=["get"], detail=False)
#     def token(self, request, **kwargs):
#         return redirect(self.logic_redirect_uri)

#     def get_scope(self):
#         """Convert a list of scopes to a space separated string."""
#         if isinstance(self.SCOPES, str) or self.SCOPES is None:
#             return self.SCOPES
#         elif isinstance(self.SCOPES, (set, tuple, list)):
#             return " ".join([str(s) for s in self.SCOPES])
#         else:
#             raise ValueError(
#                 "Invalid scope (%s), must be string, tuple, set, or list." % self.scope
#      http://127.0.0.1:8000/accounts/google/login/?process=login       )

#     def construct_grant_url(self, **kwargs):
#         email = self.request.query_params.get("email")
#         event_uuid = self.request.query_params.get("event_uuid")
#         state = base64.b64encode(f"{email},{event_uuid}".encode("utf-8")).decode(
#             "utf-8"
#         )

#         params = {
#             "scope": self.get_scope(),
#             "client_id": self.client_id,
#             "response_type": self.response_type,
#             "access_type": self.access_type,
#             "state": state,
#         }

#         if self.code_redirect_uri:
#             params["redirect_uri"] = self.code_redirect_uri
#         encoded_url = urlencode(params)
#         full_url = f"{self.CODE_URL}?{encoded_url}"
#         return full_url

#         # https://accounts.google.com/o/oauth2/auth?response_type=code&client_id=<client_id>&redirect_uri=<redirect_uri>&scope=<scope_of_the_resource>&access_type=offline
#         # pass

#     def construct_token_params(self):
#         params = {
#             "code": self.request.query_params.get("code"),
#             "scope": self.request.query_params.get("scope"),
#             "client_id": self.client_id,
#             "client_secret": self.client_secret,
#             "grant_type": self.grant_type,
#         }
#         if self.token_redirect_uri:
#             params["redirect_uri"] = self.code_redirect_uri

#         encoded_params = json.dumps(params)  # urlencode(params)
#         # full_url = f"{self.CODE_URL}?{encoded_url}"

#         return encoded_params

#     def get_state_params(self, **kwargs):
#         state = self.request.query_params.get("state")
#         values = base64.urlsafe_b64decode(state).decode("utf-8").split(",")
#         return tuple(values)


# class Home_View(APIView):
#     def get(self, request, **kwargs):
#         endpoint = self.request.build_absolute_uri(reverse("api-root"))

#         return Response(data={"root-api": endpoint}, status=200)

# import allauth
