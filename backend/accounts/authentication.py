from datetime import datetime
from django.utils.timezone import make_aware
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken
import logging

logger = logging.getLogger(__name__)

class JWTAuthenticationFromCookie(JWTAuthentication):
    def authenticate(self, request):
        token = request.COOKIES.get("access_token")
        source = "cookie"

        if not token:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
                source = "header"

        if not token:
            return None

        validated_token = self.get_validated_token(token)
        user = self.get_user(validated_token)

        # Only check token_version for cookie-based auth (webpage)
        # Skip for header-based auth (Rasa bot)
        if source == "cookie":
            if validated_token.get("token_version") != user.token_version:
                raise InvalidToken("Token revoked")

        return user, validated_token