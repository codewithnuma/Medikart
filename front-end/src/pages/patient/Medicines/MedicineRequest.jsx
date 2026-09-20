import React, {
  useEffect,
  useState,
} from "react";

import {
  AlertCircle,
  ArrowLeft,
  CheckCircle2,
  Crosshair,
  FileImage,
  MapPin,
  Package,
  RefreshCw,
  ShieldCheck,
  Upload,
  X,
} from "lucide-react";

import {
  Link,
  useNavigate,
  useParams,
} from "react-router-dom";

import {
  getMedicine,
} from "../../../services/medicineApi";

import {
  createOrder,
} from "../../../services/orderApi";

import {
  getProfile,
} from "../../../services/profileApi";

import "./MedicineRequest.css";

const MedicineRequest = () => {
  const { id } = useParams();

  const navigate = useNavigate();

  const [medicine, setMedicine] =
    useState(null);

  const [quantity, setQuantity] =
    useState(1);

  const [contactPhone, setContactPhone] =
    useState("");

  const [
    deliveryAddress,
    setDeliveryAddress,
  ] = useState("");

  const [
    deliveryNote,
    setDeliveryNote,
  ] = useState("");

  const [
    prescriptionFile,
    setPrescriptionFile,
  ] = useState(null);

  const [
    prescriptionPreview,
    setPrescriptionPreview,
  ] = useState("");

  const [location, setLocation] =
    useState({
      latitude: "",
      longitude: "",
      accuracy: "",
    });

  const [
    locationLoading,
    setLocationLoading,
  ] = useState(false);

  const [loading, setLoading] =
    useState(true);

  const [submitting, setSubmitting] =
    useState(false);

  const [error, setError] =
    useState("");

  const [success, setSuccess] =
    useState("");

  useEffect(() => {
    const loadPage = async () => {
      try {
        setLoading(true);
        setError("");

        const [
          medicineResult,
          profileResult,
        ] = await Promise.allSettled([
          getMedicine(id),
          getProfile(),
        ]);

        if (
          medicineResult.status !==
          "fulfilled"
        ) {
          throw new Error(
            "Medicine could not be loaded."
          );
        }

        setMedicine(
          medicineResult.value.data
        );

        if (
          profileResult.status ===
          "fulfilled"
        ) {
          setContactPhone(
            profileResult.value.data
              ?.phone_number || ""
          );

          setDeliveryAddress(
            profileResult.value.data
              ?.location || ""
          );
        }
      } catch (err) {
        console.error(
          "Medicine request page error:",
          err
        );

        setError(
          "Could not prepare the medicine request."
        );
      } finally {
        setLoading(false);
      }
    };

    loadPage();
  }, [id]);

  const handlePrescription = (
    event
  ) => {
    const file =
      event.target.files?.[0];

    if (!file) {
      return;
    }

    if (
      !file.type.startsWith(
        "image/"
      )
    ) {
      setError(
        "Please upload an image file."
      );

      return;
    }

    setPrescriptionFile(file);

    setPrescriptionPreview(
      URL.createObjectURL(file)
    );

    setError("");
  };

  const removePrescription = () => {
    if (
      prescriptionPreview.startsWith(
        "blob:"
      )
    ) {
      URL.revokeObjectURL(
        prescriptionPreview
      );
    }

    setPrescriptionFile(null);
    setPrescriptionPreview("");
  };

  const captureLocation = () => {
    if (!navigator.geolocation) {
      setError(
        "Location is not supported by this browser."
      );

      return;
    }

    setLocationLoading(true);
    setError("");

    navigator.geolocation.getCurrentPosition(
      (position) => {
        setLocation({
          latitude:
            position.coords.latitude.toFixed(
              7
            ),

          longitude:
            position.coords.longitude.toFixed(
              7
            ),

          accuracy:
            position.coords.accuracy
              ? position.coords.accuracy.toFixed(
                  2
                )
              : "",
        });

        setLocationLoading(false);
      },

      (locationError) => {
        console.error(
          "Location error:",
          locationError
        );

        setLocationLoading(false);

        setError(
          "Location could not be captured. Please allow location access and try again."
        );
      },

      {
        enableHighAccuracy: true,
        timeout: 15000,
        maximumAge: 0,
      }
    );
  };

  const handleSubmit = async (
    event
  ) => {
    event.preventDefault();

    setError("");
    setSuccess("");

    if (!medicine) {
      setError(
        "Medicine information is unavailable."
      );

      return;
    }

    const numericQuantity =
      Number(quantity);

    if (
      !Number.isInteger(
        numericQuantity
      ) ||
      numericQuantity < 1
    ) {
      setError(
        "Quantity must be at least 1."
      );

      return;
    }

    if (
      numericQuantity >
      Number(
        medicine.available_quantity
      )
    ) {
      setError(
        "Requested quantity exceeds available stock."
      );

      return;
    }

    if (!contactPhone.trim()) {
      setError(
        "Please enter a contact phone number."
      );

      return;
    }

    if (!deliveryAddress.trim()) {
      setError(
        "Please enter a delivery address."
      );

      return;
    }

    if (
      !location.latitude ||
      !location.longitude
    ) {
      setError(
        "Please capture your delivery location before submitting."
      );

      return;
    }

    const formData =
      new FormData();

    formData.append(
      "medicine",
      medicine.id
    );

    formData.append(
      "quantity",
      numericQuantity
    );

    formData.append(
      "contact_phone",
      contactPhone.trim()
    );

    formData.append(
      "delivery_address",
      deliveryAddress.trim()
    );

    formData.append(
      "delivery_latitude",
      location.latitude
    );

    formData.append(
      "delivery_longitude",
      location.longitude
    );

    if (location.accuracy) {
      formData.append(
        "delivery_location_accuracy",
        location.accuracy
      );
    }

    if (deliveryNote.trim()) {
      formData.append(
        "delivery_note",
        deliveryNote.trim()
      );
    }

    if (prescriptionFile) {
      formData.append(
        "prescription_photo",
        prescriptionFile
      );
    }

    try {
      setSubmitting(true);

      const response =
        await createOrder(
          formData
        );

      setSuccess(
        `Request #${response.data.id} submitted for pharmacist review.`
      );

      setTimeout(() => {
        navigate(
          "/patient/orders"
        );
      }, 1200);
    } catch (err) {
      console.error(
        "Medicine order error:",
        err
      );

      const responseData =
        err.response?.data;

      if (
        responseData &&
        typeof responseData ===
          "object"
      ) {
        const firstValue =
          Object.values(
            responseData
          )[0];

        if (
          Array.isArray(firstValue)
        ) {
          setError(
            firstValue[0]
          );
        } else if (
          typeof firstValue ===
          "string"
        ) {
          setError(firstValue);
        } else {
          setError(
            "The request could not be submitted."
          );
        }
      } else {
        setError(
          "The request could not be submitted to the server."
        );
      }
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="medicine-request-loading">
        <RefreshCw
          size={28}
          className="medicine-request-spinner"
        />

        <span>
          Preparing request...
        </span>
      </div>
    );
  }

  if (!medicine) {
    return (
      <div className="medicine-request-empty">
        <AlertCircle size={34} />

        <strong>
          Medicine unavailable
        </strong>

        <span>
          {error}
        </span>

        <Link
          to="/patient/medicines"
          className="medicine-request-back-link"
        >
          <ArrowLeft size={16} />
          Back to medicines
        </Link>
      </div>
    );
  }

  const inStock =
    Number(
      medicine.available_quantity
    ) > 0;

  return (
    <div className="medicine-request-page">
      <Link
        to={`/patient/medicines/${medicine.id}`}
        className="medicine-request-back"
      >
        <ArrowLeft size={16} />
        Back to medicine
      </Link>

      <header className="medicine-request-header">
        <div>
          <span className="medicine-request-kicker">
            Pharmacy Request
          </span>

          <h1>
            Request Medicine
          </h1>

          <p>
            Submit your request for
            pharmacist review.
          </p>
        </div>
      </header>

      <form
        className="medicine-request-form"
        onSubmit={handleSubmit}
      >
        {/* MEDICINE */}

        <section className="medicine-request-panel">
          <div className="medicine-request-summary">
            <div className="medicine-request-icon">
              <Package size={23} />
            </div>

            <div>
              <span>
                Selected medicine
              </span>

              <h2>
                {
                  medicine.medicine_name
                }
              </h2>

              <p>
                {medicine.mg}
                {medicine.company_name
                  ? ` • ${medicine.company_name}`
                  : ""}
              </p>

              <p>
  Pharmacy:{" "}
  <strong>
    {medicine.pharmacy_name ||
      "Registered Pharmacy"}
  </strong>
</p>
            </div>

            <div className="medicine-request-stock">
              {
                medicine.available_quantity
              }{" "}
              available
            </div>
          </div>
        </section>

        {/* REQUEST DETAILS */}

        <section className="medicine-request-panel">
          <div className="medicine-request-panel-heading">
            <h2>
              Request details
            </h2>

            <p>
              Enter the amount and
              contact information.
            </p>
          </div>

          <div className="medicine-request-grid">
            <label className="medicine-request-field">
              <span>
                Quantity
              </span>

              <input
                type="number"
                min="1"
                max={
                  medicine.available_quantity
                }
                value={quantity}
                onChange={(event) =>
                  setQuantity(
                    event.target.value
                  )
                }
              />
            </label>

            <label className="medicine-request-field">
              <span>
                Contact phone
              </span>

              <input
                type="text"
                value={contactPhone}
                onChange={(event) =>
                  setContactPhone(
                    event.target.value
                  )
                }
                placeholder="Phone number"
              />
            </label>

            <label className="medicine-request-field medicine-request-full">
              <span>
                Delivery address
              </span>

              <textarea
                rows={3}
                value={
                  deliveryAddress
                }
                onChange={(event) =>
                  setDeliveryAddress(
                    event.target.value
                  )
                }
                placeholder="Enter delivery address"
              />
            </label>

            <label className="medicine-request-field medicine-request-full">
              <span>
                Delivery notes
                <small>
                  Optional
                </small>
              </span>

              <textarea
                rows={3}
                value={deliveryNote}
                onChange={(event) =>
                  setDeliveryNote(
                    event.target.value
                  )
                }
                placeholder="Landmark, floor, or other delivery information"
              />
            </label>
          </div>
        </section>

        {/* LOCATION */}

        <section className="medicine-request-panel">
          <div className="medicine-request-panel-heading">
            <h2>
              Delivery location
            </h2>

            <p>
              Your browser location is
              stored only with this
              request for delivery.
            </p>
          </div>

          <button
            type="button"
            className="medicine-location-button"
            onClick={captureLocation}
            disabled={locationLoading}
          >
            {locationLoading ? (
              <>
                <RefreshCw
                  size={17}
                  className="medicine-request-spinner"
                />

                Getting location...
              </>
            ) : (
              <>
                <Crosshair
                  size={17}
                />

                {location.latitude
                  ? "Update Delivery Location"
                  : "Use My Current Location"}
              </>
            )}
          </button>

          {location.latitude &&
            location.longitude && (
              <div className="medicine-location-result">
                <MapPin size={18} />

                <div>
                  <strong>
                    Location captured
                  </strong>

                  <span>
                    Latitude:{" "}
                    {location.latitude}
                  </span>

                  <span>
                    Longitude:{" "}
                    {
                      location.longitude
                    }
                  </span>

                  {location.accuracy && (
                    <span>
                      Accuracy: about{" "}
                      {
                        location.accuracy
                      }{" "}
                      meters
                    </span>
                  )}
                </div>
              </div>
            )}
        </section>

        {/* PRESCRIPTION */}

        <section className="medicine-request-panel">
          <div className="medicine-request-panel-heading">
            <h2>
              Prescription
            </h2>

            <p>
              Upload a prescription
              image when required for
              pharmacist review.
            </p>
          </div>

          {!prescriptionPreview ? (
            <label className="medicine-prescription-upload">
              <Upload size={24} />

              <strong>
                Upload prescription
              </strong>

              <span>
                Select an image from
                your device
              </span>

              <input
                type="file"
                accept="image/*"
                onChange={
                  handlePrescription
                }
                hidden
              />
            </label>
          ) : (
            <div className="medicine-prescription-preview">
              <img
                src={
                  prescriptionPreview
                }
                alt="Prescription preview"
              />

              <div>
                <span>
                  <FileImage
                    size={16}
                  />

                  {
                    prescriptionFile
                      ?.name
                  }
                </span>

                <button
                  type="button"
                  onClick={
                    removePrescription
                  }
                >
                  <X size={15} />
                  Remove
                </button>
              </div>
            </div>
          )}
        </section>

        {/* REVIEW NOTICE */}

        <div className="medicine-request-review">
          <ShieldCheck size={19} />

          <div>
            <strong>
              Pharmacy review required
            </strong>

            <span>
              Submitting this form creates
              a pending request. The
              pharmacy reviews it before
              approval.
            </span>
          </div>
        </div>

        {error && (
          <div className="medicine-request-message error">
            <AlertCircle
              size={18}
            />
            {error}
          </div>
        )}

        {success && (
          <div className="medicine-request-message success">
            <CheckCircle2
              size={18}
            />
            {success}
          </div>
        )}

        <button
          type="submit"
          className="medicine-submit-request"
          disabled={
            submitting ||
            !inStock
          }
        >
          {submitting ? (
            <>
              <RefreshCw
                size={17}
                className="medicine-request-spinner"
              />

              Submitting...
            </>
          ) : (
            "Submit for Pharmacy Review"
          )}
        </button>
      </form>
    </div>
  );
};

export default MedicineRequest;