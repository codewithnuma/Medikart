from django.contrib import admin
from django.utils.html import mark_safe

from .models import (
    Medicine,
    MedicineOrder,
    Report,
)


# ============================================================
# MEDICINE ADMIN
# ============================================================

@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):

    list_display = (
        "medicine_photo_preview",
        "medicine_name",
        "company_name",
        "mg",
        "available_quantity",
        "pharmacy",
        "created_at",
        "updated_at",
    )

    list_filter = (
        "company_name",
        "pharmacy",
        "created_at",
        "updated_at",
    )

    search_fields = (
        "medicine_name",
        "company_name",
        "mg",
        "pharmacy__username",
        "pharmacy__email",
    )

    readonly_fields = (
        "medicine_photo_preview",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            "Medicine Information",
            {
                "fields": (
                    "medicine_name",
                    "company_name",
                    "short_description",
                    "mg",
                    "available_quantity",
                )
            },
        ),
        (
            "Pharmacy",
            {
                "fields": (
                    "pharmacy",
                )
            },
        ),
        (
            "Medicine Photo",
            {
                "fields": (
                    "medicine_photo",
                    "medicine_photo_preview",
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

    ordering = (
        "-created_at",
    )

    @admin.display(description="Medicine Photo")
    def medicine_photo_preview(self, obj):

        if obj.medicine_photo:
            return mark_safe(
                f"""
                <img
                    src="{obj.medicine_photo.url}"
                    width="100"
                    height="100"
                    style="
                        object-fit: contain;
                        border-radius: 8px;
                        border: 1px solid #ddd;
                        background: #f8f8f8;
                    "
                />
                """
            )

        return "No image"


# ============================================================
# MEDICINE ORDER ADMIN
# ============================================================

@admin.register(MedicineOrder)
class MedicineOrderAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "patient",
        "medicine",
        "pharmacy",
        "mg",
        "quantity",
        "status",
        "prescription_preview",
        "delivery_location_display",
        "created_at",
        "updated_at",
    )

    list_filter = (
        "status",
        "pharmacy",
        "created_at",
        "updated_at",
    )

    search_fields = (
        "patient__username",
        "patient__email",
        "pharmacy__username",
        "pharmacy__email",
        "medicine__medicine_name",
        "medicine__company_name",
        "delivery_address",
    )

    readonly_fields = (
        "patient",
        "medicine",
        "pharmacy",
        "mg",
        "created_at",
        "updated_at",
        "prescription_preview",
        "delivery_location_display",
    )

    fieldsets = (
        (
            "Order Information",
            {
                "fields": (
                    "patient",
                    "medicine",
                    "pharmacy",
                    "mg",
                    "quantity",
                )
            },
        ),
        (
            "Prescription",
            {
                "fields": (
                    "prescription_photo",
                    "prescription_preview",
                )
            },
        ),
        (
            "Delivery Location",
            {
                "fields": (
                    "delivery_latitude",
                    "delivery_longitude",
                    "delivery_address",
                    "delivery_notes",
                    "delivery_location_accuracy",
                    "location_updated_at",
                    "delivery_location_display",
                )
            },
        ),
        (
            "Order Status",
            {
                "fields": (
                    "status",
                    "denial_reason",
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

    actions = (
        "approve_orders",
        "deny_orders",
        "mark_as_delivered",
    )

    ordering = (
        "-created_at",
    )

    @admin.display(description="Prescription")
    def prescription_preview(self, obj):

        if obj.prescription_photo:
            return mark_safe(
                f"""
                <img
                    src="{obj.prescription_photo.url}"
                    width="400"
                    style="
                        max-height: 300px;
                        object-fit: contain;
                        border: 1px solid #ddd;
                        border-radius: 8px;
                        background: #f8f8f8;
                    "
                />
                """
            )

        return "No prescription"

    @admin.display(description="Delivery Location")
    def delivery_location_display(self, obj):

        if (
            obj.delivery_latitude is not None
            and obj.delivery_longitude is not None
        ):

            latitude = obj.delivery_latitude
            longitude = obj.delivery_longitude

            map_url = (
                f"https://www.google.com/maps/search/"
                f"?api=1&query={latitude},{longitude}"
            )

            return mark_safe(
                f"""
                <a
                    href="{map_url}"
                    target="_blank"
                    rel="noopener noreferrer"
                >
                    View location on Google Maps
                </a>
                <br>
                <small>
                    Latitude: {latitude}<br>
                    Longitude: {longitude}
                </small>
                """
            )

        return "No GPS location"

    @admin.action(description="Approve selected orders")
    def approve_orders(self, request, queryset):

        updated = queryset.filter(
            status="pending"
        ).update(
            status="approved"
        )

        self.message_user(
            request,
            f"{updated} order(s) approved."
        )

    @admin.action(description="Deny selected orders")
    def deny_orders(self, request, queryset):

        updated = queryset.filter(
            status="pending"
        ).update(
            status="denied"
        )

        self.message_user(
            request,
            f"{updated} order(s) denied."
        )

    @admin.action(description="Mark selected orders as delivered")
    def mark_as_delivered(self, request, queryset):

        updated = queryset.filter(
            status="approved"
        ).update(
            status="delivered"
        )

        self.message_user(
            request,
            f"{updated} order(s) marked as delivered."
        )


# ============================================================
# REPORT ADMIN
# ============================================================

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "report_photo_preview",
        "report_name",
        "patient",
        "pharmacy",
        "date",
        "created_at",
        "updated_at",
    )

    list_filter = (
        "date",
        "pharmacy",
        "created_at",
        "updated_at",
    )

    search_fields = (
        "report_name",
        "patient__username",
        "patient__email",
        "pharmacy__username",
        "pharmacy__email",
    )

    readonly_fields = (
        "report_photo_preview",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            "Report Information",
            {
                "fields": (
                    "report_name",
                    "date",
                    "patient",
                    "pharmacy",
                )
            },
        ),
        (
            "Report Photo",
            {
                "fields": (
                    "photo",
                    "report_photo_preview",
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

    ordering = (
        "-date",
        "-created_at",
    )

    # --------------------------------------------------------
    # REPORT PHOTO PREVIEW
    # --------------------------------------------------------

    @admin.display(description="Report Photo")
    def report_photo_preview(self, obj):

        if obj.photo:

            return mark_safe(
                f"""
                <img
                    src="{obj.photo.url}"
                    width="400"
                    style="
                        max-height: 300px;
                        object-fit: contain;
                        border: 1px solid #ddd;
                        border-radius: 8px;
                        background: #f8f8f8;
                    "
                />
                """
            )

        return "No report photo"