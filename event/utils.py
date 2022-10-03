from allauth.account import app_settings as account_settings
from allauth.account.adapter import get_adapter as get_account_adapter
from allauth.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import get_adapter
from allauth.socialaccount.providers.base import AuthError
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from rest_framework.response import Response

from .models import Event


class EventController:
    def __init__(self, event_obj: Event) -> None:
        pass


def render_authentication_error(
    request,
    provider_id,
    error=AuthError.UNKNOWN,
    exception=None,
    extra_context=None,
):
    try:
        if extra_context is None:
            extra_context = {}
        get_adapter(request).authentication_error(
            request,
            provider_id,
            error=error,
            exception=exception,
            extra_context=extra_context,
        )
    except ImmediateHttpResponse as e:
        return e.response
    if error == AuthError.CANCELLED:
        return Response(data={"detail": "Cancled"})
    context = {
        "auth_error": {
            "provider": provider_id,
            "code": error,
            "exception": exception,
        }
    }
    context.update(extra_context)
    return Response(data=context, status=400)
