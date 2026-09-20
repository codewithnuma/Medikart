from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.utils import timezone

from .models import (
    Users,
    UserProfile,
    RegistrationRequest,
)


# ============================================================
# USERS ADMIN
# ============================================================

@admin.register(Users)
class CustomUserAdmin(UserAdmin):

    ordering = ["email"]

    list_display = (
        "email",
        "username",
        "role",
        "is_superuser",
        "is_staff",
        "is_active",
        "date_joined",
    )

    list_filter = (
        "role",
        "is_staff",
        "is_superuser",
        "is_active",
    )

    search_fields = (
        "email",
        "username",
        "citizenship_number",
        "pharmacy_license_number",
    )

    readonly_fields = (
        "date_joined",
        "last_login",
    )

    fieldsets = (

        (
            "Basic Information",
            {
                "fields": (
                    "email",
                    "username",
                    "password",
                )
            },
        ),

        (
            "Identification",
            {
                "fields": (
                    "citizenship_number",
                    "pharmacy_license_number",
                )
            },
        ),

        (
            "Role",
            {
                "fields": (
                    "role",
                )
            },
        ),

        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),

        (
            "Security",
            {
                "fields": (
                    "token_version",
                    "last_logout",
                )
            },
        ),

        (
            "Important Dates",
            {
                "fields": (
                    "last_login",
                    "date_joined",
                )
            },
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),

                "fields": (
                    "email",
                    "username",
                    "password1",
                    "password2",
                    "role",
                    "citizenship_number",
                    "pharmacy_license_number",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                ),
            },
        ),
    )


# ============================================================
# REGISTRATION REQUEST ADMIN
# ============================================================

@admin.register(RegistrationRequest)
class RegistrationRequestAdmin(admin.ModelAdmin):

    # --------------------------------------------------------
    # LIST PAGE
    # --------------------------------------------------------

    list_display = (
        "id",
        "email",
        "username",
        "role",
        "status",
        "documents_display",
        "created_at",
        "reviewed_by",
        "reviewed_at",
    )

    list_filter = (
        "role",
        "status",
        "created_at",
        "reviewed_at",
    )

    search_fields = (
        "email",
        "username",
        "citizenship_number",
        "pharmacy_license_number",
    )

    ordering = (
        "-created_at",
    )

    # --------------------------------------------------------
    # READ ONLY
    # --------------------------------------------------------

    readonly_fields = (
        "created_at",
        "updated_at",
        "reviewed_at",
        "reviewed_by",

        "citizenship_front_preview",
        "citizenship_back_preview",
        "pharmacy_license_preview",

        "documents_display",
    )

    # --------------------------------------------------------
    # FORM
    # --------------------------------------------------------

    fieldsets = (

        (
            "Registration Information",
            {
                "fields": (
                    "email",
                    "username",
                    "role",
                    "phone_number",
                    "password",
                )
            },
        ),

        (
            "Patient Verification",
            {
                "fields": (
                    "citizenship_number",

                    "citizenship_front",
                    "citizenship_front_preview",

                    "citizenship_back",
                    "citizenship_back_preview",
                ),

                "description": (
                    "Citizenship documents uploaded "
                    "by the patient."
                ),
            },
        ),

        (
            "Pharmacy Verification",
            {
                "fields": (
                    "pharmacy_license_number",

                    "pharmacy_license_document",
                    "pharmacy_license_preview",
                ),

                "description": (
                    "Pharmacy license information "
                    "and uploaded license document."
                ),
            },
        ),

        (
            "Verification",
            {
                "fields": (
                    "status",
                    "rejection_reason",
                    "reviewed_by",
                    "reviewed_at",
                )
            },
        ),

        (
            "Dates",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    # ========================================================
    # DOCUMENT STATUS IN LIST
    # ========================================================

    @admin.display(
        description="Documents"
    )
    def documents_display(self, obj):

        documents = []

        if obj.citizenship_front:
            documents.append("Citizenship Front")

        if obj.citizenship_back:
            documents.append("Citizenship Back")

        if obj.pharmacy_license_document:
            documents.append("License")

        if not documents:
            return "No documents"

        return ", ".join(documents)

    # ========================================================
    # CITIZENSHIP FRONT PREVIEW
    # ========================================================

    @admin.display(
        description="Citizenship Front Preview"
    )
    def citizenship_front_preview(self, obj):

        if not obj.citizenship_front:
            return "No citizenship front image."

        try:
            url = obj.citizenship_front.url
        except Exception:
            return "File unavailable."

        return format_html(
            """
            <div style="
                margin-top:10px;
                padding:15px;
                background:#f8f9fa;
                border:1px solid #ddd;
                border-radius:8px;
            ">
                <img
                    src="{}"
                    style="
                        max-width:700px;
                        max-height:500px;
                        width:auto;
                        height:auto;
                        object-fit:contain;
                        border:1px solid #ccc;
                        border-radius:6px;
                        background:white;
                    "
                />

                <br><br>

                <a
                    href="{}"
                    target="_blank"
                    style="
                        display:inline-block;
                        padding:8px 14px;
                        background:#417690;
                        color:white;
                        border-radius:5px;
                        text-decoration:none;
                    "
                >
                    Open Full Image
                </a>
            </div>
            """,
            url,
            url,
        )

    # ========================================================
    # CITIZENSHIP BACK PREVIEW
    # ========================================================

    @admin.display(
        description="Citizenship Back Preview"
    )
    def citizenship_back_preview(self, obj):

        if not obj.citizenship_back:
            return "No citizenship back image."

        try:
            url = obj.citizenship_back.url
        except Exception:
            return "File unavailable."

        return format_html(
            """
            <div style="
                margin-top:10px;
                padding:15px;
                background:#f8f9fa;
                border:1px solid #ddd;
                border-radius:8px;
            ">
                <img
                    src="{}"
                    style="
                        max-width:700px;
                        max-height:500px;
                        width:auto;
                        height:auto;
                        object-fit:contain;
                        border:1px solid #ccc;
                        border-radius:6px;
                        background:white;
                    "
                />

                <br><br>

                <a
                    href="{}"
                    target="_blank"
                    style="
                        display:inline-block;
                        padding:8px 14px;
                        background:#417690;
                        color:white;
                        border-radius:5px;
                        text-decoration:none;
                    "
                >
                    Open Full Image
                </a>
            </div>
            """,
            url,
            url,
        )

    # ========================================================
    # PHARMACY LICENSE PREVIEW
    # ========================================================

    @admin.display(
        description="Pharmacy License Preview"
    )
    def pharmacy_license_preview(self, obj):

        if not obj.pharmacy_license_document:
            return "No pharmacy license document."

        try:
            url = obj.pharmacy_license_document.url
        except Exception:
            return "File unavailable."

        filename = str(
            obj.pharmacy_license_document.name
        ).lower()

        # ----------------------------------------------------
        # IMAGE
        # ----------------------------------------------------

        if filename.endswith(
            (
                ".jpg",
                ".jpeg",
                ".png",
                ".webp",
                ".gif",
            )
        ):

            return format_html(
                """
                <div style="
                    margin-top:10px;
                    padding:15px;
                    background:#f8f9fa;
                    border:1px solid #ddd;
                    border-radius:8px;
                ">

                    <img
                        src="{}"
                        style="
                            max-width:700px;
                            max-height:500px;
                            width:auto;
                            height:auto;
                            object-fit:contain;
                            border:1px solid #ccc;
                            border-radius:6px;
                            background:white;
                        "
                    />

                    <br><br>

                    <a
                        href="{}"
                        target="_blank"
                        style="
                            display:inline-block;
                            padding:8px 14px;
                            background:#417690;
                            color:white;
                            border-radius:5px;
                            text-decoration:none;
                        "
                    >
                        Open Full License
                    </a>

                </div>
                """,
                url,
                url,
            )

        # ----------------------------------------------------
        # PDF / OTHER DOCUMENT
        # ----------------------------------------------------

        return format_html(
            """
            <div style="
                margin-top:10px;
                padding:15px;
                background:#f8f9fa;
                border:1px solid #ddd;
                border-radius:8px;
            ">

                <strong>
                    Pharmacy License Document
                </strong>

                <br><br>

                <a
                    href="{}"
                    target="_blank"
                    style="
                        display:inline-block;
                        padding:10px 16px;
                        background:#417690;
                        color:white;
                        border-radius:5px;
                        text-decoration:none;
                    "
                >
                    Open License Document
                </a>

            </div>
            """,
            url,
        )

    # ========================================================
    # ADMIN ACTIONS
    # ========================================================

    actions = [
        "accept_selected",
        "deny_selected",
    ]

    # ========================================================
    # ACCEPT
    # ========================================================

    @admin.action(
        description="Accept selected registrations"
    )
    def accept_selected(
        self,
        request,
        queryset
    ):

        accepted = 0
        skipped = 0

        for registration in queryset:

            if registration.status != "pending":

                skipped += 1
                continue

            # ------------------------------------------------
            # EMAIL
            # ------------------------------------------------

            if Users.objects.filter(
                email=registration.email
            ).exists():

                self.message_user(
                    request,
                    (
                        f"Skipped {registration.email}: "
                        "email already exists."
                    ),
                    level="error"
                )

                skipped += 1
                continue

            # ------------------------------------------------
            # USERNAME
            # ------------------------------------------------

            if Users.objects.filter(
                username=registration.username
            ).exists():

                self.message_user(
                    request,
                    (
                        f"Skipped {registration.username}: "
                        "username already exists."
                    ),
                    level="error"
                )

                skipped += 1
                continue

            # ------------------------------------------------
            # CITIZENSHIP
            # ------------------------------------------------

            if (
                registration.role == "patient"
                and registration.citizenship_number
                and Users.objects.filter(
                    citizenship_number=(
                        registration.citizenship_number
                    )
                ).exists()
            ):

                self.message_user(
                    request,
                    (
                        f"Skipped {registration.username}: "
                        "citizenship number already exists."
                    ),
                    level="error"
                )

                skipped += 1
                continue

            # ------------------------------------------------
            # PHARMACY LICENSE
            # ------------------------------------------------

            if (
                registration.role == "pharmacy"
                and registration.pharmacy_license_number
                and Users.objects.filter(
                    pharmacy_license_number=(
                        registration.pharmacy_license_number
                    )
                ).exists()
            ):

                self.message_user(
                    request,
                    (
                        f"Skipped {registration.username}: "
                        "pharmacy license already exists."
                    ),
                    level="error"
                )

                skipped += 1
                continue

            # ------------------------------------------------
            # CREATE USER
            # ------------------------------------------------

            user = Users(
                email=registration.email,

                username=registration.username,

                role=registration.role,

                citizenship_number=(
                    registration.citizenship_number
                    if registration.role == "patient"
                    else None
                ),

                pharmacy_license_number=(
                    registration.pharmacy_license_number
                    if registration.role == "pharmacy"
                    else None
                ),

                is_active=True,

                is_staff=(
                    registration.role == "pharmacy"
                ),
            )

            # IMPORTANT:
            # RegistrationRequest.password already contains
            # the hashed password.

            user.password = registration.password

            user.save()

            # ------------------------------------------------
            # PROFILE
            # ------------------------------------------------

            UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    "phone_number": (
                        registration.phone_number
                    )
                }
            )

            # ------------------------------------------------
            # REGISTRATION
            # ------------------------------------------------

            registration.status = "accepted"

            registration.reviewed_by = request.user

            registration.reviewed_at = timezone.now()

            registration.rejection_reason = None

            registration.save()

            accepted += 1

        self.message_user(
            request,
            (
                f"{accepted} registration(s) accepted. "
                f"{skipped} skipped."
            )
        )

    # ========================================================
    # DENY
    # ========================================================

    @admin.action(
        description="Deny selected registrations"
    )
    def deny_selected(
        self,
        request,
        queryset
    ):

        denied = 0
        skipped = 0

        for registration in queryset:

            if registration.status != "pending":

                skipped += 1
                continue

            registration.status = "denied"

            registration.reviewed_by = request.user

            registration.reviewed_at = timezone.now()

            registration.rejection_reason = (
                "Registration denied by administrator."
            )

            registration.save()

            denied += 1

        self.message_user(
            request,
            (
                f"{denied} registration(s) denied. "
                f"{skipped} skipped."
            )
        )


# ============================================================
# USER PROFILE ADMIN
# ============================================================

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "profile_image_display",
        "phone_number",
        "location",
        "birth_date",
        "created_at",
    )

    readonly_fields = (
        "profile_image_display",
    )

    search_fields = (
        "user__email",
        "user__username",
        "phone_number",
    )

    list_filter = (
        "location",
        "birth_date",
    )

    # ========================================================
    # PROFILE IMAGE
    # ========================================================

    @admin.display(
        description="Profile Image"
    )
    def profile_image_display(self, obj):

        if not obj.profile_image:
            return "No image"

        try:
            url = obj.profile_image.url
        except Exception:
            return "File unavailable"

        return format_html(
            """
            <a href="{}" target="_blank">
                <img
                    src="{}"
                    width="80"
                    height="80"
                    style="
                        object-fit:cover;
                        border-radius:8px;
                        border:1px solid #ddd;
                    "
                />
            </a>
            """,
            url,
            url,
        )