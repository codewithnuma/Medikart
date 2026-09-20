import React, {
  useCallback,
  useEffect,
  useState,
} from "react";

import {
  CheckCircle2,
  FileText,
  PackageSearch,
  Pill,
  RefreshCw,
  Truck,
} from "lucide-react";

import { Link } from "react-router-dom";

import { useAuth } from "../../../context/AuthContext";

import {
  getMyMedicines,
} from "../../../services/medicineApi";

import {
  getPharmacyOrders,
} from "../../../services/orderApi";

import {
  getPharmacyReports,
} from "../../../services/reportApi";

import "./PharmacyDashboard.css";

const PharmacyDashboard = () => {
  const { user } = useAuth();

  const [medicines, setMedicines] =
    useState([]);

  const [orders, setOrders] =
    useState([]);

  const [reports, setReports] =
    useState([]);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");

  const loadDashboard = useCallback(
    async () => {
      setLoading(true);
      setError("");

      const results =
        await Promise.allSettled([
          getMyMedicines(),
          getPharmacyOrders(),
          getPharmacyReports(),
        ]);

      const [
        medicineResult,
        orderResult,
        reportResult,
      ] = results;

      if (
        medicineResult.status ===
        "fulfilled"
      ) {
        const data =
          medicineResult.value.data;

        setMedicines(
          Array.isArray(data)
            ? data
            : data?.results || []
        );
      } else {
        console.error(
          "Pharmacy medicines API error:",
          medicineResult.reason
        );
      }

      if (
        orderResult.status ===
        "fulfilled"
      ) {
        const data =
          orderResult.value.data;

        setOrders(
          Array.isArray(data)
            ? data
            : data?.results || []
        );
      } else {
        console.error(
          "Pharmacy orders API error:",
          orderResult.reason
        );
      }

      if (
        reportResult.status ===
        "fulfilled"
      ) {
        const data =
          reportResult.value.data;

        setReports(
          Array.isArray(data)
            ? data
            : data?.results || []
        );
      } else {
        console.error(
          "Pharmacy reports API error:",
          reportResult.reason
        );
      }

      const failedRequests =
        results.filter(
          (result) =>
            result.status ===
            "rejected"
        );

      if (
        failedRequests.length ===
        results.length
      ) {
        setError(
          "Dashboard data could not be loaded."
        );
      }

      setLoading(false);
    },
    []
  );

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  const pendingOrders =
    orders.filter(
      (order) =>
        order.status === "pending"
    );

  const approvedOrders =
    orders.filter(
      (order) =>
        order.status === "approved"
    );

  const deliveredOrders =
    orders.filter(
      (order) =>
        order.status === "delivered"
    );

  const recentOrders =
    [...orders]
      .sort(
        (a, b) =>
          new Date(b.created_at) -
          new Date(a.created_at)
      )
      .slice(0, 4);

  const lowStockMedicines =
    medicines.filter(
      (medicine) =>
        Number(
          medicine.available_quantity
        ) <= 5
    );

  const displayName =
    user?.username ||
    user?.email ||
    "Pharmacy";

  if (loading) {
    return (
      <div className="pharmacy-dashboard-loading">
        <RefreshCw
          size={28}
          className="pharmacy-dashboard-spinner"
        />

        <span>
          Loading pharmacy dashboard...
        </span>
      </div>
    );
  }

  return (
    <div className="pharmacy-dashboard">
      <header className="pharmacy-dashboard-header">
        <div>
          <span className="pharmacy-dashboard-kicker">
            Pharmacy Dashboard
          </span>

          <h1>
            Hello, {displayName}
          </h1>

          <p>
            Manage medicine inventory,
            patient requests and reports
            from one place.
          </p>
        </div>

        <button
          type="button"
          onClick={loadDashboard}
          className="pharmacy-dashboard-refresh"
        >
          <RefreshCw size={17} />
          Refresh
        </button>
      </header>

      {error && (
        <div className="pharmacy-dashboard-error">
          {error}
        </div>
      )}

      {/* STATS */}

      <section className="pharmacy-dashboard-stats">
        <Link
          to="/pharmacy/medicines"
          className="pharmacy-stat-card"
        >
          <div className="pharmacy-stat-icon blue">
            <Pill size={21} />
          </div>

          <div>
            <span>
              My Medicines
            </span>

            <strong>
              {medicines.length}
            </strong>
          </div>
        </Link>

        <Link
          to="/pharmacy/orders"
          className="pharmacy-stat-card"
        >
          <div className="pharmacy-stat-icon orange">
            <PackageSearch
              size={21}
            />
          </div>

          <div>
            <span>
              Pending Orders
            </span>

            <strong>
              {pendingOrders.length}
            </strong>
          </div>
        </Link>

        <Link
          to="/pharmacy/orders"
          className="pharmacy-stat-card"
        >
          <div className="pharmacy-stat-icon green">
            <CheckCircle2
              size={21}
            />
          </div>

          <div>
            <span>
              Approved Orders
            </span>

            <strong>
              {approvedOrders.length}
            </strong>
          </div>
        </Link>

        <Link
          to="/pharmacy/orders"
          className="pharmacy-stat-card"
        >
          <div className="pharmacy-stat-icon purple">
            <Truck size={21} />
          </div>

          <div>
            <span>
              Delivered
            </span>

            <strong>
              {deliveredOrders.length}
            </strong>
          </div>
        </Link>
      </section>

      {/* QUICK ACTIONS */}

      <section className="pharmacy-dashboard-section">
        <div className="pharmacy-dashboard-section-header">
          <div>
            <h2>
              Quick actions
            </h2>

            <p>
              Access common pharmacy
              management tasks.
            </p>
          </div>
        </div>

        <div className="pharmacy-dashboard-actions">
          <Link
            to="/pharmacy/medicines"
            className="pharmacy-action-card"
          >
            <div>
              <Pill size={22} />
            </div>

            <strong>
              Manage Medicines
            </strong>

            <span>
              Add, update and manage your
              pharmacy inventory.
            </span>
          </Link>

          <Link
            to="/pharmacy/orders"
            className="pharmacy-action-card"
          >
            <div>
              <PackageSearch
                size={22}
              />
            </div>

            <strong>
              Review Orders
            </strong>

            <span>
              Review medicine requests
              submitted by patients.
            </span>
          </Link>

          <Link
            to="/pharmacy/reports"
            className="pharmacy-action-card"
          >
            <div>
              <FileText size={22} />
            </div>

            <strong>
              Patient Reports
            </strong>

            <span>
              View reports connected to
              your pharmacy.
            </span>
          </Link>
        </div>
      </section>

      {/* LOWER GRID */}

      <div className="pharmacy-dashboard-content">
        <section className="pharmacy-dashboard-panel">
          <div className="pharmacy-panel-header">
            <div>
              <h2>
                Recent orders
              </h2>

              <p>
                Latest medicine requests
                from patients.
              </p>
            </div>

            <Link
              to="/pharmacy/orders"
              className="pharmacy-view-all"
            >
              View all
            </Link>
          </div>

          {recentOrders.length === 0 ? (
            <div className="pharmacy-dashboard-empty">
              <PackageSearch
                size={30}
              />

              <strong>
                No orders yet
              </strong>

              <span>
                Patient medicine
                requests will appear
                here.
              </span>
            </div>
          ) : (
            <div className="pharmacy-dashboard-list">
              {recentOrders.map(
                (order) => (
                  <div
                    key={order.id}
                    className="pharmacy-dashboard-list-item"
                  >
                    <div className="pharmacy-dashboard-list-icon">
                      <PackageSearch
                        size={18}
                      />
                    </div>

                    <div className="pharmacy-dashboard-list-info">
                      <strong>
                        {order.medicine_name ||
                          `Order #${order.id}`}
                      </strong>

                      <span>
                        {order.patient_name ||
                          "Patient"}
                      </span>
                    </div>

                    <span
                      className={`pharmacy-order-status ${order.status}`}
                    >
                      {order.status}
                    </span>
                  </div>
                )
              )}
            </div>
          )}
        </section>

        <section className="pharmacy-dashboard-panel">
          <div className="pharmacy-panel-header">
            <div>
              <h2>
                Inventory overview
              </h2>

              <p>
                Medicines that may need
                restocking.
              </p>
            </div>

            <Link
              to="/pharmacy/medicines"
              className="pharmacy-view-all"
            >
              Manage
            </Link>
          </div>

          {lowStockMedicines.length ===
          0 ? (
            <div className="pharmacy-dashboard-empty">
              <Pill size={30} />

              <strong>
                Inventory looks good
              </strong>

              <span>
                No medicines currently
                have 5 or fewer units.
              </span>
            </div>
          ) : (
            <div className="pharmacy-dashboard-list">
              {lowStockMedicines
                .slice(0, 4)
                .map(
                  (medicine) => (
                    <div
                      key={
                        medicine.id
                      }
                      className="pharmacy-dashboard-list-item"
                    >
                      <div className="pharmacy-dashboard-list-icon">
                        <Pill
                          size={18}
                        />
                      </div>

                      <div className="pharmacy-dashboard-list-info">
                        <strong>
                          {
                            medicine.medicine_name
                          }
                        </strong>

                        <span>
                          {medicine.mg ||
                            "Dose not provided"}
                        </span>
                      </div>

                      <span className="pharmacy-low-stock">
                        {
                          medicine.available_quantity
                        }{" "}
                        left
                      </span>
                    </div>
                  )
                )}
            </div>
          )}
        </section>
      </div>

      <section className="pharmacy-dashboard-summary">
        <FileText size={18} />

        <div>
          <strong>
            {reports.length} patient
            report
            {reports.length === 1
              ? ""
              : "s"}
          </strong>

          <span>
            Reports currently connected
            to your pharmacy account.
          </span>
        </div>
      </section>
    </div>
  );
};

export default PharmacyDashboard;