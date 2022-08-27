from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import EventAPIViewSet

router = DefaultRouter()

router.register(basename="event",viewset=EventAPIViewSet, prefix="events")

urlpatterns = []
urlpatterns += router.urls