# A Base class for all OAuth2 Integration

## Instructions

### Configuration
- The Meta of the application created in OAuth2 Provider website should be registred in the config file with all necessary provider including the required scopes as shown below:

```
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        # For each OAuth based provider, either add a ``SocialApp``
        # (``socialaccount`` app) containing the required client
        # credentials, or list them here:
        'APP': {
            'client_id': config("GOOGLE_OUTH_CLIENT_ID"),
            'secret': config("GOOGLE_OUTH_CLIENT_SECRET"),
            'key': ''
        },
         'SCOPE': [
             "https://www.googleapis.com/auth/calendar.readonly",
             "https://www.googleapis.com/auth/calendar.events",
             "https://www.googleapis.com/auth/calendar",
         ],
        "AUTH_PARAMS": {
            "access_type": "offline",
        }
    }
}
```
- While registering the application on the provider website, the `redirect_uri` should be provided in the following format:

```
grant/google/callback/
```

### Grant and CallBack View

- While calling the `{provider}_grant_view` endpoint, an `action` query parameter should be specified with a value of an action to be performed:
```
http://127.0.0.1:8000/api/v1/events/?action=add_to_calendar
```
- A method with the action name prefixed with `complete_` should be implemeted on the Provider Adapter class.The method performs the logic necessary to perform the specified action on the resource server:

```
class GoogleOAuth2Adapter(OAuth2Adapter):
        ...

    def complete_add_to_calendar(self, request, app, token, **kwargs):
        ...
```

### Adapter Class

- An adapter class for the provider class should be created and the providers `Authorization grant endpoint` , `Access Token endpoint` and the `Allauth provider id` specified as `authorization_url`, `access_token_url`, `provider_id` respectively:

```
class GoogleOAuth2Adapter(OAuth2Adapter):
    provider_id = GoogleProvider.id
    access_token_url = "https://accounts.google.com/o/oauth2/token"
    authorize_url = "https://accounts.google.com/o/oauth2/auth"

    def complete_event_insert(self, request, app, token, **kwargs):
        scope =request.query_params.get("scope")
            ...
```
- The adapter class should implment a `complete_{action name}` name method as said above

- Implement a `get_callback_uri` method in the adapter class that returns the url pattern you want to use for callback


### URL Configuration

- The Grant view and the Callback view should be initiated with the provider Adapter as shown below:
```
google_oauth2_grant_view = OAuth2GrantView.adapter_view(GoogleOAuth2Adapter)
google_oauth2_callback_view = OAuth2CallbackView.adapter_view(GoogleOAuth2Adapter)
```
