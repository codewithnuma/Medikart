import React, {
  useEffect,
  useState,
} from "react";

import {
  ArrowLeft,
  Building2,
  CalendarDays,
  FileText,
  Image as ImageIcon,
  RefreshCw,
} from "lucide-react";

import {
  Link,
  useParams,
} from "react-router-dom";

import {
  getPatientReport,
} from "../../../services/reportApi";

import "./ReportDetails.css";

const ReportDetails = () => {
  const { id } = useParams();

  const [report, setReport] =
    useState(null);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");

  const loadReport = async () => {
    try {
      setLoading(true);
      setError("");

      const response =
        await getPatientReport(id);

      setReport(response.data);
    } catch (err) {
      console.error(
        "Report details API error:",
        err
      );

      setError(
        "Could not load this medical report."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReport();
  }, [id]);

  if (loading) {
    return (
      <div className="report-detail-loading">
        <RefreshCw
          size={28}
          className="report-detail-spinner"
        />

        <span>
          Loading report...
        </span>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="report-detail-error">
        <FileText size={38} />

        <strong>
          Report unavailable
        </strong>

        <span>
          {error ||
            "This report could not be found."}
        </span>

        <Link
          to="/patient/report-vault"
          className="report-detail-back-link"
        >
          <ArrowLeft size={16} />
          Back to Report Vault
        </Link>
      </div>
    );
  }

  return (
    <div className="report-detail-page">
      <Link
        to="/patient/report-vault"
        className="report-detail-back"
      >
        <ArrowLeft size={16} />
        Back to Report Vault
      </Link>

      <header className="report-detail-header">
        <div>
          <span className="report-detail-kicker">
            Medical Record
          </span>

          <h1>
            {report.report_name ||
              "Medical Report"}
          </h1>

          <p>
            Review the details and
            uploaded report file.
          </p>
        </div>
      </header>

      <div className="report-detail-grid">
        <section className="report-detail-panel">
          <div className="report-detail-section-heading">
            <h2>
              Report information
            </h2>
          </div>

          <div className="report-detail-info-list">
            <div>
              <CalendarDays size={17} />

              <section>
                <span>
                  Report date
                </span>

                <strong>
                  {report.date ||
                    "Not provided"}
                </strong>
              </section>
            </div>

            <div>
              <Building2 size={17} />

              <section>
                <span>
                  Pharmacy
                </span>

                <strong>
                  {report.pharmacy_name ||
                    "Not linked to a pharmacy"}
                </strong>
              </section>
            </div>
          </div>

          {report.created_at && (
            <div className="report-detail-created">
              <span>
                Added to vault
              </span>

              <strong>
                {new Date(
                  report.created_at
                ).toLocaleString()}
              </strong>
            </div>
          )}
        </section>

        <section className="report-detail-panel">
          <div className="report-detail-section-heading">
            <h2>
              Report file
            </h2>
          </div>

          {report.photo ? (
            <div className="report-detail-preview">
              <img
                src={report.photo}
                alt={
                  report.report_name ||
                  "Medical report"
                }
              />

              <a
                href={report.photo}
                target="_blank"
                rel="noreferrer"
                className="report-detail-open"
              >
                <ImageIcon size={16} />
                Open full report
              </a>
            </div>
          ) : (
            <div className="report-detail-no-file">
              <ImageIcon size={35} />

              <strong>
                No report image
              </strong>

              <span>
                No uploaded file is
                attached to this report.
              </span>
            </div>
          )}
        </section>
      </div>
    </div>
  );
};

export default ReportDetails;