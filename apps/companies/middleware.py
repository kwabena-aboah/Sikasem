"""companies/middleware.py - Sets company context on request"""


class CompanyContextMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if hasattr(request, 'user') and request.user.is_authenticated:
            request.company = request.user.company
        else:
            request.company = None
        return self.get_response(request)
