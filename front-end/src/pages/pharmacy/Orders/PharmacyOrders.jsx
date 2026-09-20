import React, {
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  AlertCircle,
  Clock3,
  PackageSearch,
  RefreshCw,
  Search,
  CheckCircle2,
  Truck,
  XCircle,
} from "lucide-react";

import {
  Link,
} from "react-router-dom";

import {
  getPharmacyOrders,
} from "../../../services/orderApi";

import "./PharmacyOrders.css";

const PharmacyOrders = () => {
  const [orders, setOrders] =
    useState([]);

  const [search, setSearch] =
    useState("");

  const [statusFilter, setStatusFilter] =
    useState("all");

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");

  const loadOrders = async () => {
    try {
      setLoading(true);
      setError("");

      const response =
        await getPharmacyOrders();

      const data =
        Array.isArray(response.data)
          ? response.data
          : response.data?.results || [];

      setOrders(data);
    } catch (err) {
      console.error(
        "Pharmacy orders API error:",
        err
      );

      setError(
        "Could not load pharmacy orders."
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

      return orders.filter(
        (order) => {
          const matchesStatus =
            statusFilter === "all" ||
            order.status === statusFilter;

          const searchableText = [
            order.id,
            order.patient_name,
            order.patient_email,
            order.medicine_name,
            order.company_name,
            order.status,
            order.delivery_address,
          ]
            .filter(Boolean)
            .join(" ")
            .toLowerCase();

          const matchesSearch =
            !query ||
            searchableText.includes(
              query
            );

          return (
            matchesStatus &&
            matchesSearch
          );
        }
      );
    }, [
      orders,
      search,
      statusFilter,
    ]);

  const getStatusIcon = (
    status
  ) => {
    switch (status) {
      case "approved":
        return (
          <CheckCircle2 size={16} />
        );

      case "denied":
        return (
          <XCircle size={16} />
        );

      case "delivered":
        return (
          <Truck size={16} />
        );

      default:
        return (
          <Clock3 size={16} />
        );
    }
  };

  if (loading) {
    return (
      <div className="pharmacy-orders-loading">
        <RefreshCw
          size={28}
          className="pharmacy-orders-spinner"
        />

        <span>
          Loading patient orders...
        </span>
      </div>
    );
  }

  return (
    <div className="pharmacy-orders-page">
      <header className="pharmacy-orders-header">
        <div>
          <span className="pharmacy-orders-kicker">
            Order Management
          </span>

          <h1>
            Patient Orders
          </h1>

          <p>
            Review medicine requests
            submitted to your pharmacy.
          </p>
        </div>

        <button
          type="button"
          onClick={loadOrders}
          className="pharmacy-orders-refresh"
        >
          <RefreshCw size={17} />
          Refresh
        </button>
      </header>

      <div className="pharmacy-orders-toolbar">
        <div className="pharmacy-orders-search">
          <Search size={18} />

          <input
            type="text"
            placeholder="Search patient, medicine, order or address..."
            value={search}
            onChange={(event) =>
              setSearch(
                event.target.value
              )
            }
          />
        </div>

        <select
          value={statusFilter}
          onChange={(event) =>
            setStatusFilter(
              event.target.value
            )
          }
          className="pharmacy-orders-filter"
        >
          <option value="all">
            All statuses
          </option>

          <option value="pending">
            Pending
          </option>

          <option value="approved">
            Approved
          </option>

          <option value="denied">
            Denied
          </option>

          <option value="delivered">
            Delivered
          </option>
        </select>
      </div>

      {error && (
        <div className="pharmacy-orders-error">
          <AlertCircle size={18} />

          <span>{error}</span>
        </div>
      )}

      <div className="pharmacy-orders-count">
        {filteredOrders.length}{" "}
        order
        {filteredOrders.length === 1
          ? ""
          : "s"}
      </div>

      {filteredOrders.length === 0 ? (
        <div className="pharmacy-orders-empty">
          <PackageSearch size={38} />

          <strong>
            No orders found
          </strong>

          <span>
            Patient medicine requests
            for your pharmacy will
            appear here.
          </span>
        </div>
      ) : (
        <section className="pharmacy-orders-list">
          {filteredOrders.map(
            (order) => (
              <article
                key={order.id}
                className="pharmacy-order-card"
              >
                <div className="pharmacy-order-card-top">
                  <div>
                    <span className="pharmacy-order-number">
                      Order #{order.id}
                    </span>

                    <h2>
                      {order.medicine_name ||
                        "Medicine"}
                    </h2>

                    <span className="pharmacy-order-patient">
                      {order.patient_name ||
                        "Patient"}
                    </span>
                  </div>

                  <div
                    className={`pharmacy-order-badge ${order.status}`}
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

                <div className="pharmacy-order-info-grid">
                  <div>
                    <span>
                      Requested
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
                      Contact
                    </span>

                    <strong>
                      {order.contact_phone ||
                        "Not provided"}
                    </strong>
                  </div>
                </div>

                {order.delivery_address && (
                  <div className="pharmacy-order-address">
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
                  to={`/pharmacy/orders/${order.id}`}
                  className="pharmacy-order-review-button"
                >
                  Review Order
                </Link>
              </article>
            )
          )}
        </section>
      )}
    </div>
  );
};

export default PharmacyOrders;