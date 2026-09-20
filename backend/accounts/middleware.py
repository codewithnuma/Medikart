# middleware.py
import json
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings

class RefreshCookieToBodyMiddleware(MiddlewareMixin):
    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.path.endswith('/accounts/refresh/') and request.method == 'POST':
            try:
                data = json.loads(request.body) if request.body else {}
            except ValueError:
                data = {}

            refresh_token = request.COOKIES.get('refresh_token')
            if refresh_token:
                data['refresh'] = refresh_token
                request._body = json.dumps(data).encode('utf-8')
        return None
    


from django.utils import timezone
from zoneinfo import ZoneInfo

class NepalTimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        timezone.activate(ZoneInfo("Asia/Kathmandu"))
        response = self.get_response(request)
        return response

