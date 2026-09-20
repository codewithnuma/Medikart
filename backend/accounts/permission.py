from rest_framework.permissions import BasePermission, SAFE_METHODS


# ============================================================
# PATIENT
# ============================================================

class IsUser(BasePermission):

    def has_permission(self, request, view):

        return (
            request.user.is_authenticated
            and request.user.role == "patient"
        )


# ============================================================
# ADMIN
# ============================================================

class IsAdmin(BasePermission):

    def has_permission(self, request, view):

        return (
            request.user.is_authenticated
            and request.user.role == "admin"
        )


# ============================================================
# PHARMACY
# ============================================================

class IsEmployee(BasePermission):

    def has_permission(self, request, view):

        return (
            request.user.is_authenticated
            and request.user.role == "pharmacy"
        )


# ============================================================
# ADMIN OR PHARMACY
# ============================================================

class IsAdminOrEmployee(BasePermission):

    def has_permission(self, request, view):

        return (
            request.user.is_authenticated
            and request.user.role in [
                "admin",
                "pharmacy"
            ]
        )


# ============================================================
# READ ONLY
# ============================================================

class ReadOnly(BasePermission):

    def has_permission(self, request, view):

        return request.method in SAFE_METHODS


# ============================================================
# REPORT OWNER OR READ ONLY
# ============================================================

class IsReportOwnerOrReadOnly(BasePermission):

    message = (
        "You can only edit your own pending reports."
    )

    def has_object_permission(
        self,
        request,
        view,
        obj
    ):

        # Anyone authenticated can view
        if request.method in SAFE_METHODS:
            return True

        # Only the original report owner can edit
        if obj.reported_by != request.user:
            return False

        # Only pending reports can be edited
        if obj.status != "pending":

            self.message = (
                "This report can no longer be edited "
                "because it has already been processed."
            )

            return False

        return True


# ============================================================
# NOTICE OWNER OR ADMIN
# ============================================================

class IsNoticeOwnerOrAdmin(BasePermission):

    """
    Admin can edit/delete any notice.

    Pharmacy can edit/delete only notices
    created by themselves.

    Other pharmacies cannot modify
    someone else's notice.
    """

    def has_permission(
        self,
        request,
        view
    ):

        return (
            request.user.is_authenticated
            and request.user.role in [
                "admin",
                "pharmacy"
            ]
        )

    def has_object_permission(
        self,
        request,
        view,
        obj
    ):

        # Admin can modify every notice
        if request.user.role == "admin":
            return True

        # Pharmacy can modify only their own notice
        if request.user.role == "pharmacy":

            return (
                obj.created_by_id
                == request.user.id
            )

        return False
