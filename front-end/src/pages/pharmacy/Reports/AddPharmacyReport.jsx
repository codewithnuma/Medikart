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
} from "react-router-dom";

import {
  createPharmacyReport,
} from "../../../services/reportApi";

import {
  getPatients,
} from "../../../services/patientApi";

import "./AddPharmacyReport.css";

const AddPharmacyReport = () => {
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

  const [loadingPatients, setLoadingPatients] =
    useState(true);

  const [submitting, setSubmitting] =
    useState(false);

  const [error, setError] =
    useState("");

  useEffect(() => {
    const loadPatients = async () => {
      try {
        setLoadingPatients(true);

        const response =
          await getPatients();

        const data =
          Array.isArray(response.data)
            ? response.data
            : response.data?.results || [];

        setPatients(data);
      } catch (err) {
        console.error(
          "Load patients error:",
          err
        );

        setError(
          "Could not load patients."
        );
      } finally {
        setLoadingPatients(false);
      }
    };

    loadPatients();
  }, []);

  const handleSubmit = async (event) => {
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

      await createPharmacyReport(
        formData
      );

      navigate(
        "/pharmacy/reports"
      );
    } catch (err) {
      console.error(
        "Create pharmacy report error:",
        err
      );

      setError(
        err.response?.data?.detail ||
          "Could not create this report."
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="add-pharmacy-report-page">
      <Link
        to="/pharmacy/reports"
        className="add-pharmacy-report-back"
      >
        <ArrowLeft size={16} />
        Back to Reports
      </Link>

      <header className="add-pharmacy-report-header">
        <span>
          Patient Records
        </span>

        <h1>
          Add Patient Report
        </h1>

        <p>
          Add a report for one of your
          patients.
        </p>
      </header>

      {error && (
        <div className="add-pharmacy-report-error">
          <AlertCircle size={17} />

          <span>
            {error}
          </span>
        </div>
      )}

      <form
        className="add-pharmacy-report-form"
        onSubmit={handleSubmit}
      >
        <div className="add-pharmacy-report-field">
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
            disabled={loadingPatients}
          >
            <option value="">
              {loadingPatients
                ? "Loading patients..."
                : "Select patient"}
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

        <div className="add-pharmacy-report-field">
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
            placeholder="Example: Blood Test Report"
          />
        </div>

        <div className="add-pharmacy-report-field">
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

        <div className="add-pharmacy-report-field">
          <label htmlFor="reportPhoto">
            Report Image
          </label>

          <label
            htmlFor="reportPhoto"
            className="add-pharmacy-report-upload"
          >
            <FileImage size={20} />

            <span>
              {photo
                ? photo.name
                : "Choose report image"}
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
          className="add-pharmacy-report-submit"
          disabled={
            submitting ||
            loadingPatients
          }
        >
          <Save size={17} />

          {submitting
            ? "Saving..."
            : "Save Report"}
        </button>
      </form>
    </div>
  );
};

export default AddPharmacyReport;