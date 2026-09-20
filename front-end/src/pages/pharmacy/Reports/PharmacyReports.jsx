import React, {
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  AlertCircle,
  FileImage,
  FileText,
  Pencil,
  Plus,
  RefreshCw,
  Search,
  Trash2,
  User,
} from "lucide-react";

import {
  Link,
} from "react-router-dom";

import {
  deletePharmacyReport,
  getPharmacyReports,
} from "../../../services/reportApi";

import "./PharmacyReports.css";

const PharmacyReports = () => {
  const [reports, setReports] =
    useState([]);

  const [search, setSearch] =
    useState("");

  const [loading, setLoading] =
    useState(true);

const [error, setError] =
    useState("");
    const [
  deletingReportId,
  setDeletingReportId,
] = useState(null);

  const loadReports = async () => {
    try {
      setLoading(true);
      setError("");

      const response =
        await getPharmacyReports();

      const data =
        Array.isArray(response.data)
          ? response.data
          : response.data?.results || [];

      setReports(data);
    } catch (err) {
      console.error(
        "Pharmacy reports API error:",
        err
      );

      setError(
        "Could not load patient reports."
      );
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteReport = async (
  report
) => {
  const confirmed = window.confirm(
    `Delete "${report.report_name}"?`
  );

  if (!confirmed) {
    return;
  }

  try {
    setDeletingReportId(
      report.id
    );

    setError("");

    await deletePharmacyReport(
      report.id
    );

    setReports(
      (currentReports) =>
        currentReports.filter(
          (item) =>
            item.id !== report.id
        )
    );
  } catch (err) {
    console.error(
      "Delete report error:",
      err
    );

    setError(
      "Could not delete this report."
    );
  } finally {
    setDeletingReportId(
      null
    );
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
            report.id,
            report.report_name,
            report.patient_name,
            report.pharmacy_name,
            report.date,
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
      <div className="pharmacy-reports-loading">
        <RefreshCw
          size={28}
          className="pharmacy-reports-spinner"
        />

        <span>
          Loading patient reports...
        </span>
      </div>
    );
  }

  return (
    <div className="pharmacy-reports-page">
      <header className="pharmacy-reports-header">
        <div>
          <span className="pharmacy-reports-kicker">
            Patient Records
          </span>

          <h1>
            Patient Reports
          </h1>

          <p>
            View and manage reports associated
            with your pharmacy.
          </p>
        </div>

        <div className="pharmacy-reports-header-actions">
          <button
            type="button"
            className="pharmacy-reports-refresh"
            onClick={loadReports}
          >
            <RefreshCw size={16} />
            Refresh
          </button>

<Link
  to="/pharmacy/reports/add"
  className="pharmacy-reports-add"
>
  <Plus size={16} />
  Add Report
</Link>
        </div>
      </header>

      <div className="pharmacy-reports-search">
        <Search size={18} />

        <input
          type="text"
          placeholder="Search report or patient..."
          value={search}
          onChange={(event) =>
            setSearch(
              event.target.value
            )
          }
        />
      </div>

      {error && (
        <div className="pharmacy-reports-error">
          <AlertCircle size={18} />

          <span>
            {error}
          </span>
        </div>
      )}

      <div className="pharmacy-reports-count">
        {filteredReports.length}{" "}
        report
        {filteredReports.length === 1
          ? ""
          : "s"}
      </div>

      {filteredReports.length === 0 ? (
        <div className="pharmacy-reports-empty">
          <FileText size={38} />

          <strong>
            No reports found
          </strong>

          <span>
            Reports connected to your
            pharmacy will appear here.
          </span>
        </div>
      ) : (
        <section className="pharmacy-reports-grid">
          {filteredReports.map(
            (report) => (
              <article
                key={report.id}
                className="pharmacy-report-card"
              >
                <div className="pharmacy-report-card-top">
                  <div className="pharmacy-report-icon">
                    <FileText size={20} />
                  </div>

                  <span className="pharmacy-report-id">
                    Report #{report.id}
                  </span>
                </div>

                <h2>
                  {report.report_name ||
                    "Untitled Report"}
                </h2>

                <div className="pharmacy-report-patient">
                  <User size={14} />

                  <span>
                    {report.patient_name ||
                      "Unknown patient"}
                  </span>
                </div>

                <div className="pharmacy-report-meta">
                  <div>
                    <span>
                      Report date
                    </span>

                    <strong>
                      {report.date ||
                        "Not provided"}
                    </strong>
                  </div>

                  <div>
                    <span>
                      Added
                    </span>

                    <strong>
                      {report.created_at
                        ? new Date(
                            report.created_at
                          ).toLocaleDateString()
                        : "Not available"}
                    </strong>
                  </div>
                </div>

                {report.photo ? (
                  <a
                    href={report.photo}
                    target="_blank"
                    rel="noreferrer"
                    className="pharmacy-report-view-photo"
                  >
                    <FileImage size={15} />
                    View Report Image
                  </a>
                ) : (
                  <div className="pharmacy-report-no-photo">
                    <FileImage size={15} />
                    No image attached
                  </div>
                )}
               {report.pharmacy && (
  <div className="pharmacy-report-actions">
    <Link
      to={`/pharmacy/reports/${report.id}/edit`}
      className="pharmacy-report-edit-button"
    >
      <Pencil size={15} />
      Edit Report
    </Link>

    <button
      type="button"
      className="pharmacy-report-delete-button"
      onClick={() =>
        handleDeleteReport(report)
      }
      disabled={
        deletingReportId === report.id
      }
    >
      <Trash2 size={15} />

      {deletingReportId === report.id
        ? "Deleting..."
        : "Delete Report"}
    </button>
  </div>
)}
              </article>
            )
          )}
        </section>
      )}
    </div>
  );
};

export default PharmacyReports;