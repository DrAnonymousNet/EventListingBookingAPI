from allauth.utils import import_attribute
from django.urls import include, path

from provider.adapters.google_adapter import (
    google_oauth2_callback_view,
    google_oauth2_grant_view,
)

urlpatterns = [
    path("grant/google/", google_oauth2_grant_view, name="google_grant"),
    path("grant/google/callback/", google_oauth2_callback_view, name="google_callback"),
]
