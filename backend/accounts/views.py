import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone

from rest_framework import generics, status
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import (
    Users,
    UserProfile,
    RegistrationRequest,
)

from .serializer import (
    RegistrationSerializer,
    CustomUserSerializer,
    UserUpdateSerializer,
    UserProfileSerializer,
    UserSerializer,
    CustomTokenObtainPairSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer,
    RegistrationRequestSerializer,
)

from .permission import (
    IsUser,
    IsAdmin,
    IsEmployee,
    IsAdminOrEmployee,
    ReadOnly,
)


logger = logging.getLogger(__name__)

User = get_user_model()


# ============================================================
# JWT AUTHENTICATION FROM COOKIE
# ============================================================

class JWTAuthenticationFromCookie(JWTAuthentication):

    def authenticate(self, request):

        token = request.COOKIES.get("access_token")
        source = "cookie"

        # ----------------------------------------------------
        # Fallback to Authorization header
        # ----------------------------------------------------

        if not token:

            auth_header = request.headers.get("Authorization")

            if (
                auth_header
                and auth_header.startswith("Bearer ")
            ):
                token = auth_header.split(" ")[1]
                source = "header"

        if not token:
            return None

        # ----------------------------------------------------
        # Validate token
        # ----------------------------------------------------

        validated_token = self.get_validated_token(token)

        user = self.get_user(validated_token)

        # ----------------------------------------------------
        # Check token version for cookie authentication
        # ----------------------------------------------------

        if source == "cookie":

            token_version = validated_token.get(
                "token_version"
            )

            if token_version != user.token_version:

                raise InvalidToken(
                    "Token revoked"
                )

        return user, validated_token


# ============================================================
# REGISTRATION
# ============================================================

class RegisterView(
    generics.CreateAPIView
):

    permission_classes = [
        AllowAny
    ]

    authentication_classes = []

    serializer_class = RegistrationSerializer

    def create(
        self,
        request,
        *args,
        **kwargs
    ):

        serializer = self.get_serializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        registration = serializer.save()

        return Response(
            {
                "message": (
                    "Registration submitted successfully. "
                    "Your account is waiting for admin verification."
                ),

                "registration_id": registration.id,

                "status": registration.status,

                "role": registration.role,

                "email": registration.email,

                "username": registration.username,
            },

            status=status.HTTP_201_CREATED
        )


# ============================================================
# LOGIN
# ============================================================

class CookieTokenObtainPairView(
    TokenObtainPairView
):

    permission_classes = [
        AllowAny
    ]

    authentication_classes = []

    serializer_class = (
        CustomTokenObtainPairSerializer
    )

    def post(
        self,
        request,
        *args,
        **kwargs
    ):

        response = super().post(
            request,
            *args,
            **kwargs
        )

        access_token = response.data.pop(
            "access",
            None
        )

        refresh_token = response.data.pop(
            "refresh",
            None
        )

        # ----------------------------------------------------
        # Access token cookie
        # ----------------------------------------------------

        if access_token:

            response.set_cookie(
                "access_token",
                access_token,

                httponly=True,
                secure=True,
                samesite="None",

                max_age=300,

                path="/",
            )

        # ----------------------------------------------------
        # Refresh token cookie
        # ----------------------------------------------------

        if refresh_token:

            response.set_cookie(
                "refresh_token",
                refresh_token,

                httponly=True,
                secure=True,
                samesite="None",

                max_age=7 * 24 * 3600,

                path="/",
            )

        return response


# ============================================================
# REFRESH TOKEN
# ============================================================

class RefreshFromCookie(APIView):

    permission_classes = [
        AllowAny
    ]

    authentication_classes = []

    def post(self, request):

        refresh_token = request.COOKIES.get(
            "refresh_token"
        )

        if not refresh_token:

            return Response(
                {
                    "detail": "No refresh token"
                },
                status=status.HTTP_401_UNAUTHORIZED
            )

        try:

            refresh = RefreshToken(
                refresh_token
            )

            user_id = refresh["user_id"]

            user = User.objects.get(
                id=user_id
            )

            # ------------------------------------------------
            # Create new access token
            # ------------------------------------------------

            access = refresh.access_token

            access["token_version"] = (
                user.token_version
            )

            response = Response(
                {
                    "detail": "Token refreshed"
                }
            )

            response.set_cookie(
                "access_token",
                str(access),

                httponly=True,
                secure=True,
                samesite="None",

                max_age=300,

                path="/",
            )

            # ------------------------------------------------
            # Rotate refresh token
            # ------------------------------------------------

            if settings.SIMPLE_JWT.get(
                "ROTATE_REFRESH_TOKENS"
            ):

                try:

                    refresh.blacklist()

                except Exception:
                    pass

                new_refresh = (
                    RefreshToken.for_user(user)
                )

                new_refresh[
                    "token_version"
                ] = user.token_version

                response.set_cookie(
                    "refresh_token",
                    str(new_refresh),

                    httponly=True,
                    secure=True,
                    samesite="None",

                    max_age=7 * 24 * 3600,

                    path="/",
                )

            return response

        except Exception as e:

            logger.error(
                f"Refresh failed: {e}"
            )

            return Response(
                {
                    "detail": (
                        "Invalid refresh token"
                    )
                },
                status=status.HTTP_401_UNAUTHORIZED
            )


# ============================================================
# LOGOUT
# ============================================================

class LogoutView(APIView):

    permission_classes = [
        IsAuthenticated
    ]

    authentication_classes = [
        JWTAuthenticationFromCookie
    ]

    def post(self, request):

        user = request.user

        # ----------------------------------------------------
        # Revoke all current access tokens
        # ----------------------------------------------------

        user.last_logout = timezone.now()

        user.token_version += 1

        user.save(
            update_fields=[
                "last_logout",
                "token_version",
            ]
        )

        # ----------------------------------------------------
        # Blacklist refresh token
        # ----------------------------------------------------

        refresh_token = request.COOKIES.get(
            "refresh_token"
        )

        if refresh_token:

            try:

                RefreshToken(
                    refresh_token
                ).blacklist()

            except Exception:
                pass

        # ----------------------------------------------------
        # Clear cookies
        # ----------------------------------------------------

        response = Response(
            {
                "detail": (
                    "Logged out successfully"
                )
            },
            status=status.HTTP_205_RESET_CONTENT
        )

        response.delete_cookie(
            "access_token",
            path="/"
        )

        response.delete_cookie(
            "refresh_token",
            path="/"
        )

        return response


# ============================================================
# CURRENT USER
# ============================================================

class UserDetail(APIView):

    permission_classes = [
        IsAuthenticated
    ]

    authentication_classes = [
        JWTAuthenticationFromCookie
    ]

    def get(self, request):

        return Response(
            CustomUserSerializer(
                request.user
            ).data
        )


# ============================================================
# UPDATE CURRENT USER
# ============================================================

class UserUpdateView(APIView):

    permission_classes = [
        IsAuthenticated
    ]

    authentication_classes = [
        JWTAuthenticationFromCookie
    ]

    def patch(
        self,
        request
    ):

        serializer = UserUpdateSerializer(
            request.user,

            data=request.data,

            partial=True,

            context={
                "request": request
            }
        )

        serializer.is_valid(
            raise_exception=True
        )

        serializer.save()

        return Response(
            serializer.data
        )


# ============================================================
# USER LIST
# ============================================================

class UserListView(
    generics.ListAPIView
):

    queryset = Users.objects.all()

    serializer_class = UserSerializer

    permission_classes = [
        IsAdminOrEmployee
    ]

    authentication_classes = [
        JWTAuthenticationFromCookie
    ]
    
class PatientListView(
    generics.ListAPIView
):
    serializer_class = UserSerializer

    permission_classes = [
        IsAdminOrEmployee
    ]

    authentication_classes = [
        JWTAuthenticationFromCookie
    ]

    def get_queryset(self):
        return Users.objects.filter(
        role="patient",
        medicine_orders__pharmacy=self.request.user
    ).distinct().order_by("username")


# ============================================================
# USER DETAIL
# ============================================================

class UserDetailView(
    generics.RetrieveUpdateDestroyAPIView
):

    queryset = Users.objects.all()

    serializer_class = UserSerializer

    permission_classes = [
        IsAuthenticated
    ]

    authentication_classes = [
        JWTAuthenticationFromCookie
    ]


# ============================================================
# USER PROFILE LIST
# ============================================================

class UserProfileListView(
    generics.ListAPIView
):

    queryset = UserProfile.objects.all()

    serializer_class = UserProfileSerializer

    permission_classes = [
        IsAuthenticated
    ]

    authentication_classes = [
        JWTAuthenticationFromCookie
    ]


# ============================================================
# USER PROFILE DETAIL
# ============================================================

class UserProfileDetailView(
    generics.RetrieveUpdateAPIView
):

    queryset = UserProfile.objects.all()

    serializer_class = UserProfileSerializer

    permission_classes = [
        IsAuthenticated
    ]

    authentication_classes = [
        JWTAuthenticationFromCookie
    ]


# ============================================================
# CURRENT USER PROFILE
# ============================================================

class CurrentUserProfileView(APIView):

    permission_classes = [
        IsAuthenticated
    ]

    authentication_classes = [
        JWTAuthenticationFromCookie
    ]

    def get(self, request):

        profile, created = (
            UserProfile.objects.get_or_create(
                user=request.user
            )
        )

        serializer = UserProfileSerializer(
            profile,

            context={
                "request": request
            }
        )

        return Response(
            serializer.data
        )

    def patch(
        self,
        request
    ):

        profile, created = (
            UserProfile.objects.get_or_create(
                user=request.user
            )
        )

        serializer = UserProfileSerializer(
            profile,

            data=request.data,

            partial=True,

            context={
                "request": request
            }
        )

        serializer.is_valid(
            raise_exception=True
        )

        serializer.save()

        return Response(
            serializer.data
        )


# ============================================================
# REGISTRATION REQUEST LIST
# ADMIN ONLY
# ============================================================

class RegistrationRequestListView(
    generics.ListAPIView
):

    serializer_class = (
        RegistrationRequestSerializer
    )

    permission_classes = [
        IsAdmin
    ]

    authentication_classes = [
        JWTAuthenticationFromCookie
    ]

    def get_queryset(self):

        queryset = (
            RegistrationRequest.objects.all()
        )

        request_status = (
            self.request.query_params.get(
                "status"
            )
        )

        if request_status:

            queryset = queryset.filter(
                status=request_status
            )

        return queryset.order_by(
            "-created_at"
        )


# ============================================================
# REGISTRATION REQUEST DETAIL
# ============================================================

class RegistrationRequestDetailView(
    generics.RetrieveAPIView
):

    queryset = RegistrationRequest.objects.all()

    serializer_class = (
        RegistrationRequestSerializer
    )

    permission_classes = [
        IsAdmin
    ]

    authentication_classes = [
        JWTAuthenticationFromCookie
    ]


# ============================================================
# REGISTRATION REVIEW
# ============================================================

class RegistrationReviewView(APIView):

    permission_classes = [
        IsAdmin
    ]

    authentication_classes = [
        JWTAuthenticationFromCookie
    ]

    def post(
        self,
        request,
        pk
    ):

        try:

            registration = (
                RegistrationRequest.objects.get(
                    pk=pk
                )
            )

        except RegistrationRequest.DoesNotExist:

            return Response(
                {
                    "detail": (
                        "Registration request not found."
                    )
                },

                status=status.HTTP_404_NOT_FOUND
            )

        # ----------------------------------------------------
        # Cannot review twice
        # ----------------------------------------------------

        if registration.status != "pending":

            return Response(
                {
                    "detail": (
                        "This registration has "
                        "already been reviewed."
                    ),

                    "status": registration.status,
                },

                status=status.HTTP_400_BAD_REQUEST
            )

        review_status = request.data.get(
            "status"
        )

        rejection_reason = request.data.get(
            "rejection_reason",
            ""
        )

        # ====================================================
        # DENY
        # ====================================================

        if review_status == "denied":

            registration.status = "denied"

            registration.reviewed_by = (
                request.user
            )

            registration.reviewed_at = (
                timezone.now()
            )

            registration.rejection_reason = (
                rejection_reason
                or "Registration denied by administrator."
            )

            registration.save()

            return Response(
                {
                    "message": (
                        "Registration denied."
                    ),

                    "status": "denied",

                    "registration_id": (
                        registration.id
                    ),
                },

                status=status.HTTP_200_OK
            )

        # ====================================================
        # ACCEPT
        # ====================================================

        if review_status == "accepted":

            # ------------------------------------------------
            # Check email duplicate
            # ------------------------------------------------

            if Users.objects.filter(
                email=registration.email
            ).exists():

                return Response(
                    {
                        "detail": (
                            "A user with this email "
                            "already exists."
                        )
                    },

                    status=status.HTTP_400_BAD_REQUEST
                )

            # ------------------------------------------------
            # Check username duplicate
            # ------------------------------------------------

            if Users.objects.filter(
                username=registration.username
            ).exists():

                return Response(
                    {
                        "detail": (
                            "A user with this username "
                            "already exists."
                        )
                    },

                    status=status.HTTP_400_BAD_REQUEST
                )

            # ------------------------------------------------
            # Create user
            #
            # IMPORTANT:
            # RegistrationRequest.password should contain
            # a hashed password.
            # ------------------------------------------------

            user = Users(
                email=registration.email,

                username=registration.username,

                role=registration.role,

                is_active=True,

                is_staff=(
                    registration.role == "admin"
                ),
            )

            # Use set_password only if the registration
            # model stores the RAW password.
            #
            # If your serializer already hashes it,
            # use the hashed value directly.
            #
            user.password = (
                registration.password
            )

            user.save()

            # ------------------------------------------------
            # Create profile
            # ------------------------------------------------

            UserProfile.objects.create(
                user=user,

                phone_number=(
                    registration.phone_number
                ),
            )

            # ------------------------------------------------
            # Update registration
            # ------------------------------------------------

            registration.status = "accepted"

            registration.reviewed_by = (
                request.user
            )

            registration.reviewed_at = (
                timezone.now()
            )

            registration.rejection_reason = ""

            registration.save()

            return Response(
                {
                    "message": (
                        "Registration accepted "
                        "and user account created."
                    ),

                    "status": "accepted",

                    "registration_id": (
                        registration.id
                    ),

                    "user_id": user.id,
                },

                status=status.HTTP_200_OK
            )

        # ====================================================
        # INVALID STATUS
        # ====================================================

        return Response(
            {
                "detail": (
                    "Status must be either "
                    "'accepted' or 'denied'."
                )
            },

            status=status.HTTP_400_BAD_REQUEST
        )


# ============================================================
# RASA TOKEN
# ============================================================

@api_view(["GET"])
@authentication_classes(
    [JWTAuthenticationFromCookie]
)
@permission_classes(
    [IsAuthenticated]
)
def rasa_get_token(request):

    user = request.user

    token = AccessToken.for_user(
        user
    )

    token["token_version"] = (
        user.token_version
    )

    return Response(
        {
            "authenticated": True,

            "jwt_token": str(token),

            "user": {
                "id": user.id,

                "username": user.username,

                "email": user.email,

                "role": user.role,
            },
        },

        status=status.HTTP_200_OK
    )


# ============================================================
# RASA VERIFY TOKEN
# ============================================================

@api_view(["GET"])
@authentication_classes(
    [JWTAuthenticationFromCookie]
)
@permission_classes(
    [IsAuthenticated]
)
def rasa_verify_token(request):

    return Response(
        {
            "authenticated": True,

            "user_id": request.user.id,

            "username": request.user.username,

            "email": request.user.email,

            "role": request.user.role,
        },

        status=status.HTTP_200_OK
    )


# ============================================================
# FORGOT PASSWORD
# ============================================================

class ForgotPasswordView(APIView):

    permission_classes = [
        AllowAny
    ]

    authentication_classes = []

    def post(
        self,
        request
    ):

        serializer = (
            ForgotPasswordSerializer(
                data=request.data
            )
        )

        serializer.is_valid(
            raise_exception=True
        )

        serializer.save()

        return Response(
            {
                "message": (
                    "OTP sent to email."
                )
            },

            status=status.HTTP_200_OK
        )


# ============================================================
# RESET PASSWORD
# ============================================================

class ResetPasswordView(APIView):

    permission_classes = [
        AllowAny
    ]

    authentication_classes = []

    def post(
        self,
        request
    ):

        serializer = (
            ResetPasswordSerializer(
                data=request.data
            )
        )

        serializer.is_valid(
            raise_exception=True
        )

        serializer.save()

        return Response(
            {
                "message": (
                    "Password changed successfully."
                )
            },

            status=status.HTTP_200_OK
        )
        
from .pharmacy_verification import start_pharmacy_verification,is_internal_request,transaction
class RegisterView(
    generics.CreateAPIView
):

    permission_classes = [
        AllowAny
    ]

    authentication_classes = []

    serializer_class = RegistrationSerializer

    def create(
        self,
        request,
        *args,
        **kwargs
    ):

        serializer = self.get_serializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        registration = serializer.save()

        is_pharmacy = (
            str(registration.role).lower() == "pharmacy"
        )

        # ----------------------------------------------------
        # PHARMACY -> hand over to the AI agent
        #
        # The agent verifies the licence with the Nepal Pharmacy
        # Council, creates the user (via /register/pharmacy/) or
        # leaves the request denied, and emails the result.
        # This runs in the background; the response is immediate.
        # ----------------------------------------------------

        if is_pharmacy:

            license_no = (
                getattr(registration, "pharmacy_license_number", None)
                or request.data.get("pharmacy_license_number")
                or ""
            )

            start_pharmacy_verification(
                registration,
                str(license_no),
            )

            message = (
                "Registration submitted. We are verifying your "
                "pharmacy licence with the Nepal Pharmacy Council. "
                "You will receive an email with the result shortly."
            )

            verification = "in_progress"

        # ----------------------------------------------------
        # PATIENT -> unchanged, waits for admin
        # ----------------------------------------------------

        else:

            message = (
                "Registration submitted successfully. "
                "Your account is waiting for admin verification."
            )

            verification = "manual_review"

        return Response(
            {
                "message": message,

                "registration_id": registration.id,

                "status": registration.status,

                "verification": verification,

                "role": registration.role,

                "email": registration.email,

                "username": registration.username,
            },

            status=status.HTTP_201_CREATED
        )


# ============================================================
# PHARMACY USER CREATION  —  INTERNAL ONLY
#
#   POST /api/accounts/register/pharmacy/
#   Header: X-Internal-Key: <INTERNAL_API_KEY>
#   JSON:   {"registration_id": 12, "license_no": "G6432", ...}
#
# Called by the AI agent AFTER the licence was verified.
#
# SECURITY: the old version of this endpoint had no authentication,
# so anyone could POST here and create a pharmacy account without
# verification. It is now locked with a shared secret.
#
# The password is never sent: the user is created from the
# RegistrationRequest row, which already stores the hashed password
# (same approach as RegistrationReviewView).
# ============================================================

class PharmacyRegistrationView(APIView):

    authentication_classes = []
    permission_classes = []

    def post(self, request):

        if not is_internal_request(request):

            return Response(
                {"detail": "Forbidden."},
                status=status.HTTP_403_FORBIDDEN
            )

        registration_id = request.data.get(
            "registration_id"
        )

        if not registration_id:

            return Response(
                {"detail": "registration_id is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():

            try:

                registration = (
                    RegistrationRequest.objects
                    .select_for_update()
                    .get(pk=registration_id)
                )

            except (
                RegistrationRequest.DoesNotExist,
                ValueError,
            ):

                return Response(
                    {"detail": "Registration request not found."},
                    status=status.HTTP_404_NOT_FOUND
                )

            if str(registration.role).lower() != "pharmacy":

                return Response(
                    {"detail": "This is not a pharmacy registration."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if registration.status != "pending":

                return Response(
                    {
                        "detail": (
                            "This registration has already "
                            "been reviewed."
                        ),
                        "status": registration.status,
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            if Users.objects.filter(
                email=registration.email
            ).exists():

                return Response(
                    {"detail": "A user with this email already exists."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if Users.objects.filter(
                username=registration.username
            ).exists():

                return Response(
                    {"detail": "A user with this username already exists."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            license_no = (
                getattr(registration, "pharmacy_license_number", None)
                or request.data.get("license_no")
                or ""
            )

            user = Users(
                email=registration.email,

                username=registration.username,

                role=registration.role,

                is_active=True,

                is_staff=False,
            )

            # RegistrationRequest.password is already hashed.
            user.password = registration.password

            user.pharmacy_license_number = license_no

            user.save()

            UserProfile.objects.create(
                user=user,

                phone_number=registration.phone_number,
            )

            # Auto-approved by the AI agent (no admin user).
            registration.status = "accepted"

            registration.reviewed_at = timezone.now()

            registration.rejection_reason = ""

            registration.save()

        return Response(
            {
                "message": "Pharmacy registered successfully.",

                "registration_id": registration.id,

                "user": {
                    "id": user.id,

                    "email": user.email,

                    "username": user.username,

                    "role": user.role,

                    "pharmacy_license_number": license_no,

                    "is_active": user.is_active,
                },
            },

            status=status.HTTP_201_CREATED
        )