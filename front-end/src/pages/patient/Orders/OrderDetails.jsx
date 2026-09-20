import React, {
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  AlertCircle,
  ArrowLeft,
  Building2,
  CheckCircle2,
  Clock3,
  FileImage,
  MapPin,
  PackageSearch,
  Phone,
  RefreshCw,
  Truck,
  XCircle,
} from "lucide-react";

import {
  Link,
  useParams,
} from "react-router-dom";

import {
  getPatientOrder,
} from "../../../services/orderApi";

import "./OrderDetails.css";

const OrderDetails = () => {
  const { id } = useParams();

  const [order, setOrder] =
    useState(null);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");

  const loadOrder = async () => {
    try {
      setLoading(true);
      setError("");

      const response =
        await getPatientOrder(id);

      setOrder(response.data);
    } catch (err) {
      console.error(
        "Order details API error:",
        err
      );

      setError(
        "Could not load this order."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadOrder();
  }, [id]);

  const timeline = useMemo(() => {
    const currentStatus =
      order?.status || "pending";

    const denied =
      currentStatus === "denied";

    const steps = [
      {
        key: "pending",
        label: "Requested",
        icon: Clock3,
      },
      {
        key: denied
          ? "denied"
          : "approved",
        label: denied
          ? "Denied"
          : "Approved",
        icon: denied
          ? XCircle
          : CheckCircle2,
      },
      {
        key: "delivered",
        label: "Delivered",
        icon: Truck,
      },
    ];

    const statusOrder = {
      pending: 0,
      approved: 1,
      denied: 1,
      delivered: 2,
    };

    const currentIndex =
      statusOrder[currentStatus] ?? 0;

    return steps.map(
      (step, index) => ({
        ...step,
        active:
          index <= currentIndex,
        current:
          step.key === currentStatus,
      })
    );
  }, [order]);

  if (loading) {
    return (
      <div className="order-detail-loading">
        <RefreshCw
          size={28}
          className="order-detail-spinner"
        />

        <span>
          Loading order...
        </span>
      </div>
    );
  }

  if (error || !order) {
    return (
      <div className="order-detail-error">
        <AlertCircle size={36} />

        <strong>
          Order unavailable
        </strong>

        <span>
          {error ||
            "This order could not be found."}
        </span>

        <Link
          to="/patient/orders"
          className="order-detail-back-link"
        >
          <ArrowLeft size={16} />
          Back to orders
        </Link>
      </div>
    );
  }

  return (
    <div className="order-detail-page">
      <Link
        to="/patient/orders"
        className="order-detail-back"
      >
        <ArrowLeft size={16} />
        Back to orders
      </Link>

      <header className="order-detail-header">
        <div>
          <span className="order-detail-kicker">
            Order Tracking
          </span>

          <h1>
            Order #{order.id}
          </h1>

          <p>
            Track your pharmacy request
            and delivery information.
          </p>
        </div>

        <span
          className={`order-detail-status ${order.status}`}
        >
          {order.status}
        </span>
      </header>

      {/* STATUS TIMELINE */}

      <section className="order-detail-panel">
        <div className="order-detail-section-heading">
          <h2>Order status</h2>

          <p>
            Current progress of this
            pharmacy request.
          </p>
        </div>

        <div className="order-status-timeline">
          {timeline.map(
            ({
              key,
              label,
              icon: Icon,
              active,
              current,
            }) => (
              <div
                key={key}
                className={`order-timeline-step ${
                  active
                    ? "active"
                    : ""
                } ${
                  current
                    ? "current"
                    : ""
                }`}
              >
                <div className="order-timeline-icon">
                  <Icon size={18} />
                </div>

                <span>{label}</span>
              </div>
            )
          )}
        </div>
      </section>

      <div className="order-detail-grid">
        {/* MEDICINE */}

        <section className="order-detail-panel">
          <div className="order-detail-section-heading">
            <h2>
              Medicine information
            </h2>
          </div>

          <div className="order-detail-info-list">
            <div>
              <span>Medicine</span>

              <strong>
                {order.medicine_name ||
                  "Medicine"}
              </strong>
            </div>

            <div>
              <span>Company</span>

              <strong>
                {order.company_name ||
                  "Not provided"}
              </strong>
            </div>

            <div>
              <span>Dosage</span>

              <strong>
                {order.mg ||
                  "Not provided"}
              </strong>
            </div>

            <div>
              <span>Quantity</span>

              <strong>
                {order.quantity}
              </strong>
            </div>
          </div>
        </section>

        {/* PHARMACY */}

        <section className="order-detail-panel">
          <div className="order-detail-section-heading">
            <h2>Pharmacy</h2>
          </div>

          <div className="order-pharmacy-summary">
            <div className="order-detail-icon">
              <Building2 size={21} />
            </div>

            <div>
              <strong>
                {order.pharmacy_name ||
                  "Registered Pharmacy"}
              </strong>

              {order.pharmacy_email && (
                <span>
                  {
                    order.pharmacy_email
                  }
                </span>
              )}
            </div>
          </div>
        </section>
      </div>

      {/* DELIVERY */}

      <section className="order-detail-panel">
        <div className="order-detail-section-heading">
          <h2>
            Delivery information
          </h2>

          <p>
            Delivery details submitted
            with this request.
          </p>
        </div>

        <div className="order-delivery-grid">
          <div>
            <MapPin size={17} />

            <section>
              <span>
                Delivery address
              </span>

              <strong>
                {order.delivery_address ||
                  "Not provided"}
              </strong>
            </section>
          </div>

          <div>
            <Phone size={17} />

            <section>
              <span>
                Contact phone
              </span>

              <strong>
                {order.contact_phone ||
                  "Not provided"}
              </strong>
            </section>
          </div>
        </div>

        {order.delivery_note && (
          <div className="order-detail-note">
            <span>
              Delivery notes
            </span>

            <p>
              {order.delivery_note}
            </p>
          </div>
        )}

        {order.delivery_latitude &&
          order.delivery_longitude && (
            <div className="order-location-card">
              <MapPin size={18} />

              <div>
                <strong>
                  Delivery location
                  captured
                </strong>

                <span>
                  Latitude:{" "}
                  {
                    order.delivery_latitude
                  }
                </span>

                <span>
                  Longitude:{" "}
                  {
                    order.delivery_longitude
                  }
                </span>

                {order.delivery_location_accuracy && (
                  <span>
                    Accuracy: about{" "}
                    {
                      order.delivery_location_accuracy
                    }{" "}
                    meters
                  </span>
                )}

                {order.location_updated_at && (
                  <span>
                    Captured:{" "}
                    {new Date(
                      order.location_updated_at
                    ).toLocaleString()}
                  </span>
                )}
              </div>
            </div>
          )}
      </section>

      {/* PRESCRIPTION */}

      {order.prescription_photo && (
        <section className="order-detail-panel">
          <div className="order-detail-section-heading">
            <h2>
              Prescription
            </h2>
          </div>

          <div className="order-prescription-card">
            <img
              src={
                order.prescription_photo
              }
              alt="Prescription"
            />

            <a
              href={
                order.prescription_photo
              }
              target="_blank"
              rel="noreferrer"
            >
              <FileImage size={16} />
              View prescription
            </a>
          </div>
        </section>
      )}

      {/* DENIAL */}

      {order.status === "denied" &&
        order.denial_reason && (
          <section className="order-denial-panel">
            <XCircle size={20} />

            <div>
              <strong>
                Request denied
              </strong>

              <span>
                {order.denial_reason}
              </span>
            </div>
          </section>
        )}

      {/* DATES */}

      <section className="order-detail-footer">
        <PackageSearch size={17} />

        <div>
          <span>
            Created:{" "}
            {order.created_at
              ? new Date(
                  order.created_at
                ).toLocaleString()
              : "Not available"}
          </span>

          {order.updated_at && (
            <span>
              Last updated:{" "}
              {new Date(
                order.updated_at
              ).toLocaleString()}
            </span>
          )}
        </div>
      </section>
    </div>
  );
};

export default OrderDetails;