from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import EventAPIViewSet, OuthCallBackView

router = DefaultRouter()

router.register(basename="event", viewset=EventAPIViewSet, prefix="events")
router.register(basename="oauth", viewset=OuthCallBackView, prefix="")
urlpatterns = []
urlpatterns += router.urls
