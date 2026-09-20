from django.urls import path

from . import views
from .views import (
    PharmacyReportListCreateView,
    PharmacyReportDetailView,
    PatientReportListView,
    PatientReportDetailView,
)


urlpatterns = [
    path(
        "pharmacy/reports/",
        PharmacyReportListCreateView.as_view(),
        name="pharmacy-report-list-create",
    ),

    path(
        "pharmacy/reports/<int:pk>/",
        PharmacyReportDetailView.as_view(),
        name="pharmacy-report-detail",
    ),

    # Patient
    path(
        "patient/reports/",
        PatientReportListView.as_view(),
        name="patient-report-list",
    ),

    path(
        "patient/reports/<int:pk>/",
        PatientReportDetailView.as_view(),
        name="patient-report-detail",
    ),

    # ========================================================
    # PHARMACIES
    # ========================================================

    path(
        "pharmacies/",
        views.PharmacyListView.as_view(),
        name="pharmacy-list"
    ),


    # ========================================================
    # MEDICINES
    # ========================================================

    # Patient:
    #   GET medicines
    #
    # Pharmacy:
    #   GET own medicines
    #   POST new medicine
    path(
        "medicines/",
        views.MedicineListCreateView.as_view(),
        name="medicine-list-create"
    ),

    # Pharmacy:
    #   POST medicine
    path(
        "medicines/create/",
        views.MedicineCreateView.as_view(),
        name="medicine-create"
    ),

    # Pharmacy:
    #   GET own medicines
    path(
        "medicines/my/",
        views.MyMedicineListView.as_view(),
        name="my-medicines"
    ),

    # GET / PATCH / PUT / DELETE
    path(
        "medicines/<int:pk>/",
        views.MedicineDetailView.as_view(),
        name="medicine-detail"
    ),


    # ========================================================
    # PATIENT ORDERS
    # ========================================================

    # GET:
    #   Patient's orders
    #
    # POST:
    #   Patient places order
    path(
        "orders/",
        views.PatientOrderListCreateView.as_view(),
        name="patient-orders"
    ),

    # Patient can view individual order
    path(
        "orders/<int:pk>/",
        views.PatientOrderDetailView.as_view(),
        name="patient-order-detail"
    ),


    # ========================================================
    # PHARMACY ORDERS
    # ========================================================

    # Pharmacy sees orders belonging to its pharmacy
    path(
        "pharmacy/orders/",
        views.PharmacyOrderListView.as_view(),
        name="pharmacy-orders"
    ),

    # Pharmacy views individual order
    path(
        "pharmacy/orders/<int:pk>/",
        views.PharmacyOrderDetailView.as_view(),
        name="pharmacy-order-detail"
    ),



    # Admin sees all orders
    path(
        "admin/orders/",
        views.AdminOrderListView.as_view(),
        name="admin-orders"
    ),


    # ========================================================
    # ORDER ACTIONS
    # ========================================================

    # Approve order
    path(
        "pharmacy/orders/<int:pk>/approve/",
        views.ApproveMedicineOrderView.as_view(),
        name="approve-medicine-order"
    ),

    # Deny order
    path(
        "pharmacy/orders/<int:pk>/deny/",
        views.DenyMedicineOrderView.as_view(),
        name="deny-medicine-order"
    ),

    # Mark as delivered
    path(
        "pharmacy/orders/<int:pk>/deliver/",
        views.DeliverMedicineOrderView.as_view(),
        name="deliver-medicine-order"
    ),

    # Optional combined status endpoint
    path(
        "pharmacy/orders/<int:pk>/status/",
        views.PharmacyOrderStatusView.as_view(),
        name="pharmacy-order-status"
    ),
]
