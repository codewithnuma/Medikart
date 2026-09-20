from django.urls import path

from . import views

from .views import (
    rasa_get_token,
    rasa_verify_token,
)
from .views import PharmacyRegistrationView

urlpatterns = [
    path(
        "register/pharmacy/",
        PharmacyRegistrationView.as_view(),
        name="pharmacy-register"
    ),
    

    # ==========================================================
    # 🤖 RASA
    # ==========================================================

    # Get JWT token for Rasa
    path(
        "rasa-token/",
        rasa_get_token,
        name="rasa-get-token"
    ),

    # Verify authenticated user
    path(
        "rasa-verify/",
        rasa_verify_token,
        name="rasa-verify-token"
    ),


    # ==========================================================
    # 🔐 AUTHENTICATION
    # ==========================================================

    # Patient / Pharmacy registration
    #
    # IMPORTANT:
    # This does NOT create Users immediately.
    # It creates a RegistrationRequest with status=pending.
    #
    path(
        "register/",
        views.RegisterView.as_view(),
        name="register"
    ),

    # Login
    #
    # Only users already accepted by admin can log in.
    #
    path(
        "login/",
        views.CookieTokenObtainPairView.as_view(),
        name="login"
    ),

    # Refresh access token
    path(
        "refresh/",
        views.RefreshFromCookie.as_view(),
        name="token-refresh"
    ),

    # Logout
    path(
        "logout/",
        views.LogoutView.as_view(),
        name="logout"
    ),


    # ==========================================================
    # 👤 CURRENT USER
    # ==========================================================

    # Current logged-in user
    path(
        "me/",
        views.UserDetail.as_view(),
        name="user-detail"
    ),

    # Update current user
    path(
        "update-user/",
        views.UserUpdateView.as_view(),
        name="user-update"
    ),


    # ==========================================================
    # 👥 USER MANAGEMENT
    # ==========================================================

    # List accepted users
    #
    # Admin only
    #
    path(
        "users/",
        views.UserListView.as_view(),
        name="user-list"
    ),
    path(
    "patients/",
    views.PatientListView.as_view(),
    name="patient-list"
),

    # Get / update / delete a specific user
    path(
        "users/<int:pk>/",
        views.UserDetailView.as_view(),
        name="user-detail-by-id"
    ),


    # ==========================================================
    # ✅ REGISTRATION VERIFICATION
    # ==========================================================

    # List registration requests
    #
    # Admin only
    #
    # Example:
    #
    # GET /registration-requests/
    #
    # GET /registration-requests/?status=pending
    #
    path(
        "registration-requests/",
        views.RegistrationRequestListView.as_view(),
        name="registration-request-list"
    ),

    # View one registration request
    #
    # Admin can see:
    # - Patient citizenship number
    # - Citizenship front
    # - Citizenship back
    # - Pharmacy licence number
    # - Pharmacy licence document
    #
    path(
        "registration-requests/<int:pk>/",
        views.RegistrationRequestDetailView.as_view(),
        name="registration-request-detail"
    ),

    # Accept / deny registration
    #
    # POST:
    #
    # {
    #     "status": "accepted"
    # }
    #
    # OR
    #
    # {
    #     "status": "denied",
    #     "rejection_reason": "Invalid document"
    # }
    #
    path(
        "registration-requests/<int:pk>/review/",
        views.RegistrationReviewView.as_view(),
        name="registration-request-review"
    ),


    # ==========================================================
    # 🧾 USER PROFILES
    # ==========================================================

    # Current user's profile
    path(
        "profile/",
        views.CurrentUserProfileView.as_view(),
        name="current-user-profile"
    ),

    # All user profiles
    path(
        "user-profiles/",
        views.UserProfileListView.as_view(),
        name="user-profile-list"
    ),

    # Specific user profile
    path(
        "user-profiles/<int:pk>/",
        views.UserProfileDetailView.as_view(),
        name="user-profile-detail"
    ),


    # ==========================================================
    # 🔑 PASSWORD RESET
    # ==========================================================

    # Send OTP
    path(
        "forgot-password/",
        views.ForgotPasswordView.as_view(),
        name="forgot-password"
    ),

    # Verify OTP and reset password
    path(
        "reset-password/",
        views.ResetPasswordView.as_view(),
        name="reset-password"
    ),

]
