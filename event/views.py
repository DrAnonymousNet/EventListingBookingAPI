import json
from http import client
from urllib import request, response
from urllib.parse import urlencode

import requests
from django.conf import settings
from django.http import Http404
from django.shortcuts import redirect
from googleapiclient.discovery import build
from rest_framework import permissions, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ViewSet

from event.googleapi.calendar import event_create_schema
from event.models import Event, EventLocationType, EventPaymentType, EventStatus
from event.permissions import IsOwnerorReadonly
from event.serializers import (
    EventBookingSerializer,
    EventCreateSerializer,
    EventReadSerializer,
    OnSiteEventDirectionSerializer,
)


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
            return Response(
                data={"message": "You have Booked for a sit successfully"},
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


class OuthCallBackView(ViewSet):
    SCOPES = [
        "https://www.googleapis.com/auth/calendar.readonly",
        "https://www.googleapis.com/auth/calendar.events",
        "https://www.googleapis.com/auth/calendar",
    ]
    CODE_URL = "https://accounts.google.com/o/oauth2/auth"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    client_id = settings.CLIENT_ID
    client_secret = settings.CLIENT_SECRET
    access_type = "offline"
    response_type = "code"
    code_redirect_uri = "http://localhost:8000/api/v1/code"
    token_redirect_uri = "http://localhost:8000/api/v1/token"
    logic_redirect_uri = "http://localhost:8000"
    grant_type = "authorization_code"

    @action(methods=["get"], detail=False)
    def grant(self, request, **kwargs):
        return redirect(self.construct_grant_url())

    @action(methods=["get"], detail=False)
    def code(self, request, **kwargs):
        token_endpoint_params = self.construct_token_params()
        full_url = f"{self.TOKEN_URL}"

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",  # "application/x-www-form-urlencoded;charset=UTF-8",
        }
        # __import__("ipdb").set_trace()
        response = requests.post(full_url, data=token_endpoint_params, headers=headers)
        self.request.data.update({"token": response.json()})
        return redirect()

    @action(methods=["get"], detail=False)
    def token(self, request, **kwargs):
        return redirect(self.logic_redirect_uri)

    def get_scope(self):
        """Convert a list of scopes to a space separated string."""
        if isinstance(self.SCOPES, str) or self.SCOPES is None:
            return self.SCOPES
        elif isinstance(self.SCOPES, (set, tuple, list)):
            return " ".join([str(s) for s in self.SCOPES])
        else:
            raise ValueError(
                "Invalid scope (%s), must be string, tuple, set, or list." % self.scope
            )

    def construct_grant_url(self, **kwargs):
        params = {
            "scope": self.get_scope(),
            "client_id": self.client_id,
            "response_type": self.response_type,
            "access_type": self.access_type,
        }

        if self.code_redirect_uri:
            params["redirect_uri"] = self.code_redirect_uri
        encoded_url = urlencode(params)
        full_url = f"{self.CODE_URL}?{encoded_url}"
        return full_url

        # https://accounts.google.com/o/oauth2/auth?response_type=code&client_id=<client_id>&redirect_uri=<redirect_uri>&scope=<scope_of_the_resource>&access_type=offline
        # pass

    def construct_token_params(self):
        params = {
            "code": self.request.query_params.get("code"),
            "scope": self.request.query_params.get("scope"),
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": self.grant_type,
        }
        if self.token_redirect_uri:
            params["redirect_uri"] = self.code_redirect_uri

        encoded_params = json.dumps(params)  # urlencode(params)
        # full_url = f"{self.CODE_URL}?{encoded_url}"

        return encoded_params


class Home_View(APIView):
    def get(self, request, **kwargs):
        event_uuid = self.kwargs.get("event_uuid")

        service = build("calendar", "v3", credentials=creds)
        event = event_create_schema(event_uuid)
        event = service.events().insert(calendarId="primary", body=event).execute()
        print("Event created: %s" % (event.get("htmlLink")))

        return Response({"data": request.data, "query_params": request.query_params})
