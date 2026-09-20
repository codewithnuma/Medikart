import React, {
  useEffect,
  useState,
} from "react";

import {
  AlertCircle,
  ArrowLeft,
  FileImage,
  Save,
} from "lucide-react";

import {
  Link,
  useNavigate,
  useParams,
} from "react-router-dom";

import {
  getPharmacyReport,
  updatePharmacyReport,
} from "../../../services/reportApi";

import {
  getPatients,
} from "../../../services/patientApi";

import "./EditPharmacyReport.css";

const EditPharmacyReport = () => {
  const { id } = useParams();

  const navigate = useNavigate();

  const [patients, setPatients] =
    useState([]);

  const [reportName, setReportName] =
    useState("");

  const [reportDate, setReportDate] =
    useState("");

  const [patientId, setPatientId] =
    useState("");

  const [photo, setPhoto] =
    useState(null);

  const [currentPhoto, setCurrentPhoto] =
    useState("");

  const [loading, setLoading] =
    useState(true);

  const [submitting, setSubmitting] =
    useState(false);

  const [error, setError] =
    useState("");

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        setError("");

        const [
          reportResponse,
          patientsResponse,
        ] = await Promise.all([
          getPharmacyReport(id),
          getPatients(),
        ]);

        const report =
          reportResponse.data;

        const patientData =
          Array.isArray(
            patientsResponse.data
          )
            ? patientsResponse.data
            : patientsResponse.data
                ?.results || [];

        setPatients(patientData);

        setReportName(
          report.report_name || ""
        );

        setReportDate(
          report.date || ""
        );

        setPatientId(
          String(
            report.patient || ""
          )
        );

        setCurrentPhoto(
          report.photo || ""
        );
      } catch (err) {
        console.error(
          "Load pharmacy report error:",
          err
        );

        setError(
          "Could not load this report."
        );
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [id]);

  const handleSubmit = async (
    event
  ) => {
    event.preventDefault();

    if (
      !reportName.trim() ||
      !reportDate ||
      !patientId
    ) {
      setError(
        "Please complete all required fields."
      );

      return;
    }

    try {
      setSubmitting(true);
      setError("");

      const formData =
        new FormData();

      formData.append(
        "report_name",
        reportName.trim()
      );

      formData.append(
        "date",
        reportDate
      );

      formData.append(
        "patient",
        patientId
      );

      if (photo) {
        formData.append(
          "photo",
          photo
        );
      }

      await updatePharmacyReport(
        id,
        formData
      );

      navigate(
        "/pharmacy/reports"
      );
    } catch (err) {
      console.error(
        "Update pharmacy report error:",
        err
      );

      setError(
        err.response?.data?.detail ||
          "Could not update this report."
      );
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div>
        Loading report...
      </div>
    );
  }

  return (
    <div className="edit-pharmacy-report-page">
      <Link
        to="/pharmacy/reports"
        className="edit-pharmacy-report-back"
      >
        <ArrowLeft size={16} />
        Back to Reports
      </Link>

      <header className="edit-pharmacy-report-header">
        <span>
          Patient Records
        </span>

        <h1>
          Edit Report
        </h1>

        <p>
          Update a report created by
          your pharmacy.
        </p>
      </header>

      {error && (
        <div className="edit-pharmacy-report-error">
          <AlertCircle size={17} />

          <span>
            {error}
          </span>
        </div>
      )}

      <form
        className="edit-pharmacy-report-form"
        onSubmit={handleSubmit}
      >
        <div className="edit-pharmacy-report-field">
          <label htmlFor="patient">
            Patient *
          </label>

          <select
            id="patient"
            value={patientId}
            onChange={(event) =>
              setPatientId(
                event.target.value
              )
            }
          >
            <option value="">
              Select patient
            </option>

            {patients.map(
              (patient) => (
                <option
                  key={patient.id}
                  value={patient.id}
                >
                  {patient.username}
                  {patient.email
                    ? ` — ${patient.email}`
                    : ""}
                </option>
              )
            )}
          </select>
        </div>

        <div className="edit-pharmacy-report-field">
          <label htmlFor="reportName">
            Report Name *
          </label>

          <input
            id="reportName"
            type="text"
            value={reportName}
            onChange={(event) =>
              setReportName(
                event.target.value
              )
            }
          />
        </div>

        <div className="edit-pharmacy-report-field">
          <label htmlFor="reportDate">
            Report Date *
          </label>

          <input
            id="reportDate"
            type="date"
            value={reportDate}
            onChange={(event) =>
              setReportDate(
                event.target.value
              )
            }
          />
        </div>

        <div className="edit-pharmacy-report-field">
          <label>
            Report Image
          </label>

          {currentPhoto && !photo && (
            <a
              href={currentPhoto}
              target="_blank"
              rel="noreferrer"
              className="edit-pharmacy-report-current-photo"
            >
              <FileImage size={16} />
              View Current Image
            </a>
          )}

          <label
            htmlFor="reportPhoto"
            className="edit-pharmacy-report-upload"
          >
            <FileImage size={20} />

            <span>
              {photo
                ? photo.name
                : "Choose new image"}
            </span>
          </label>

          <input
            id="reportPhoto"
            type="file"
            accept="image/*"
            onChange={(event) =>
              setPhoto(
                event.target.files?.[0] ||
                  null
              )
            }
            hidden
          />
        </div>

        <button
          type="submit"
          className="edit-pharmacy-report-submit"
          disabled={submitting}
        >
          <Save size={17} />

          {submitting
            ? "Saving..."
            : "Save Changes"}
        </button>
      </form>
    </div>
  );
};

export default EditPharmacyReport;