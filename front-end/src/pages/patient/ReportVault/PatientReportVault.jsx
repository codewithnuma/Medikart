import React, {
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  AlertCircle,
  FileText,
  Image as ImageIcon,
  RefreshCw,
  Search,
} from "lucide-react";

import { Link } from "react-router-dom";

import {
  getPatientReports,
} from "../../../services/reportApi";

import "./PatientReportVault.css";

const PatientReportVault = () => {
  const [reports, setReports] = useState([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadReports = async () => {
    try {
      setLoading(true);
      setError("");

      const response =
        await getPatientReports();

      const data =
        Array.isArray(response.data)
          ? response.data
          : response.data?.results || [];

      setReports(data);
    } catch (err) {
      console.error(
        "Patient reports API error:",
        err
      );

      setError(
        "Could not load your reports from the server."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReports();
  }, []);

  const filteredReports =
    useMemo(() => {
      const query =
        search.trim().toLowerCase();

      if (!query) {
        return reports;
      }

      return reports.filter(
        (report) => {
          const searchableText = [
            report.report_name,
            report.date,
            report.pharmacy_name,
          ]
            .filter(Boolean)
            .join(" ")
            .toLowerCase();

          return searchableText.includes(
            query
          );
        }
      );
    }, [reports, search]);

  if (loading) {
    return (
      <div className="report-vault-loading">
        <RefreshCw
          size={28}
          className="report-vault-spinner"
        />

        <span>
          Loading your medical reports...
        </span>
      </div>
    );
  }

  return (
    <div className="patient-report-vault">
      <header className="report-vault-header">
        <div>
          <span className="report-vault-kicker">
            Medical Records
          </span>

          <h1>Report Vault</h1>

          <p>
            View medical reports linked
            to your patient account.
          </p>
        </div>

        <div className="report-vault-header-actions">
  <Link
    to="/patient/report-capture"
    className="report-vault-add"
  >
    Add Report
  </Link>

  <button
    type="button"
    onClick={loadReports}
    className="report-vault-refresh"
  >
    <RefreshCw size={17} />
    Refresh
  </button>
</div>
      </header>

      <div className="report-vault-search">
        <Search size={18} />

        <input
          type="text"
          placeholder="Search reports..."
          value={search}
          onChange={(event) =>
            setSearch(
              event.target.value
            )
          }
        />
      </div>

      {error && (
        <div className="report-vault-error">
          <AlertCircle size={18} />
          <span>{error}</span>
        </div>
      )}

      <div className="report-vault-count">
        {filteredReports.length}{" "}
        report
        {filteredReports.length === 1
          ? ""
          : "s"}
      </div>

      {filteredReports.length === 0 ? (
        <div className="report-vault-empty">
          <FileText size={38} />

          <strong>
            No reports found
          </strong>

          <span>
            Reports linked to your
            patient account will appear
            here.
          </span>
        </div>
      ) : (
        <section className="report-vault-grid">
          {filteredReports.map(
            (report) => (
              <article
                key={report.id}
                className="report-vault-card"
              >
                <div className="report-vault-preview">
                  {report.photo ? (
                    <img
                      src={report.photo}
                      alt={
                        report.report_name ||
                        "Medical report"
                      }
                    />
                  ) : (
                    <div className="report-vault-placeholder">
                      <ImageIcon
                        size={34}
                      />
                    </div>
                  )}
                </div>

                <div className="report-vault-card-content">
                  <span className="report-vault-label">
                    Medical Report
                  </span>

                  <h2>
                    {report.report_name ||
                      "Untitled Report"}
                  </h2>

                  <div className="report-vault-meta">
                    <div>
                      <span>Date</span>

                      <strong>
                        {report.date ||
                          "Not provided"}
                      </strong>
                    </div>

                    {report.pharmacy_name && (
                      <div>
                        <span>
                          Pharmacy
                        </span>

                        <strong>
                          {
                            report.pharmacy_name
                          }
                        </strong>
                      </div>
                    )}
                  </div>

                  <Link
  to={`/patient/report-vault/${report.id}`}
  className="report-vault-open"
>
  View Details
</Link>
                </div>
              </article>
            )
          )}
        </section>
      )}
    </div>
  );
};

export default PatientReportVault;