import os
import random

from uuid import uuid4
from datetime import timedelta

from django.db import models
from django.conf import settings
from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
    BaseUserManager,
)
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from django.utils.html import mark_safe


# ============================================================
# CUSTOM USER MANAGER
# ============================================================

class CustomAccountManager(BaseUserManager):

    def create_user(
        self,
        email,
        username,
        password=None,
        **extra_fields
    ):
        if not email:
            raise ValueError("Email is required")

        if not username:
            raise ValueError("Username is required")

        email = self.normalize_email(email)

        role = extra_fields.get("role", "patient")

        user = self.model(
            email=email,
            username=username,
            **extra_fields
        )

        if password:
            user.set_password(password)

        # Pharmacy/admin can be staff if required.
        if role in ["admin", "pharmacy"]:
            user.is_staff = True

        user.save(using=self._db)

        return user

    def create_superuser(
        self,
        email,
        username,
        password=None,
        **extra_fields
    ):
        extra_fields.setdefault("role", "admin")
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True")

        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True")

        return self.create_user(
            email=email,
            username=username,
            password=password,
            **extra_fields
        )


# ============================================================
# USERS
# ============================================================

class Users(AbstractBaseUser, PermissionsMixin):

    ROLES = (
        ("admin", "Admin"),
        ("pharmacy", "Pharmacy"),
        ("patient", "Patient"),
    )

    role = models.CharField(
        max_length=20,
        choices=ROLES,
        default="patient",
    )

    email = models.EmailField(
        unique=True
    )

    username = models.CharField(
        max_length=255,
        unique=True
    )

    # Patient identification
    citizenship_number = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True,
    )

    # Pharmacy identification
    pharmacy_license_number = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True,
    )

    # JWT security
    token_version = models.IntegerField(
        default=0
    )

    last_logout = models.DateTimeField(
        null=True,
        blank=True
    )

    # Django permissions
    is_staff = models.BooleanField(
        default=False
    )

    is_superuser = models.BooleanField(
        default=False
    )

    is_active = models.BooleanField(
        default=True
    )

    date_joined = models.DateTimeField(
        default=timezone.now
    )

    objects = CustomAccountManager()

    USERNAME_FIELD = "email"

    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        return f"{self.username} ({self.role})"


# ============================================================
# REGISTRATION REQUEST
# ============================================================

def registration_upload_path(instance, filename):

    extension = filename.split(".")[-1]

    filename = f"{uuid4().hex}.{extension}"

    return os.path.join(
        "registration_documents",
        str(instance.id),
        filename
    )


class RegistrationRequest(models.Model):

    ROLE_CHOICES = (
        ("patient", "Patient"),
        ("pharmacy", "Pharmacy"),
    )

    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("denied", "Denied"),
    )

    # --------------------------------------------------------
    # Basic information
    # --------------------------------------------------------

    email = models.EmailField()

    username = models.CharField(
        max_length=255
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES
    )

    phone_number = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    # --------------------------------------------------------
    # Password
    #
    # IMPORTANT:
    # This contains a HASH, not the user's raw password.
    # --------------------------------------------------------

    password = models.CharField(
        max_length=128
    )

    # --------------------------------------------------------
    # Patient information
    # --------------------------------------------------------

    citizenship_number = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    citizenship_front = models.ImageField(
        upload_to=registration_upload_path,
        blank=True,
        null=True
    )

    citizenship_back = models.ImageField(
        upload_to=registration_upload_path,
        blank=True,
        null=True
    )

    # --------------------------------------------------------
    # Pharmacy information
    # --------------------------------------------------------

    pharmacy_license_number = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    pharmacy_license_document = models.FileField(
        upload_to=registration_upload_path,
        blank=True,
        null=True
    )

    # --------------------------------------------------------
    # Verification
    # --------------------------------------------------------

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

    rejection_reason = models.TextField(
        blank=True,
        null=True
    )

    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_registrations"
    )

    reviewed_at = models.DateTimeField(
        null=True,
        blank=True
    )

    # --------------------------------------------------------
    # Dates
    # --------------------------------------------------------

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):

        return (
            f"{self.username} - "
            f"{self.role} - "
            f"{self.status}"
        )

    # ========================================================
    # ACCEPT REGISTRATION
    # ========================================================

    def accept(self, admin_user):

        if self.status != "pending":
            raise ValueError(
                "Only pending registrations can be accepted."
            )

        # Prevent duplicate email
        if Users.objects.filter(
            email=self.email
        ).exists():

            raise ValueError(
                "A user with this email already exists."
            )

        # Prevent duplicate username
        if Users.objects.filter(
            username=self.username
        ).exists():

            raise ValueError(
                "A user with this username already exists."
            )

        # Patient duplicate citizenship
        if (
            self.role == "patient"
            and self.citizenship_number
            and Users.objects.filter(
                citizenship_number=self.citizenship_number
            ).exists()
        ):

            raise ValueError(
                "This citizenship number is already registered."
            )

        # Pharmacy duplicate licence
        if (
            self.role == "pharmacy"
            and self.pharmacy_license_number
            and Users.objects.filter(
                pharmacy_license_number=self.pharmacy_license_number
            ).exists()
        ):

            raise ValueError(
                "This pharmacy licence number is already registered."
            )

        # ----------------------------------------------------
        # Create actual user
        # ----------------------------------------------------

        user = Users(
            email=self.email,
            username=self.username,
            role=self.role,
            citizenship_number=(
                self.citizenship_number
                if self.role == "patient"
                else None
            ),
            pharmacy_license_number=(
                self.pharmacy_license_number
                if self.role == "pharmacy"
                else None
            ),
            is_active=True,
            is_staff=(
                True
                if self.role == "pharmacy"
                else False
            ),
        )

        # password already contains a Django hash
        user.password = self.password

        user.save()

        # ----------------------------------------------------
        # Create profile
        # ----------------------------------------------------

        UserProfile.objects.get_or_create(
            user=user,
            defaults={
                "phone_number": self.phone_number
            }
        )

        # ----------------------------------------------------
        # Update request
        # ----------------------------------------------------

        self.status = "accepted"
        self.reviewed_by = admin_user
        self.reviewed_at = timezone.now()
        self.rejection_reason = None

        self.save(
            update_fields=[
                "status",
                "reviewed_by",
                "reviewed_at",
                "rejection_reason",
                "updated_at",
            ]
        )

        return user

    # ========================================================
    # DENY REGISTRATION
    # ========================================================

    def deny(
        self,
        admin_user,
        reason=None
    ):

        if self.status != "pending":
            raise ValueError(
                "Only pending registrations can be denied."
            )

        self.status = "denied"

        self.reviewed_by = admin_user

        self.reviewed_at = timezone.now()

        self.rejection_reason = (
            reason
            or "Registration denied by administrator."
        )

        self.save()

        return self


# ============================================================
# USER PROFILE
# ============================================================

def user_directory_path(
    instance,
    filename
):

    extension = filename.split(".")[-1]

    filename = f"{uuid4().hex}.{extension}"

    return os.path.join(
        "user_images",
        str(instance.user.id),
        filename
    )


class UserProfile(models.Model):

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile"
    )

    profile_image = models.ImageField(
        upload_to=user_directory_path,
        blank=True,
        null=True
    )

    bio = models.TextField(
        blank=True,
        null=True
    )

    birth_date = models.DateField(
        blank=True,
        null=True
    )

    location = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    phone_number = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        default=timezone.now
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"Profile of {self.user.username}"

    def profile_image_tag(self):

        if self.profile_image:

            return mark_safe(
                f'''
                <img
                    src="{self.profile_image.url}"
                    width="60"
                    height="60"
                    style="
                        object-fit: cover;
                        border-radius: 5px;
                    "
                />
                '''
            )

        return "Image not available"

    profile_image_tag.short_description = "Image"


# ============================================================
# PASSWORD RESET OTP
# ============================================================

class PasswordResetOTP(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    otp = models.CharField(
        max_length=6
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    @staticmethod
    def generate_otp():

        return str(
            random.randint(
                100000,
                999999
            )
        )

    def __str__(self):

        return f"{self.user.email} - {self.otp}"