from rest_framework.views import APIView


class OAuthGrantMixin(APIView):
    def dispatch(self, request, *args, **kwargs):
        """
        `.dispatch()` is pretty much the same as Django's regular dispatch,
        but with extra hooks for startup, finalize, and exception handling.

        I needed to override the dispatch method because the `request`
        from Allauth dispatch method does not have the `.query_params` and `.data` attribute.

        The dipatch method in Allauth are generally based on Django dispatch rather than DRF dispatch
        """

        self.args = args
        self.kwargs = kwargs
        request = self.initialize_request(request, *args, **kwargs)
        self.request = request
        self.headers = self.default_response_headers  # deprecate?

        try:
            self.initial(request, *args, **kwargs)
        except Exception as exc:
            return self.handle_exception(exc)
        return self.grant(request, *args, **kwargs)

    def grant(self, request, *args, **kwargs):
        """Logic to allow users to perform Authorization Grant"""
        raise NotImplementedError
