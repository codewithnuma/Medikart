from django.db import models
from django.conf import settings
from django.utils import timezone
from uuid import uuid4

import os


# ============================================================
# MEDICINE PHOTO UPLOAD PATH
# ============================================================

def medicine_photo_path(instance, filename):
    """
    Store medicine photos inside:

    media/medicines/<pharmacy_id>/<unique-file-name>
    """

    ext = filename.split(".")[-1]

    filename = f"{uuid4().hex}.{ext}"

    # If pharmacy exists
    pharmacy_id = (
        instance.pharmacy.id
        if instance.pharmacy
        else "unknown"
    )

    return os.path.join(
        "medicines",
        str(pharmacy_id),
        filename
    )


# ============================================================
# MEDICINE
# ============================================================

class Medicine(models.Model):

    # ========================================================
    # MEDICINE INFORMATION
    # ========================================================

    medicine_name = models.CharField(
        max_length=255
    )

    company_name = models.CharField(
        max_length=255
    )

    short_description = models.TextField(
        blank=True,
        null=True
    )

    # Example:
    # 500mg
    # 250mg
    # 10ml

    mg = models.CharField(
        max_length=50
    )

    # ========================================================
    # AVAILABLE STOCK
    # ========================================================

    available_quantity = models.PositiveIntegerField(
        default=0
    )

    # ========================================================
    # PHARMACY
    #
    # The pharmacy that owns/stores this medicine.
    # ========================================================

    pharmacy = models.ForeignKey(
    settings.AUTH_USER_MODEL,
    on_delete=models.CASCADE,
    related_name="medicines",
    limit_choices_to={"role": "pharmacy"},
)

    # ========================================================
    # MEDICINE PHOTO
    # ========================================================

    medicine_photo = models.ImageField(
        upload_to=medicine_photo_path,
        blank=True,
        null=True
    )

    # ========================================================
    # DATES
    # ========================================================

    created_at = models.DateTimeField(
        default=timezone.now
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    # ========================================================
    # PHARMACY NAME
    # ========================================================

    @property
    def pharmacy_name(self):
        """
        Returns the pharmacy username.
        """

        return self.pharmacy.username

    # ========================================================
    # STRING REPRESENTATION
    # ========================================================

    def __str__(self):

        return (
            f"{self.medicine_name} "
            f"- {self.mg} "
            f"- {self.pharmacy.username} "
            f"- Stock: {self.available_quantity}"
        )

    class Meta:

        ordering = [
            "-created_at"
        ]


# ============================================================
# PRESCRIPTION PHOTO UPLOAD PATH
# ============================================================

def prescription_photo_path(instance, filename):
    """
    Store prescription photos inside:

    media/prescriptions/<patient_id>/<unique-file-name>
    """

    ext = filename.split(".")[-1]

    filename = f"{uuid4().hex}.{ext}"

    patient_id = (
        instance.patient.id
        if instance.patient
        else "unknown"
    )

    return os.path.join(
        "prescriptions",
        str(patient_id),
        filename
    )


# ============================================================
# MEDICINE ORDER
# ============================================================

from django.conf import settings
from django.db import models
from django.utils import timezone


class MedicineOrder(models.Model):

    # ========================================================
    # ORDER STATUS
    # ========================================================

    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("denied", "Denied"),
        ("delivered", "Delivered"),
    )

    # ========================================================
    # PATIENT
    # ========================================================

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="medicine_orders",
        limit_choices_to={
            "role": "patient"
        }
    )

    # ========================================================
    # MEDICINE
    # ========================================================

    medicine = models.ForeignKey(
        Medicine,
        on_delete=models.CASCADE,
        related_name="orders"
    )

    # ========================================================
    # PHARMACY
    #
    # Automatically taken from medicine.
    # Patient does NOT choose this directly.
    # ========================================================

    pharmacy = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="pharmacy_orders",
        limit_choices_to={
            "role": "pharmacy"
        }
    )

    # ========================================================
    # MG / STRENGTH
    #
    # Automatically copied from Medicine.
    # ========================================================

    mg = models.CharField(
        max_length=50
    )

    # ========================================================
    # ORDER QUANTITY
    # ========================================================

    quantity = models.PositiveIntegerField(
        default=1
    )

    # ========================================================
    # DOCTOR PRESCRIPTION
    # ========================================================

    prescription_photo = models.ImageField(
        upload_to=prescription_photo_path,
        blank=True,
        null=True
    )

    # ========================================================
    # DELIVERY LOCATION
    #
    # GPS coordinates selected by patient from frontend.
    # These coordinates are stored for THIS ORDER.
    # ========================================================

    delivery_latitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True
    )

    delivery_longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True
    )

    # Human-readable address obtained/displayed by frontend
    # or generated through reverse geocoding.

    delivery_address = models.TextField(
        blank=True,
        null=True
    )
    
    contact_phone = models.CharField(
    max_length=20,
    blank=True,
    null=True
)
    # Optional landmark, floor, apartment number, etc.

    delivery_notes = models.TextField(
        blank=True,
        null=True
    )

    # GPS accuracy in meters, if the browser provides it.

    delivery_location_accuracy = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    # Time when GPS location was captured.

    location_updated_at = models.DateTimeField(
        null=True,
        blank=True
    )

    # ========================================================
    # ORDER STATUS
    # ========================================================

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

    # ========================================================
    # DENIAL REASON
    # ========================================================

    denial_reason = models.TextField(
        blank=True,
        null=True
    )

    # ========================================================
    # DATES
    # ========================================================

    created_at = models.DateTimeField(
        default=timezone.now
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    # ========================================================
    # SAVE
    # ========================================================

    def save(
        self,
        *args,
        **kwargs
    ):
        """
        Automatically set:

        1. Pharmacy from medicine
        2. MG from medicine
        """

        if self.medicine:

            # Automatically assign pharmacy
            self.pharmacy = (
                self.medicine.pharmacy
            )

            # Automatically assign medicine strength
            self.mg = (
                self.medicine.mg
            )

        super().save(
            *args,
            **kwargs
        )

    # ========================================================
    # STRING REPRESENTATION
    # ========================================================

    def __str__(self):

        return (
            f"{self.patient.username} - "
            f"{self.medicine.medicine_name} - "
            f"{self.quantity} units - "
            f"{self.pharmacy.username} - "
            f"{self.status}"
        )

    # ========================================================
    # META
    # ========================================================

    class Meta:

        ordering = [
            "-created_at"
        ]

import os
from uuid import uuid4

from django.conf import settings
from django.db import models
from django.utils import timezone


def report_photo_path(instance, filename):
    ext = filename.split(".")[-1]
    filename = f"{uuid4().hex}.{ext}"

    patient_id = (
        instance.patient.id
        if instance.patient
        else "unknown"
    )

    return os.path.join(
        "reports",
        str(patient_id),
        filename
    )


class Report(models.Model):

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reports",
        limit_choices_to={"role": "patient"},
    )

    report_name = models.CharField(
        max_length=255
    )

    date = models.DateField(
        default=timezone.now
    )

    photo = models.ImageField(
        upload_to=report_photo_path,
        blank=True,
        null=True
    )

    pharmacy = models.ForeignKey(
    settings.AUTH_USER_MODEL,
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name="pharmacy_reports",
    limit_choices_to={"role": "pharmacy"},
)

    created_at = models.DateTimeField(
        default=timezone.now
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    @property
    def pharmacy_name(self):
        return self.pharmacy.username

    def __str__(self):
        pharmacy_name = (
        self.pharmacy.username
            if self.pharmacy
            else "No Pharmacy"
    )

        return (
        f"{self.report_name} - "
        f"{self.patient.username} - "
        f"{pharmacy_name}"
    )

    class Meta:
        ordering = [
            "-date",
            "-created_at",
        ]