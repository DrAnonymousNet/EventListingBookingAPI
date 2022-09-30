def get_request_param(request, param, default=None):
    if request is None:
        return default
    return request.POST.get(param) or request.GET.get(param, default)
