import jwt
from allauth.socialaccount.providers.base import ProviderException
from allauth.socialaccount.providers.base.constants import AuthAction
from allauth.socialaccount.providers.oauth2.client import OAuth2Error
from allauth.socialaccount.providers.oauth2.views import OAuth2Adapter, OAuth2View
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from httplib2 import Response
from requests import RequestException
from rest_framework import status
from rest_framework.renderers import JSONRenderer

from event.utils import render_authentication_error
from provider.mixin import OAuthGrantMixin


class OAuth2APIView(OAuthGrantMixin, OAuth2View):
    """Added the GrantMIXIN"""

    pass


class OAuth2APIAdapter(OAuth2Adapter):
    def complete_action(self, request, app, access_token, **kwargs):
        state = self.get_decoded_state(request)
        action = state.get("action")
        if not action:
            return Response({"detail": "No Action was specified in the decoded state"})

        # The provider must implement a `complete_{action name}` method
        action = getattr(self, f"complete_{action}", None)
        if action is None:
            raise NotImplementedError
        return action(request, app, access_token, **kwargs)

    def get_encoded_state(self, request):
        """Encode all query parameters that are
        sent with the oauth_grant endpoint
        """
        encoded_state = jwt.encode(request.query_params, "secretkey", algorithm="HS256")
        return encoded_state

    def get_decoded_state(self, request):
        """
        Retrieve all the data that are encoded in the state query parameter
        """
        encoded_state = request.query_params.get("state")
        deccoded_state = jwt.decode(encoded_state, "secretkey", algorithms=["HS256"])
        return deccoded_state


class OAuth2CallbackView(OAuth2APIView):
    """
    The base class for all redirect_uri

    The View uses the `code` retrieved from authorization grant and exchange it
    for the access and refresh token from the provider authorization server.

    It further uses the access and refresh token to perform the `action`
    on the provider resource server
    """

    def dispatch(self, request, *args, **kwargs):
        """
        DRF dispatch method rather than the Django dispatch method
        """
        self.args = args
        self.kwargs = kwargs
        request = self.initialize_request(request, *args, **kwargs)
        self.request = request
        self.headers = self.default_response_headers

        try:
            self.initial(request, *args, **kwargs)
        except Exception as exc:
            return self.handle_exception(exc)

        # Handle the error in the query parameter or the
        if "error" in request.query_params or "code" not in request.query_params:
            auth_error = request.query_params.get("error", None)
            if auth_error:
                response = Response(
                    {"detail": auth_error}, status=status.HTTP_400_BAD_REQUEST
                )
            code = request.query_params.get("code", None)
            if not code:
                response = Response(
                    {"detail": "Code is not present in the query parameter"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return self.finalize_response(request, response, *args, **kwargs)

        # Retrieve Access and Refresh token
        app = self.adapter.get_provider().get_app(self.request)
        client = self.get_client(self.request, app)

        try:
            client.state = self.request.query_params.get("state")
            access_token = self.adapter.get_access_token_data(request, app, client)
            token = self.adapter.parse_token(access_token)
            token.app = app

            # Perform the specified action (Add Event to Google Calendar) on the resource server
            complete_action = self.adapter.complete_action(
                request, app, token, response=access_token
            )

            response = complete_action

            self.response = self.finalize_response(request, response, *args, **kwargs)
            return self.response
        except (
            PermissionDenied,
            OAuth2Error,
            RequestException,
            ProviderException,
        ) as e:
            return Response({"detail": e}, status=status.HTTP_400_BAD_REQUEST)


class OAuth2GrantView(OAuth2APIView):
    def grant(self, request):
        """Perform the Authorization grant"""
        # __import__("ipdb").set_trace()
        provider = self.adapter.get_provider()
        app = provider.get_app(self.request)
        __import__("ipdb").set_trace()
        client = self.get_client(request, app)
        action = request.query_params.get("action", AuthAction.AUTHENTICATE)
        auth_url = self.adapter.authorize_url
        auth_params = provider.get_auth_params(request, action)
        if not request.query_params.get("action"):
            return Response(
                {"detail": "No action was specified in the Query Parameter"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        client.state = self.adapter.get_encoded_state(request)
        # client.call_back_url = f"{self.provider.id}_callback"
        try:
            return HttpResponseRedirect(client.get_redirect_url(auth_url, auth_params))
        except OAuth2Error as e:
            return render_authentication_error(request, provider.id, exception=e)
