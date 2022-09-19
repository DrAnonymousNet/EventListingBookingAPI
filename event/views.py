from django.http import Http404
from rest_framework import permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

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
            return Response(data=error, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(methods=["post", "get"], detail=True)
    def publish_event(self, request, event_uuid=None):
        event = self.get_object()
        event.publish_event()
        response = Response(
            {"message": "Event has been published successfully"},
            status=status.HTTP_200_OK,
        )
        response["location"] = event.get_absolute_url()
        return response

    @action(methods=["post"], detail=True)
    def cancel_event(self, request, event_uuid=None):
        event = self.get_object()
        event.cancel_event()
        # TODO send Email to all those that have registered
        return Response(
            {"message": "Event has been Cancled successfully"},
            status=status.HTTP_200_OK,
        )

    @action(methods=["post"], detail=True)
    def open_event(self, request):
        event = self.get_object()
        event.open_event()

        # TODO send Email

    @action(methods=["post"], detail=True)
    def direction(self, request, **kwargs):
        # __import__("ipdb").set_trace()
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

    def get_object(self, *args, **kwargs):
        print(self.kwargs, "OD4OFKFFFKNRK4")
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
