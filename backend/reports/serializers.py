from rest_framework import serializers
from django.utils import timezone
from .models import Medicine, MedicineOrder
from accounts.models import Users
from django.core.exceptions import ObjectDoesNotExist


# ============================================================
# PHARMACY SERIALIZER
# ============================================================

class PharmacySerializer(serializers.ModelSerializer):

    phone_number = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()
    bio = serializers.SerializerMethodField()
    profile_image_url = serializers.SerializerMethodField()

    class Meta:
        model = Users

        fields = [
            "id",
            "username",
            "email",
            "phone_number",
            "location",
            "bio",
            "profile_image_url",
        ]

    def get_profile(self, obj):
        try:
            return obj.profile
        except ObjectDoesNotExist:
            return None

    def get_phone_number(self, obj):
        profile = self.get_profile(obj)

        if not profile:
            return None

        return profile.phone_number

    def get_location(self, obj):
        profile = self.get_profile(obj)

        if not profile:
            return None

        return profile.location

    def get_bio(self, obj):
        profile = self.get_profile(obj)

        if not profile:
            return None

        return profile.bio

    def get_profile_image_url(self, obj):
        profile = self.get_profile(obj)

        if (
            not profile
            or not profile.profile_image
        ):
            return None

        request = self.context.get("request")

        if request:
            return request.build_absolute_uri(
                profile.profile_image.url
            )

        return profile.profile_image.url


# ============================================================
# MEDICINE SERIALIZER
# ============================================================

class MedicineSerializer(serializers.ModelSerializer):

    # ========================================================
    # PHARMACY INFORMATION
    # ========================================================

    pharmacy_name = serializers.CharField(
        source="pharmacy.username",
        read_only=True
    )

    pharmacy_email = serializers.EmailField(
        source="pharmacy.email",
        read_only=True
    )

    class Meta:

        model = Medicine

        fields = [
            "id",

            # Medicine
            "medicine_name",
            "company_name",
            "short_description",
            "mg",

            # Stock
            "available_quantity",

            # Photo
            "medicine_photo",

            # Pharmacy
            "pharmacy",
            "pharmacy_name",
            "pharmacy_email",

            # Dates
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",

            "pharmacy",
            "pharmacy_name",
            "pharmacy_email",

            "created_at",
            "updated_at",
        ]

    # ========================================================
    # VALIDATE MEDICINE
    # ========================================================

    def validate(self, attrs):

        request = self.context.get("request")

        if not request:
            raise serializers.ValidationError(
                "Request context is required."
            )

        user = request.user

        if not user.is_authenticated:
            raise serializers.ValidationError(
                "Authentication is required."
            )

        # ----------------------------------------------------
        # Only pharmacy can add/edit medicine
        # ----------------------------------------------------

        if user.role.lower() != "pharmacy":

            raise serializers.ValidationError(
                "Only pharmacy users can manage medicines."
            )

        # ----------------------------------------------------
        # Available quantity
        # ----------------------------------------------------

        available_quantity = attrs.get(
            "available_quantity"
        )

        if available_quantity is not None:

            if available_quantity < 0:

                raise serializers.ValidationError({
                    "available_quantity":
                        "Available quantity cannot be negative."
                })

        return attrs

    # ========================================================
    # CREATE MEDICINE
    # ========================================================

    def create(self, validated_data):

        request = self.context.get("request")

        if not request or not request.user.is_authenticated:

            raise serializers.ValidationError(
                "Authentication is required."
            )

        user = request.user

        # Only pharmacy can create medicine
        if user.role.lower() != "pharmacy":

            raise serializers.ValidationError(
                "Only pharmacy users can add medicines."
            )

        # Automatically assign pharmacy
        validated_data["pharmacy"] = user

        return Medicine.objects.create(
            **validated_data
        )

    # ========================================================
    # UPDATE MEDICINE
    # ========================================================

    def update(
        self,
        instance,
        validated_data
    ):

        request = self.context.get("request")

        if not request or not request.user.is_authenticated:

            raise serializers.ValidationError(
                "Authentication is required."
            )

        user = request.user

        # ----------------------------------------------------
        # Pharmacy can only edit its own medicine
        # ----------------------------------------------------

        if user.role.lower() == "pharmacy":

            if instance.pharmacy_id != user.id:

                raise serializers.ValidationError(
                    "You can only edit your own medicines."
                )

        elif user.role.lower() == "admin":

            pass

        else:

            raise serializers.ValidationError(
                "You do not have permission to edit medicines."
            )

        # ----------------------------------------------------
        # Never allow pharmacy to change owner
        # ----------------------------------------------------

        validated_data.pop(
            "pharmacy",
            None
        )

        return super().update(
            instance,
            validated_data
        )


# ============================================================
# MEDICINE ORDER SERIALIZER
# ============================================================

class MedicineOrderSerializer(
    serializers.ModelSerializer
):

    # ========================================================
    # PATIENT INFORMATION
    # ========================================================

    patient_name = serializers.CharField(
        source="patient.username",
        read_only=True
    )

    patient_email = serializers.EmailField(
        source="patient.email",
        read_only=True
    )

    # ========================================================
    # MEDICINE INFORMATION
    # ========================================================

    medicine_name = serializers.CharField(
        source="medicine.medicine_name",
        read_only=True
    )

    company_name = serializers.CharField(
        source="medicine.company_name",
        read_only=True
    )

    # ========================================================
    # PHARMACY INFORMATION
    # ========================================================

    pharmacy_name = serializers.CharField(
        source="pharmacy.username",
        read_only=True
    )

    pharmacy_email = serializers.EmailField(
        source="pharmacy.email",
        read_only=True
    )

    # ========================================================
    # CURRENT AVAILABLE STOCK
    # ========================================================

    available_quantity = serializers.IntegerField(
        source="medicine.available_quantity",
        read_only=True
    )

    # ========================================================
    # DELIVERY LOCATION
    # ========================================================

    delivery_latitude = serializers.DecimalField(
        max_digits=10,
        decimal_places=7,
        required=True
    )

    delivery_longitude = serializers.DecimalField(
        max_digits=10,
        decimal_places=7,
        required=True
    )

    delivery_address = serializers.CharField(
        required=True,
        allow_blank=False
    )
    
    delivery_location_accuracy = serializers.DecimalField(
    max_digits=10,
    decimal_places=2,
    required=False,
    allow_null=True
)

    # ========================================================
    # DELIVERY CONTACT
    # ========================================================

    contact_phone = serializers.CharField(
        required=True,
        allow_blank=False,
        max_length=20
    )

    # ========================================================
    # DELIVERY NOTE
    # ========================================================

    delivery_note = serializers.CharField(
    source="delivery_notes",
    required=False,
    allow_blank=True,
    allow_null=True
    )

    # ========================================================
    # META
    # ========================================================

    class Meta:

        model = MedicineOrder

        fields = [

            "id",

            # ------------------------------------------------
            # Patient
            # ------------------------------------------------

            "patient",
            "patient_name",
            "patient_email",

            # ------------------------------------------------
            # Medicine
            # ------------------------------------------------

            "medicine",
            "medicine_name",
            "company_name",

            # ------------------------------------------------
            # Pharmacy
            # ------------------------------------------------

            "pharmacy",
            "pharmacy_name",
            "pharmacy_email",

            # ------------------------------------------------
            # Medicine strength
            # ------------------------------------------------

            "mg",

            # ------------------------------------------------
            # Stock
            # ------------------------------------------------

            "available_quantity",

            # ------------------------------------------------
            # Order quantity
            # ------------------------------------------------

            "quantity",

            # ------------------------------------------------
            # Prescription
            # ------------------------------------------------

            "prescription_photo",

            # ------------------------------------------------
            # DELIVERY LOCATION
            # ------------------------------------------------

            "delivery_latitude",
            "delivery_longitude",
            "delivery_address",
            "delivery_location_accuracy",
            "location_updated_at",

            # ------------------------------------------------
            # DELIVERY CONTACT
            # ------------------------------------------------

            "contact_phone",

            # ------------------------------------------------
            # DELIVERY NOTE
            # ------------------------------------------------

            "delivery_note",

            # ------------------------------------------------
            # Status
            # ------------------------------------------------

            "status",

            # ------------------------------------------------
            # Denial reason
            # ------------------------------------------------

            "denial_reason",

            # ------------------------------------------------
            # Dates
            # ------------------------------------------------

            "created_at",
            "updated_at",
        ]

        read_only_fields = [

            "id",
            "location_updated_at",
            # ------------------------------------------------
            # Patient is automatically assigned
            # ------------------------------------------------

            "patient",
            "patient_name",
            "patient_email",

            # ------------------------------------------------
            # Automatically obtained from medicine
            # ------------------------------------------------

            "medicine_name",
            "company_name",

            # ------------------------------------------------
            # Automatically obtained from medicine
            # ------------------------------------------------

            "pharmacy",
            "pharmacy_name",
            "pharmacy_email",

            # ------------------------------------------------
            # Automatically obtained from medicine
            # ------------------------------------------------

            "mg",

            # ------------------------------------------------
            # Current stock
            # ------------------------------------------------

            "available_quantity",

            # ------------------------------------------------
            # Patient cannot decide status
            # ------------------------------------------------

            "status",
            "denial_reason",

            # ------------------------------------------------
            # Dates
            # ------------------------------------------------

            "created_at",
            "updated_at",
        ]

    # ========================================================
    # VALIDATE MEDICINE
    # ========================================================

    def validate_medicine(
        self,
        medicine
    ):

        request = self.context.get(
            "request"
        )

        if not request:

            raise serializers.ValidationError(
                "Request context is required."
            )

        user = request.user

        if not user.is_authenticated:

            raise serializers.ValidationError(
                "Authentication is required."
            )

        # ----------------------------------------------------
        # Only patients can place orders
        # ----------------------------------------------------

        if user.role.lower() != "patient":

            raise serializers.ValidationError(
                "Only patients can place medicine orders."
            )

        # ----------------------------------------------------
        # Medicine must have stock
        # ----------------------------------------------------

        if medicine.available_quantity <= 0:

            raise serializers.ValidationError(
                "This medicine is currently out of stock."
            )

        return medicine

    # ========================================================
    # VALIDATE ORDER
    # ========================================================

    def validate(
        self,
        attrs
    ):

        medicine = attrs.get(
            "medicine"
        )

        quantity = attrs.get(
            "quantity"
        )

        # ----------------------------------------------------
        # Medicine
        # ----------------------------------------------------

        if not medicine:

            raise serializers.ValidationError({
                "medicine":
                    "Medicine is required."
            })

        # ----------------------------------------------------
        # Quantity
        # ----------------------------------------------------

        if quantity is None:

            raise serializers.ValidationError({
                "quantity":
                    "Quantity is required."
            })

        if quantity <= 0:

            raise serializers.ValidationError({
                "quantity":
                    "Quantity must be greater than zero."
            })

        # ----------------------------------------------------
        # Check stock
        # ----------------------------------------------------

        if quantity > medicine.available_quantity:

            raise serializers.ValidationError({
                "quantity": (
                    f"Only "
                    f"{medicine.available_quantity} "
                    f"units are available."
                )
            })

        # ====================================================
        # VALIDATE GPS COORDINATES
        # ====================================================

        latitude = attrs.get(
            "delivery_latitude"
        )

        longitude = attrs.get(
            "delivery_longitude"
        )

        # ----------------------------------------------------
        # Latitude range
        # ----------------------------------------------------

        if latitude is not None:

            if latitude < -90 or latitude > 90:

                raise serializers.ValidationError({
                    "delivery_latitude":
                        "Latitude must be between -90 and 90."
                })

        # ----------------------------------------------------
        # Longitude range
        # ----------------------------------------------------

        if longitude is not None:

            if longitude < -180 or longitude > 180:

                raise serializers.ValidationError({
                    "delivery_longitude":
                        "Longitude must be between -180 and 180."
                })

        # ----------------------------------------------------
        # Require both GPS coordinates together
        # ----------------------------------------------------

        if latitude is None or longitude is None:

            raise serializers.ValidationError({
                "delivery_location":
                    "Delivery GPS location is required."
            })

        # ====================================================
        # DELIVERY ADDRESS
        # ====================================================

        delivery_address = attrs.get(
            "delivery_address"
        )

        if not delivery_address:

            raise serializers.ValidationError({
                "delivery_address":
                    "Delivery address is required."
            })

        # ====================================================
        # CONTACT PHONE
        # ====================================================

        contact_phone = attrs.get(
            "contact_phone"
        )

        if not contact_phone:

            raise serializers.ValidationError({
                "contact_phone":
                    "Contact phone number is required."
            })

        # ====================================================
        # MG
        #
        # Never trust frontend MG.
        # ====================================================

        attrs["mg"] = medicine.mg

        return attrs

    # ========================================================
    # CREATE ORDER
    # ========================================================

    def create(
        self,
        validated_data
    ):

        request = self.context.get(
            "request"
        )

        if not request or not request.user.is_authenticated:

            raise serializers.ValidationError(
                "Authentication is required."
            )

        patient = request.user

        # ----------------------------------------------------
        # Only patients can create orders
        # ----------------------------------------------------

        if patient.role.lower() != "patient":

            raise serializers.ValidationError(
                "Only patients can place medicine orders."
            )

        # ----------------------------------------------------
        # Get medicine
        # ----------------------------------------------------

        medicine = validated_data.get(
            "medicine"
        )

        # ----------------------------------------------------
        # Automatically get pharmacy
        # ----------------------------------------------------

        pharmacy = medicine.pharmacy

        # ----------------------------------------------------
        # Automatically get MG
        # ----------------------------------------------------

        validated_data["mg"] = medicine.mg
        validated_data["location_updated_at"] = timezone.now()

        # ----------------------------------------------------
        # Automatically assign patient and pharmacy
        # ----------------------------------------------------

        order = MedicineOrder.objects.create(

            patient=patient,

            medicine=medicine,

            pharmacy=pharmacy,

            **{
                key: value
                for key, value in validated_data.items()
                if key not in [
                    "medicine",
                    "patient",
                    "pharmacy",
                ]
            }
        )

        return order
    



from .models import Report


class ReportSerializer(serializers.ModelSerializer):
    pharmacy_name = serializers.CharField(
        source="pharmacy.username",
        read_only=True
    )

    patient_name = serializers.CharField(
        source="patient.username",
        read_only=True
    )

    class Meta:
        model = Report

        fields = [
            "id",
            "report_name",
            "date",
            "photo",
            "patient",
            "patient_name",
            "pharmacy",
            "pharmacy_name",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "pharmacy",
            "pharmacy_name",
            "patient_name",
            "created_at",
            "updated_at",
        ]

    def validate_patient(self, patient):
        if patient.role != "patient":
            raise serializers.ValidationError(
                "Selected user must be a patient."
            )
            


        return patient
    
class PatientReportSerializer(ReportSerializer):

    class Meta(ReportSerializer.Meta):

        read_only_fields = [
            "id",
            "patient",
            "patient_name",
            "pharmacy",
            "pharmacy_name",
            "created_at",
            "updated_at",
        ]