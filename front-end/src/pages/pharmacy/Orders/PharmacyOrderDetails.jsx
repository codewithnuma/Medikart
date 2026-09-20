import React, {
  useEffect,
  useState,
} from "react";

import {
  AlertCircle,
  ArrowLeft,
  CheckCircle2,
  Clock3,
  FileImage,
  Mail,
  MapPin,
  Package,
  Phone,
  RefreshCw,
  Truck,
  User,
  XCircle,
} from "lucide-react";

import {
  Link,
  useParams,
} from "react-router-dom";

import {
  approveOrder,
  denyOrder,
  getPharmacyOrder,
  markOrderDelivered,
} from "../../../services/orderApi";

import "./PharmacyOrderDetails.css";

const PharmacyOrderDetails = () => {
  const { id } = useParams();

  const [order, setOrder] =
    useState(null);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");
    const [
  actionLoading,
  setActionLoading,
] = useState("");

const [
  actionError,
  setActionError,
] = useState("");

const [
  denialReason,
  setDenialReason,
] = useState("");

  const loadOrder = async () => {
    try {
      setLoading(true);
      setError("");

      const response =
        await getPharmacyOrder(id);

      setOrder(response.data);
    } catch (err) {
      console.error(
        "Pharmacy order details error:",
        err
      );

      setError(
        "Could not load this order."
      );
    } finally {
      setLoading(false);
    }
  };
    const handleApproveOrder = async () => {
  const confirmed = window.confirm(
    "Approve this medicine request?"
  );

  if (!confirmed) {
    return;
  }

  try {
    setActionLoading("approve");
    setActionError("");

    await approveOrder(id);

    await loadOrder();
  } catch (err) {
    console.error(
      "Approve order error:",
      err
    );

    setActionError(
      err.response?.data?.detail ||
        "Could not approve this order."
    );
  } finally {
    setActionLoading("");
  }
};

const handleDenyOrder = async () => {
  const reason =
    denialReason.trim();

  if (!reason) {
    setActionError(
      "Please enter a reason before denying this order."
    );

    return;
  }

  const confirmed = window.confirm(
    "Deny this medicine request?"
  );

  if (!confirmed) {
    return;
  }

  try {
    setActionLoading("deny");
    setActionError("");

    await denyOrder(
      id,
      reason
    );

    setDenialReason("");

    await loadOrder();
  } catch (err) {
    console.error(
      "Deny order error:",
      err
    );

    setActionError(
      err.response?.data?.detail ||
        "Could not deny this order."
    );
  } finally {
    setActionLoading("");
  }
};

const handleMarkDelivered = async () => {
  const confirmed = window.confirm(
    "Mark this order as delivered?"
  );

  if (!confirmed) {
    return;
  }

  try {
    setActionLoading("deliver");
    setActionError("");

    await markOrderDelivered(id);

    await loadOrder();
  } catch (err) {
    console.error(
      "Mark delivered error:",
      err
    );

    setActionError(
      err.response?.data?.detail ||
        "Could not mark this order as delivered."
    );
  } finally {
    setActionLoading("");
  }
};
  useEffect(() => {
    loadOrder();
  }, [id]);

  const getStatusIcon = (
    status
  ) => {
    switch (status) {
      case "approved":
        return (
          <CheckCircle2 size={17} />
        );

      case "denied":
        return (
          <XCircle size={17} />
        );

      case "delivered":
        return (
          <Truck size={17} />
        );

      default:
        return (
          <Clock3 size={17} />
        );
    }
  };

  if (loading) {
    return (
      <div className="pharmacy-order-details-loading">
        <RefreshCw
          size={30}
          className="pharmacy-order-details-spinner"
        />

        <span>
          Loading order details...
        </span>
      </div>
    );
  }

  if (error || !order) {
    return (
      <div className="pharmacy-order-details-error-page">
        <AlertCircle size={34} />

        <strong>
          Order unavailable
        </strong>

        <span>
          {error ||
            "This order could not be found."}
        </span>

        <Link
          to="/pharmacy/orders"
          className="pharmacy-order-details-back"
        >
          <ArrowLeft size={16} />
          Back to Orders
        </Link>
      </div>
    );
  }

  const prescriptionUrl =
    order.prescription_photo;

  return (
    <div className="pharmacy-order-details-page">
      <div className="pharmacy-order-details-topbar">
        <Link
          to="/pharmacy/orders"
          className="pharmacy-order-details-back"
        >
          <ArrowLeft size={16} />
          Back to Orders
        </Link>

        <button
          type="button"
          onClick={loadOrder}
          className="pharmacy-order-details-refresh"
        >
          <RefreshCw size={16} />
          Refresh
        </button>
      </div>

      <header className="pharmacy-order-details-header">
        <div>
          <span className="pharmacy-order-details-kicker">
            Medicine Request
          </span>

          <h1>
            Order #{order.id}
          </h1>

          <p>
            Review the patient request,
            medicine information and
            delivery details.
          </p>
        </div>

        <div
          className={`pharmacy-order-details-status ${order.status}`}
        >
          {getStatusIcon(
            order.status
          )}

          <span>
            {order.status ||
              "pending"}
          </span>
        </div>
      </header>

      <div className="pharmacy-order-details-grid">
        <section className="pharmacy-order-details-card">
          <div className="pharmacy-order-details-section-title">
            <Package size={18} />

            <h2>
              Medicine
            </h2>
          </div>

          <div className="pharmacy-order-details-fields">
            <div>
              <span>
                Medicine name
              </span>

              <strong>
                {order.medicine_name ||
                  "Not provided"}
              </strong>
            </div>

            <div>
              <span>
                Company
              </span>

              <strong>
                {order.company_name ||
                  "Not provided"}
              </strong>
            </div>

            <div>
              <span>
                Dosage
              </span>

              <strong>
                {order.mg ||
                  "Not provided"}
              </strong>
            </div>

            <div>
              <span>
                Requested quantity
              </span>

              <strong>
                {order.quantity}
              </strong>
            </div>

            <div>
              <span>
                Current stock
              </span>

              <strong>
                {
                  order.available_quantity
                }
              </strong>
            </div>
          </div>
        </section>

        <section className="pharmacy-order-details-card">
          <div className="pharmacy-order-details-section-title">
            <User size={18} />

            <h2>
              Patient
            </h2>
          </div>

          <div className="pharmacy-order-details-fields">
            <div>
              <span>
                Name
              </span>

              <strong>
                {order.patient_name ||
                  "Not provided"}
              </strong>
            </div>

            <div>
              <span>
                Email
              </span>

              <strong className="pharmacy-order-details-inline">
                <Mail size={14} />

                {order.patient_email ||
                  "Not provided"}
              </strong>
            </div>

            <div>
              <span>
                Contact phone
              </span>

              <strong className="pharmacy-order-details-inline">
                <Phone size={14} />

                {order.contact_phone ||
                  "Not provided"}
              </strong>
            </div>
          </div>
        </section>

        <section className="pharmacy-order-details-card">
          <div className="pharmacy-order-details-section-title">
            <MapPin size={18} />

            <h2>
              Delivery
            </h2>
          </div>

          <div className="pharmacy-order-details-fields">
            <div className="pharmacy-order-details-full">
              <span>
                Address
              </span>

              <strong>
                {order.delivery_address ||
                  "Not provided"}
              </strong>
            </div>

            <div>
              <span>
                Latitude
              </span>

              <strong>
                {order.delivery_latitude ||
                  "Not provided"}
              </strong>
            </div>

            <div>
              <span>
                Longitude
              </span>

              <strong>
                {order.delivery_longitude ||
                  "Not provided"}
              </strong>
            </div>

            <div>
              <span>
                Location accuracy
              </span>

              <strong>
                {order.delivery_location_accuracy
                  ? `${order.delivery_location_accuracy} m`
                  : "Not provided"}
              </strong>
            </div>

            <div className="pharmacy-order-details-full">
              <span>
                Delivery note
              </span>

              <strong>
                {order.delivery_note ||
                  "No delivery note"}
              </strong>
            </div>
          </div>
        </section>

        <section className="pharmacy-order-details-card">
          <div className="pharmacy-order-details-section-title">
            <FileImage size={18} />

            <h2>
              Prescription
            </h2>
          </div>

          {prescriptionUrl ? (
            <a
              href={prescriptionUrl}
              target="_blank"
              rel="noreferrer"
              className="pharmacy-order-prescription-link"
            >
              <FileImage size={18} />

              View Prescription
            </a>
          ) : (
            <div className="pharmacy-order-no-prescription">
              No prescription was attached
              to this request.
            </div>
          )}
        </section>
      </div>
          <section className="pharmacy-order-actions">
  <div className="pharmacy-order-actions-heading">
    <h2>
      Pharmacy Action
    </h2>

    <p>
      Review the request before changing
      its status.
    </p>
  </div>

  {actionError && (
    <div className="pharmacy-order-action-error">
      <AlertCircle size={17} />

      <span>
        {actionError}
      </span>
    </div>
  )}

  {order.status === "pending" && (
    <>
      <div className="pharmacy-order-deny-field">
        <label htmlFor="denialReason">
          Denial reason
        </label>

        <textarea
          id="denialReason"
          value={denialReason}
          onChange={(event) =>
            setDenialReason(
              event.target.value
            )
          }
          placeholder="Required only if you deny this request..."
          rows={3}
          disabled={Boolean(
            actionLoading
          )}
        />
      </div>

      <div className="pharmacy-order-action-buttons">
        <button
          type="button"
          className="pharmacy-order-approve-button"
          onClick={handleApproveOrder}
          disabled={Boolean(
            actionLoading
          )}
        >
          <CheckCircle2 size={17} />

          {actionLoading === "approve"
            ? "Approving..."
            : "Approve Order"}
        </button>

        <button
          type="button"
          className="pharmacy-order-deny-button"
          onClick={handleDenyOrder}
          disabled={Boolean(
            actionLoading
          )}
        >
          <XCircle size={17} />

          {actionLoading === "deny"
            ? "Denying..."
            : "Deny Order"}
        </button>
      </div>
    </>
  )}

  {order.status === "approved" && (
    <button
      type="button"
      className="pharmacy-order-deliver-button"
      onClick={handleMarkDelivered}
      disabled={Boolean(
        actionLoading
      )}
    >
      <Truck size={17} />

      {actionLoading === "deliver"
        ? "Updating..."
        : "Mark as Delivered"}
    </button>
  )}

  {order.status === "denied" && (
    <div className="pharmacy-order-action-complete denied">
      <XCircle size={17} />
      This request has been denied.
    </div>
  )}

  {order.status === "delivered" && (
    <div className="pharmacy-order-action-complete delivered">
      <CheckCircle2 size={17} />
      This order has been delivered.
    </div>
  )}
</section>

      {order.denial_reason && (
        <section className="pharmacy-order-denial-reason">
          <XCircle size={18} />

          <div>
            <span>
              Denial reason
            </span>

            <strong>
              {order.denial_reason}
            </strong>
          </div>
        </section>
      )}

      <section className="pharmacy-order-details-meta">
        <div>
          <span>
            Created
          </span>

          <strong>
            {order.created_at
              ? new Date(
                  order.created_at
                ).toLocaleString()
              : "Not available"}
          </strong>
        </div>

        <div>
          <span>
            Last updated
          </span>

          <strong>
            {order.updated_at
              ? new Date(
                  order.updated_at
                ).toLocaleString()
              : "Not available"}
          </strong>
        </div>
      </section>
    </div>
  );
};

export default PharmacyOrderDetails;