import React, {
  useEffect,
  useState,
} from "react";

import {
  ArrowLeft,
  Building2,
  Mail,
  Package,
  Pill,
  RefreshCw,
  ShieldCheck,
} from "lucide-react";

import {
  Link,
  useParams,
} from "react-router-dom";

import {
  getMedicine,
} from "../../../services/medicineApi";

import "./MedicineDetails.css";

const MedicineDetails = () => {
  const { id } = useParams();

  const [medicine, setMedicine] =
    useState(null);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");

  const loadMedicine = async () => {
    try {
      setLoading(true);
      setError("");

      const response =
        await getMedicine(id);

      setMedicine(response.data);
    } catch (err) {
      console.error(
        "Medicine detail API error:",
        err
      );

      setError(
        "Could not load this medicine."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMedicine();
  }, [id]);

  if (loading) {
    return (
      <div className="medicine-detail-loading">
        <RefreshCw
          size={28}
          className="medicine-detail-spinner"
        />

        <span>
          Loading medicine...
        </span>
      </div>
    );
  }

  if (error || !medicine) {
    return (
      <div className="medicine-detail-error">
        <Pill size={34} />

        <strong>
          Medicine unavailable
        </strong>

        <span>
          {error ||
            "This medicine could not be found."}
        </span>

        <Link
          to="/patient/medicines"
          className="medicine-back-link"
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
    <div className="medicine-detail-page">
      <Link
        to="/patient/medicines"
        className="medicine-detail-back"
      >
        <ArrowLeft size={16} />
        Back to medicines
      </Link>

      <div className="medicine-detail-layout">
        <section className="medicine-detail-image-card">
          {medicine.medicine_photo ? (
            <img
              src={
                medicine.medicine_photo
              }
              alt={
                medicine.medicine_name
              }
            />
          ) : (
            <div className="medicine-detail-placeholder">
              <Pill size={58} />
            </div>
          )}
        </section>

        <section className="medicine-detail-content">
          <span className="medicine-detail-kicker">
            Medicine Information
          </span>

          <div className="medicine-detail-title-row">
            <div>
              <h1>
                {
                  medicine.medicine_name
                }
              </h1>

              <p>
                {medicine.company_name ||
                  "Company not provided"}
              </p>
            </div>

            {medicine.mg && (
              <span className="medicine-detail-dose">
                {medicine.mg}
              </span>
            )}
          </div>

          <div
            className={`medicine-detail-stock ${
              inStock
                ? "available"
                : "unavailable"
            }`}
          >
            <Package size={17} />

            <span>
              {inStock
                ? `${medicine.available_quantity} available`
                : "Out of stock"}
            </span>
          </div>

          <div className="medicine-detail-section">
            <h2>Description</h2>

            <p>
              {medicine.short_description ||
                "No description has been provided for this medicine."}
            </p>
          </div>

          <div className="medicine-detail-section">
            <h2>
              Pharmacy
            </h2>

            <div className="medicine-pharmacy-card">
              <div className="medicine-pharmacy-icon">
                <Building2
                  size={22}
                />
              </div>

              <div className="medicine-pharmacy-info">
                <strong>
                  {medicine.pharmacy_name ||
                    "Registered Pharmacy"}
                </strong>

                {medicine.pharmacy_email && (
                  <span>
                    <Mail
                      size={14}
                    />

                    {
                      medicine.pharmacy_email
                    }
                  </span>
                )}
              </div>
            </div>
          </div>

          <div className="medicine-review-notice">
            <ShieldCheck
              size={18}
            />

            <div>
              <strong>
                Pharmacist review
              </strong>

              <span>
                Medicine requests are
                reviewed by the pharmacy
                before approval.
              </span>
            </div>
          </div>

          {inStock ? (
  <Link
    to={`/patient/medicines/${medicine.id}/request`}
    className="medicine-request-button"
  >
    Request Medicine
  </Link>
) : (
  <button
    type="button"
    className="medicine-request-button"
    disabled
  >
    Currently Unavailable
  </button>
)}
        </section>
      </div>
    </div>
  );
};

export default MedicineDetails;