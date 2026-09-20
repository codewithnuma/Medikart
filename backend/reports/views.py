from django.db import transaction
from django.shortcuts import get_object_or_404
from django.db.models import Q

from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response

from rest_framework.permissions import IsAuthenticated

from accounts.views import JWTAuthenticationFromCookie

from .models import Medicine, MedicineOrder

from .serializers import (
    MedicineSerializer,
    MedicineOrderSerializer,
    PharmacySerializer,
    PatientReportSerializer,
)

from accounts.permission import (
    IsUser,
    IsAdmin,
    IsEmployee,
    IsAdminOrEmployee,
)


# ============================================================
# MEDICINE LIST
#
# GET:
#   Everyone authenticated can see medicines.
#
# POST:
#   Pharmacy can add medicine.
# ============================================================

class MedicineListCreateView(generics.ListCreateAPIView):

    serializer_class = MedicineSerializer

    authentication_classes = [
        JWTAuthenticationFromCookie
    ]

    def get_permissions(self):

        if self.request.method == "POST":

            return [
                IsAuthenticated(),
                IsEmployee(),
            ]

        return [
            IsAuthenticated()
        ]

    def get_queryset(self):

        queryset = Medicine.objects.select_related(
            "pharmacy"
        ).all()

        # ----------------------------------------------------
        # Pharmacy sees its own medicines
        # ----------------------------------------------------

        if self.request.user.role == "pharmacy":

            return queryset.filter(
                pharmacy=self.request.user
            )

        # ----------------------------------------------------
        # Admin sees everything
        # ----------------------------------------------------

        if self.request.user.role == "admin":

            return queryset

        # ----------------------------------------------------
        # Patient sees medicines that are available
        # ----------------------------------------------------

        return queryset.filter(
            available_quantity__gt=0
        ).order_by(
            "medicine_name"
        )


# ============================================================
# MEDICINE DETAIL
#
# GET:
#   View medicine.
#
# PATCH / PUT:
#   Pharmacy can edit its own medicine.
#
# DELETE:
#   Pharmacy can delete its own medicine.
#   Admin can delete any medicine.
# ============================================================

class MedicineDetailView(
    generics.RetrieveUpdateDestroyAPIView
):

    serializer_class = MedicineSerializer

    authentication_classes = [
        JWTAuthenticationFromCookie
    ]

    def get_permissions(self):

        if self.request.method == "GET":

            return [
                IsAuthenticated()
            ]

        return [
            IsAuthenticated(),
            IsAdminOrEmployee()
        ]

    def get_queryset(self):

        return Medicine.objects.select_related(
            "pharmacy"
        ).all()

    def get_object(self):

        medicine = super().get_object()

        # ----------------------------------------------------
        # Admin can access everything
        # ----------------------------------------------------

        if self.request.user.role == "admin":

            return medicine

        # ----------------------------------------------------
        # Pharmacy can only access own medicines
        # ----------------------------------------------------

        if self.request.user.role == "pharmacy":

            if medicine.pharmacy_id != self.request.user.id:

                from rest_framework.exceptions import PermissionDenied

                raise PermissionDenied(
                    "You can only manage your own medicines."
                )

            return medicine

        # ----------------------------------------------------
        # Patient can read medicines
        # ----------------------------------------------------

        if self.request.method == "GET":

            return medicine

        from rest_framework.exceptions import PermissionDenied

        raise PermissionDenied(
            "Patients cannot modify medicines."
        )


# ============================================================
# MY MEDICINES
#
# Pharmacy can specifically get its own medicines.
# ============================================================

class MyMedicineListView(generics.ListAPIView):

    serializer_class = MedicineSerializer

    authentication_classes = [
        JWTAuthenticationFromCookie
    ]

    permission_classes = [
        IsAuthenticated,
        IsEmployee
    ]

    def get_queryset(self):

        return Medicine.objects.filter(
            pharmacy=self.request.user
        ).select_related(
            "pharmacy"
        )


# ============================================================
# PHARMACY LIST
#
# Useful if frontend wants to display pharmacy information.
# ============================================================

class PharmacyListView(generics.ListAPIView):

    serializer_class = PharmacySerializer

    authentication_classes = [
        JWTAuthenticationFromCookie
    ]

    permission_classes = [
        IsAuthenticated
    ]

    def get_queryset(self):

        from accounts.models import Users

        return Users.objects.filter(
            role="pharmacy",
            is_active=True
        ).order_by(
            "username"
        )


# ============================================================
# CREATE MEDICINE
#
# Pharmacy only.
#
# POST /medicines/create/
# ============================================================

class MedicineCreateView(
    generics.CreateAPIView
):

    serializer_class = MedicineSerializer

    authentication_classes = [
        JWTAuthenticationFromCookie
    ]

    permission_classes = [
        IsAuthenticated,
        IsEmployee
    ]


# ============================================================
# PATIENT ORDER LIST / CREATE
#
# GET:
#   Patient sees own orders.
#
# POST:
#   Patient creates order.
# ============================================================

class PatientOrderListCreateView(
    generics.ListCreateAPIView
):

    serializer_class = MedicineOrderSerializer

    authentication_classes = [
        JWTAuthenticationFromCookie
    ]

    permission_classes = [
        IsAuthenticated,
        IsUser
    ]

    def get_queryset(self):

        return MedicineOrder.objects.filter(
            patient=self.request.user
        ).select_related(
            "medicine",
            "pharmacy",
            "patient"
        )

    def perform_create(self, serializer):

        serializer.save(
            patient=self.request.user
        )


# ============================================================
# PATIENT ORDER DETAIL
#
# Patient can view their own order.
#
# No editing/deleting after order creation.
# ============================================================

class PatientOrderDetailView(
    generics.RetrieveAPIView
):

    serializer_class = MedicineOrderSerializer

    authentication_classes = [
        JWTAuthenticationFromCookie
    ]

    permission_classes = [
        IsAuthenticated,
        IsUser
    ]

    def get_queryset(self):

        return MedicineOrder.objects.filter(
            patient=self.request.user
        ).select_related(
            "medicine",
            "pharmacy",
            "patient"
        )


# ============================================================
# PHARMACY ORDER LIST
#
# Pharmacy sees orders belonging to its medicines.
# ============================================================

class PharmacyOrderListView(
    generics.ListAPIView
):

    serializer_class = MedicineOrderSerializer

    authentication_classes = [
        JWTAuthenticationFromCookie
    ]

    permission_classes = [
        IsAuthenticated,
        IsEmployee
    ]

    def get_queryset(self):

        return MedicineOrder.objects.filter(
            pharmacy=self.request.user
        ).select_related(
            "medicine",
            "patient",
            "pharmacy"
        )


# ============================================================
# ALL ORDERS FOR ADMIN
# ============================================================

class AdminOrderListView(
    generics.ListAPIView
):

    serializer_class = MedicineOrderSerializer

    authentication_classes = [
        JWTAuthenticationFromCookie
    ]

    permission_classes = [
        IsAuthenticated,
        IsAdmin
    ]

    def get_queryset(self):

        return MedicineOrder.objects.select_related(
            "medicine",
            "patient",
            "pharmacy"
        ).all()


# ============================================================
# PHARMACY ORDER DETAIL
#
# Pharmacy can view an order belonging to its pharmacy.
# ============================================================

class PharmacyOrderDetailView(
    generics.RetrieveAPIView
):

    serializer_class = MedicineOrderSerializer

    authentication_classes = [
        JWTAuthenticationFromCookie
    ]

    permission_classes = [
        IsAuthenticated,
        IsEmployee
    ]

    def get_queryset(self):

        return MedicineOrder.objects.filter(
            pharmacy=self.request.user
        ).select_related(
            "medicine",
            "patient",
            "pharmacy"
        )


# ============================================================
# APPROVE ORDER
#
# Pharmacy approves pending order.
#
# IMPORTANT:
# Stock is reduced here.
#
# Example:
#
# Available = 100
# Ordered = 5
#
# After approval:
#
# Available = 95
# ============================================================

class ApproveMedicineOrderView(
    APIView
):

    authentication_classes = [
        JWTAuthenticationFromCookie
    ]

    permission_classes = [
        IsAuthenticated,
        IsEmployee
    ]

    def post(
        self,
        request,
        pk
    ):

        with transaction.atomic():

            # Lock the order row
            order = get_object_or_404(
                MedicineOrder.objects.select_for_update().select_related(
                    "medicine",
                    "patient",
                    "pharmacy"
                ),
                pk=pk
            )

            # ------------------------------------------------
            # Make sure pharmacy owns this order
            # ------------------------------------------------

            if order.pharmacy_id != request.user.id:

                return Response(
                    {
                        "detail":
                            "You can only manage orders "
                            "for your pharmacy."
                    },
                    status=status.HTTP_403_FORBIDDEN
                )

            # ------------------------------------------------
            # Only pending orders can be approved
            # ------------------------------------------------

            if order.status != "pending":

                return Response(
                    {
                        "detail":
                            (
                                "Only pending orders can "
                                "be approved."
                            )
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # ------------------------------------------------
            # Lock medicine row
            # ------------------------------------------------

            medicine = Medicine.objects.select_for_update().get(
                pk=order.medicine_id
            )

            # ------------------------------------------------
            # Check stock
            # ------------------------------------------------

            if medicine.available_quantity < order.quantity:

                return Response(
                    {
                        "detail": (
                            f"Not enough stock. "
                            f"Available: "
                            f"{medicine.available_quantity}, "
                            f"Requested: "
                            f"{order.quantity}."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # ------------------------------------------------
            # SUBTRACT STOCK
            # ------------------------------------------------

            medicine.available_quantity -= order.quantity

            medicine.save(
                update_fields=[
                    "available_quantity",
                    "updated_at"
                ]
            )

            # ------------------------------------------------
            # Approve order
            # ------------------------------------------------

            order.status = "approved"

            order.denial_reason = None

            order.save(
                update_fields=[
                    "status",
                    "denial_reason",
                    "updated_at"
                ]
            )

        return Response(
            {
                "message":
                    "Order approved successfully.",
                "order":
                    MedicineOrderSerializer(
                        order,
                        context={
                            "request": request
                        }
                    ).data
            },
            status=status.HTTP_200_OK
        )


# ============================================================
# DENY ORDER
#
# Pharmacy can deny only pending orders.
# ============================================================

class DenyMedicineOrderView(
    APIView
):

    authentication_classes = [
        JWTAuthenticationFromCookie
    ]

    permission_classes = [
        IsAuthenticated,
        IsEmployee
    ]

    def post(
        self,
        request,
        pk
    ):

        order = get_object_or_404(
            MedicineOrder.objects.select_related(
                "medicine",
                "patient",
                "pharmacy"
            ),
            pk=pk
        )

        # ----------------------------------------------------
        # Check pharmacy ownership
        # ----------------------------------------------------

        if order.pharmacy_id != request.user.id:

            return Response(
                {
                    "detail":
                        "You can only manage orders "
                        "for your pharmacy."
                },
                status=status.HTTP_403_FORBIDDEN
            )

        # ----------------------------------------------------
        # Only pending orders can be denied
        # ----------------------------------------------------

        if order.status != "pending":

            return Response(
                {
                    "detail":
                        "Only pending orders can be denied."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # ----------------------------------------------------
        # Get denial reason
        # ----------------------------------------------------

        reason = request.data.get(
            "denial_reason",
            ""
        )

        order.status = "denied"

        order.denial_reason = reason

        order.save(
            update_fields=[
                "status",
                "denial_reason",
                "updated_at"
            ]
        )

        return Response(
            {
                "message":
                    "Order denied successfully.",

                "order":
                    MedicineOrderSerializer(
                        order,
                        context={
                            "request": request
                        }
                    ).data
            },
            status=status.HTTP_200_OK
        )


# ============================================================
# DELIVER ORDER
#
# Pharmacy marks approved order as delivered.
#
# IMPORTANT:
# Stock is NOT reduced here because it was already
# reduced during approval.
# ============================================================

class DeliverMedicineOrderView(
    APIView
):

    authentication_classes = [
        JWTAuthenticationFromCookie
    ]

    permission_classes = [
        IsAuthenticated,
        IsEmployee
    ]

    def post(
        self,
        request,
        pk
    ):

        order = get_object_or_404(
            MedicineOrder.objects.select_related(
                "medicine",
                "patient",
                "pharmacy"
            ),
            pk=pk
        )

        # ----------------------------------------------------
        # Check pharmacy ownership
        # ----------------------------------------------------

        if order.pharmacy_id != request.user.id:

            return Response(
                {
                    "detail":
                        "You can only manage orders "
                        "for your pharmacy."
                },
                status=status.HTTP_403_FORBIDDEN
            )

        # ----------------------------------------------------
        # Only approved orders can be delivered
        # ----------------------------------------------------

        if order.status != "approved":

            return Response(
                {
                    "detail":
                        (
                            "Only approved orders "
                            "can be marked as delivered."
                        )
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # ----------------------------------------------------
        # Mark delivered
        # ----------------------------------------------------

        order.status = "delivered"

        order.save(
            update_fields=[
                "status",
                "updated_at"
            ]
        )

        return Response(
            {
                "message":
                    "Order marked as delivered.",

                "order":
                    MedicineOrderSerializer(
                        order,
                        context={
                            "request": request
                        }
                    ).data
            },
            status=status.HTTP_200_OK
        )


# ============================================================
# PHARMACY ORDER STATUS
#
# One endpoint if you want to use:
#
# PATCH /orders/pharmacy/<id>/status/
#
# Example:
#
# {
#     "status": "approved"
# }
#
# or
#
# {
#     "status": "denied",
#     "denial_reason": "Prescription is invalid"
# }
#
# or
#
# {
#     "status": "delivered"
# }
#
# This is optional because the three dedicated endpoints
# above are safer and clearer.
# ============================================================

class PharmacyOrderStatusView(
    APIView
):

    authentication_classes = [
        JWTAuthenticationFromCookie
    ]

    permission_classes = [
        IsAuthenticated,
        IsEmployee
    ]

    def patch(
        self,
        request,
        pk
    ):

        new_status = request.data.get(
            "status"
        )

        if new_status not in [
            "approved",
            "denied",
            "delivered"
        ]:

            return Response(
                {
                    "detail":
                        (
                            "Status must be approved, "
                            "denied, or delivered."
                        )
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if new_status == "approved":

            view = ApproveMedicineOrderView()

            view.request = request

            return view.post(
                request,
                pk
            )

        if new_status == "denied":

            view = DenyMedicineOrderView()

            view.request = request

            return view.post(
                request,
                pk
            )

        if new_status == "delivered":

            view = DeliverMedicineOrderView()

            view.request = request

            return view.post(
                request,
                pk
            )


from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from accounts.views import JWTAuthenticationFromCookie
from accounts.permission import IsUser, IsEmployee

from .models import Report
from .serializers import ReportSerializer


# Pharmacy can see only reports created by that pharmacy
# Pharmacy can also create a report
class PharmacyReportListCreateView(generics.ListCreateAPIView):
    serializer_class = ReportSerializer
    authentication_classes = [
        JWTAuthenticationFromCookie
    ]
    permission_classes = [
        IsAuthenticated,
        IsEmployee
    ]

    def get_queryset(self):
        return Report.objects.filter(
        Q(
            pharmacy=self.request.user
        )
        |
        Q(
            pharmacy__isnull=True,
            patient__medicine_orders__pharmacy=self.request.user
        )
    ).select_related(
        "patient",
        "pharmacy"
    ).distinct()

    def perform_create(self, serializer):
        serializer.save(
            pharmacy=self.request.user
        )


# Pharmacy can view/update/delete only their own reports
class PharmacyReportDetailView(
    generics.RetrieveUpdateDestroyAPIView
):
    serializer_class = ReportSerializer
    authentication_classes = [
        JWTAuthenticationFromCookie
    ]
    permission_classes = [
        IsAuthenticated,
        IsEmployee
    ]

    def get_queryset(self):
        return Report.objects.filter(
        Q(
            pharmacy=self.request.user
        )
        |
        Q(
            pharmacy__isnull=True,
            patient__medicine_orders__pharmacy=self.request.user
        )
    ).select_related(
        "patient",
        "pharmacy"
    ).distinct()


# Patient can see only their own reports
class PatientReportListView(
    generics.ListCreateAPIView
):
    serializer_class = PatientReportSerializer

    authentication_classes = [
        JWTAuthenticationFromCookie
    ]

    permission_classes = [
        IsAuthenticated,
        IsUser
    ]

    def get_queryset(self):
        return Report.objects.filter(
            patient=self.request.user
        ).select_related(
            "patient",
            "pharmacy"
        )

    def perform_create(self, serializer):
        serializer.save(
            patient=self.request.user,
            pharmacy=None
        )


# Patient can view only their own report
class PatientReportDetailView(generics.RetrieveAPIView):
    serializer_class = ReportSerializer
    authentication_classes = [
        JWTAuthenticationFromCookie
    ]
    permission_classes = [
        IsAuthenticated,
        IsUser
    ]

    def get_queryset(self):
        return Report.objects.filter(
            patient=self.request.user
        ).select_related(
            "patient",
            "pharmacy"
        )