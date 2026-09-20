import { Link } from "react-router-dom";
import React, {
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  AlertCircle,
  CheckCircle2,
  Clock3,
  PackageSearch,
  RefreshCw,
  Search,
  XCircle,
} from "lucide-react";

import {
  getPatientOrders,
} from "../../../services/orderApi";

import "./PatientOrders.css";

const PatientOrders = () => {
  const [orders, setOrders] =
    useState([]);

  const [search, setSearch] =
    useState("");

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");

  const loadOrders = async () => {
    try {
      setLoading(true);
      setError("");

      const response =
        await getPatientOrders();

      const data =
        Array.isArray(response.data)
          ? response.data
          : response.data?.results || [];

      setOrders(data);
    } catch (err) {
      console.error(
        "Patient orders API error:",
        err
      );

      setError(
        "Could not load your orders from the server."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadOrders();
  }, []);

  const filteredOrders =
    useMemo(() => {
      const query =
        search.trim().toLowerCase();

      if (!query) {
        return orders;
      }

      return orders.filter(
        (order) => {
          const searchableText = [
            order.id,
            order.medicine_name,
            order.pharmacy_name,
            order.status,
            order.mg,
          ]
            .filter(Boolean)
            .join(" ")
            .toLowerCase();

          return searchableText.includes(
            query
          );
        }
      );
    }, [orders, search]);

  const getStatusIcon = (status) => {
    switch (status) {
      case "approved":
        return (
          <CheckCircle2
            size={17}
          />
        );

      case "denied":
        return (
          <XCircle size={17} />
        );

      case "delivered":
        return (
          <CheckCircle2
            size={17}
          />
        );

      default:
        return (
          <Clock3 size={17} />
        );
    }
  };

  if (loading) {
    return (
      <div className="orders-loading">
        <RefreshCw
          size={28}
          className="orders-spinner"
        />

        <span>
          Loading your orders...
        </span>
      </div>
    );
  }

  return (
    <div className="patient-orders-page">
      <header className="orders-page-header">
        <div>
          <span className="orders-kicker">
            Order Tracking
          </span>

          <h1>My Orders</h1>

          <p>
            Track orders and pharmacist
            review status from one place.
          </p>
        </div>

        <button
          type="button"
          onClick={loadOrders}
          className="orders-refresh-button"
        >
          <RefreshCw size={17} />

          Refresh
        </button>
      </header>

      <div className="orders-search-bar">
        <Search size={18} />

        <input
          type="text"
          placeholder="Search order, medicine, pharmacy or status..."
          value={search}
          onChange={(event) =>
            setSearch(
              event.target.value
            )
          }
        />
      </div>

      {error && (
        <div className="orders-error">
          <AlertCircle size={18} />

          <span>{error}</span>
        </div>
      )}

      <div className="orders-result-row">
        <span>
          {filteredOrders.length}{" "}
          order
          {filteredOrders.length === 1
            ? ""
            : "s"}
        </span>
      </div>

      {filteredOrders.length === 0 ? (
        <div className="orders-empty">
          <PackageSearch size={38} />

          <strong>
            No orders found
          </strong>

          <span>
            Orders linked to your
            patient account will appear
            here.
          </span>
        </div>
      ) : (
        <section className="orders-list">
          {filteredOrders.map(
            (order) => (
              <article
                key={order.id}
                className="order-card"
              >
                <div className="order-card-top">
                  <div>
                    <span className="order-number">
                      Order #{order.id}
                    </span>

                    <h2>
                      {order.medicine_name ||
                        "Medicine Order"}
                    </h2>

                    <span className="order-pharmacy">
                      {order.pharmacy_name ||
                        "Registered pharmacy"}
                    </span>
                  </div>

                  <div
                    className={`order-status ${order.status}`}
                  >
                    {getStatusIcon(
                      order.status
                    )}

                    <span>
                      {order.status ||
                        "pending"}
                    </span>
                  </div>
                </div>

                <div className="order-details-grid">
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
                      Quantity
                    </span>

                    <strong>
                      {order.quantity ??
                        "Not provided"}
                    </strong>
                  </div>

                  <div>
                    <span>
                      Created
                    </span>

                    <strong>
                      {order.created_at
                        ? new Date(
                            order.created_at
                          ).toLocaleDateString()
                        : "Not available"}
                    </strong>
                  </div>
                </div>

                {order.status ===
                  "denied" &&
                  order.denial_reason && (
                    <div className="order-denial">
                      <strong>
                        Review note
                      </strong>

                      <span>
                        {
                          order.denial_reason
                        }
                      </span>
                    </div>
                  )}

                {order.delivery_address && (
                  <div className="order-delivery">
                    <span>
                      Delivery address
                    </span>

                    <strong>
                      {
                        order.delivery_address
                      }
                    </strong>
                  </div>
                )}
                <Link
  to={`/patient/orders/${order.id}`}
  className="order-view-button"
>
  View Details
</Link>
              </article>
            )
          )}
        </section>
      )}
    </div>
  );
};

export default PatientOrders;