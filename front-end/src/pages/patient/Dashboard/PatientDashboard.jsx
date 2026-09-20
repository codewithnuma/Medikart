import React, {
  useCallback,
  useEffect,
  useState,
} from "react";

import {
  FileText,
  HeartPulse,
  PackageSearch,
  Pill,
  RefreshCw,
  ShieldCheck,
} from "lucide-react";

import { Link } from "react-router-dom";

import { useAuth } from "../../../context/AuthContext";

import {
  getMedicines,
} from "../../../services/medicineApi";

import {
  getPatientOrders,
} from "../../../services/orderApi";

import {
  getPatientReports,
} from "../../../services/reportApi";

import "./PatientDashboard.css";

const PatientDashboard = () => {
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
          getMedicines(),
          getPatientOrders(),
          getPatientReports(),
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
        setMedicines(
          Array.isArray(
            medicineResult.value.data
          )
            ? medicineResult.value.data
            : []
        );
      } else {
        console.error(
          "Medicine API error:",
          medicineResult.reason
        );
      }

      if (
        orderResult.status ===
        "fulfilled"
      ) {
        setOrders(
          Array.isArray(
            orderResult.value.data
          )
            ? orderResult.value.data
            : []
        );
      } else {
        console.error(
          "Order API error:",
          orderResult.reason
        );
      }

      if (
        reportResult.status ===
        "fulfilled"
      ) {
        setReports(
          Array.isArray(
            reportResult.value.data
          )
            ? reportResult.value.data
            : []
        );
      } else {
        console.error(
          "Report API error:",
          reportResult.reason
        );
      }

      const failedRequests =
        results.filter(
          (result) =>
            result.status === "rejected"
        );

      if (
        failedRequests.length ===
        results.length
      ) {
        setError(
          "Dashboard data could not be loaded from the server."
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
    ).length;

  const approvedOrders =
    orders.filter(
      (order) =>
        order.status === "approved"
    ).length;

  const recentReports =
    [...reports]
      .sort(
        (a, b) =>
          new Date(
            b.created_at ||
              b.date
          ) -
          new Date(
            a.created_at ||
              a.date
          )
      )
      .slice(0, 3);

  const recentOrders =
    [...orders]
      .sort(
        (a, b) =>
          new Date(b.created_at) -
          new Date(a.created_at)
      )
      .slice(0, 3);

  const displayName =
    user?.username ||
    user?.email ||
    "Patient";

  if (loading) {
    return (
      <div className="patient-dashboard-loading">
        <RefreshCw
          size={28}
          className="dashboard-spinner"
        />

        <span>
          Loading your healthcare
          dashboard...
        </span>
      </div>
    );
  }

  return (
    <div className="patient-dashboard">
      {/* ========================
          HEADER
      ======================== */}

      <header className="patient-dashboard-header">
        <div>
          <span className="patient-dashboard-kicker">
            Patient Dashboard
          </span>

          <h1>
            Hello, {displayName}
          </h1>

          <p>
            Your reports, orders and
            healthcare services in one
            place.
          </p>
        </div>

        <button
          type="button"
          onClick={loadDashboard}
          className="dashboard-refresh-button"
        >
          <RefreshCw size={17} />

          Refresh
        </button>
      </header>

      {error && (
        <div className="dashboard-error">
          {error}
        </div>
      )}

      {/* ========================
          STATS
      ======================== */}

      <section className="dashboard-stat-grid">
        <Link
  to="/patient/medicines"
  className="dashboard-stat-card dashboard-stat-link"
>
          <div className="dashboard-stat-icon blue">
            <Pill size={21} />
          </div>

          <div>
            <span>
              Available Medicines
            </span>

            <strong>
              {medicines.length}
            </strong>
          </div>
        </Link>

        <Link
  to="/patient/orders"
  className="dashboard-stat-card dashboard-stat-link"
>
          <div className="dashboard-stat-icon orange">
            <PackageSearch
              size={21}
            />
          </div>

          <div>
            <span>
              My Orders
            </span>

            <strong>
              {orders.length}
            </strong>
          </div>
        </Link>

        <Link
  to="/patient/report-vault"
  className="dashboard-stat-card dashboard-stat-link"
>
          <div className="dashboard-stat-icon green">
            <FileText size={21} />
          </div>

          <div>
            <span>
              Medical Reports
            </span>

            <strong>
              {reports.length}
            </strong>
          </div>
        </Link>

        <Link
  to="/patient/orders"
  className="dashboard-stat-card dashboard-stat-link"
>
          <div className="dashboard-stat-icon purple">
            <HeartPulse
              size={21}
            />
          </div>

          <div>
            <span>
              Pending Orders
            </span>

            <strong>
              {pendingOrders}
            </strong>
          </div>
        </Link>
      </section>

      {/* ========================
          QUICK ACTIONS
      ======================== */}

      <section className="dashboard-section">
        <div className="dashboard-section-header">
          <div>
            <h2>
              Quick actions
            </h2>

            <p>
              Access your most used
              healthcare services.
            </p>
          </div>
        </div>

        <div className="dashboard-action-grid">
          <Link
            to="/patient/medicines"
            className="dashboard-action-card"
          >
            <div>
              <Pill size={22} />
            </div>

            <strong>
              Browse Medicines
            </strong>

            <span>
              View pharmacy inventory
              available through the
              backend.
            </span>
          </Link>

          <Link
            to="/patient/report-capture"
            className="dashboard-action-card"
          >
            <div>
              <FileText size={22} />
            </div>

            <strong>
              Add Report
            </strong>

            <span>
              Capture or upload a medical
              report.
            </span>
          </Link>

          <Link
  to="/patient/pharmacies"
  className="dashboard-action-card"
>
  <div>
    <HeartPulse size={22} />
  </div>

  <strong>
    Browse Pharmacies
  </strong>

  <span>
    View registered pharmacies
    and their available medicines.
  </span>
</Link>

        </div>
      </section>

      {/* ========================
          LOWER GRID
      ======================== */}

      <div className="dashboard-content-grid">
        {/* ORDERS */}

        <section className="dashboard-panel">
          <div className="dashboard-panel-header">
            <div>
              <h2>
                Recent orders
              </h2>

              <p>
  Your latest medicine
  requests and their status.
</p>
            </div>

            <Link
              to="/patient/orders"
              className="dashboard-view-all"
            >
              View all
            </Link>
          </div>

          {recentOrders.length === 0 ? (
            <div className="dashboard-empty">
              <PackageSearch
                size={29}
              />

              <strong>
                No orders yet
              </strong>

              <span>
                Your backend orders will
                appear here.
              </span>
            </div>
          ) : (
            <div className="dashboard-list">
              {recentOrders.map(
                (order) => (
                 <Link
  key={order.id}
  to={`/patient/orders/${order.id}`}
  className="dashboard-list-item dashboard-order-link"
>
                    <div className="dashboard-list-icon">
                      <PackageSearch
                        size={18}
                      />
                    </div>

                    <div className="dashboard-list-info">
                      <strong>
                        {order.medicine_name ||
                          `Order #${order.id}`}
                      </strong>

                      <span>
                        {order.pharmacy_name ||
                          "Pharmacy"}
                      </span>
                    </div>

                    <span
                      className={`dashboard-status ${order.status}`}
                    >
                      {order.status}
                    </span>
                  </Link>
                )
              )}
            </div>
          )}
        </section>

        {/* REPORTS */}

        <section className="dashboard-panel">
          <div className="dashboard-panel-header">
            <div>
              <h2>
                Recent reports
              </h2>

              <p>
  Your latest uploaded
  medical reports.
</p>
            </div>

            <Link
              to="/patient/report-vault"
              className="dashboard-view-all"
            >
              View vault
            </Link>
          </div>

          {recentReports.length === 0 ? (
            <div className="dashboard-empty">
              <FileText size={29} />

              <strong>
                No reports yet
              </strong>

              <span>
                Reports added in Django
                will appear here.
              </span>
            </div>
          ) : (
            <div className="dashboard-list">
              {recentReports.map(
                (report) => (
                  <div
                    key={report.id}
                    className="dashboard-list-item"
                  >
                    <div className="dashboard-list-icon">
                      <FileText
                        size={18}
                      />
                    </div>

                    <div className="dashboard-list-info">
                      <strong>
                        {report.report_name}
                      </strong>

                      <span>
                        {report.date}
                      </span>
                    </div>
                  </div>
                )
              )}
            </div>
          )}
        </section>
      </div>

      {/* ========================
          STATUS
      ======================== */}

      <section className="dashboard-system-status">
  <ShieldCheck size={18} />

  <div>
    <strong>
      Your account is up to date
    </strong>

    <span>
      Your medicines, orders and
      medical reports are synced.
      {approvedOrders > 0
        ? ` ${approvedOrders} order(s) are currently approved.`
        : ""}
    </span>
  </div>
</section>
    </div>
  );
};

export default PatientDashboard;