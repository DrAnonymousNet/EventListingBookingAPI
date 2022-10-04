import requests
from allauth.socialaccount import app_settings
from allauth.socialaccount.providers.linkedin_oauth2.provider import (
    LinkedInOAuth2Provider,
)
from django.urls import reverse
from rest_framework.response import Response

from .adapter import OAuth2APIAdapter, OAuth2CallbackView, OAuth2GrantView


class LinkedInOAuth2Adapter(OAuth2APIAdapter):
    provider_id = LinkedInOAuth2Provider.id
    access_token_url = "https://www.linkedin.com/oauth/v2/accessToken"
    authorize_url = "https://www.linkedin.com/oauth/v2/authorization"
    base_public_profile = "https://api.linkedin.com/v2/people/"
    profile_url = "https://api.linkedin.com/v2/me"

    # host: api.linkedin.com
    # basePath: /v2
    # scheme: https
    # noqa
    # See:
    # http://developer.linkedin.com/forum/unauthorized-invalid-or-expired-token-immediately-after-receiving-oauth2-token?page=1 # noqa
    access_token_method = "GET"

    def complete_profile_retrieve(self, request, app, token, **kwargs):
        # __import__("ipdb").set_trace()
        info = self.get_user_info(token)

        state = self.get_decoded_state(request)
        # vanity_name = state.get("vanity_name")
        headers = {
            "X-RestLiProtocol-Version": "2.0.0",
            "Authorization": f"Bearer {token.token}",
        }
        id = info.get("id")
        full_profile_url = (
            f"{self.base_public_profile}{id}"  # ?vanity_name={vanity_name}"
        )
        response = requests.get(
            full_profile_url, headers=headers
        )  # Requires Ads Permission
        return Response(data=info, status=200)

    def get_callback_url(self, request, app):
        return request.build_absolute_uri(reverse("linkedin_callback"))

    def get_user_info(self, token):
        # __import__("ipdb").set_trace()
        fields = self.get_provider().get_profile_fields()

        headers = {}
        headers.update(self.get_provider().get_settings().get("HEADERS", {}))
        headers["Authorization"] = " ".join(["Bearer", token.token])

        info = {}
        if app_settings.QUERY_EMAIL:
            resp = requests.get(self.email_url, headers=headers)
            # If this response goes wrong, that is not a blocker in order to
            # continue.
            if resp.ok:
                info = resp.json()

        url = self.profile_url + "?projection=(%s)" % ",".join(fields)
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        info.update(resp.json())
        return info


linkedin_oauth2_grant_view = OAuth2GrantView.adapter_view(LinkedInOAuth2Adapter)
linkedin_oauth2_callback_view = OAuth2CallbackView.adapter_view(LinkedInOAuth2Adapter)
