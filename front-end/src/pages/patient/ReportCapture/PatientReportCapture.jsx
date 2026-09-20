import React, {
  useCallback,
  useRef,
  useState,
} from "react";

import {
  Camera,
  CheckCircle2,
  FileImage,
  RefreshCw,
  Upload,
  X,
} from "lucide-react";

import Webcam from "react-webcam";
import { Link } from "react-router-dom";

import {
  createPatientReport,
} from "../../../services/reportApi";

import "./PatientReportCapture.css";

const PatientReportCapture = () => {
  const webcamRef = useRef(null);

  const [reportName, setReportName] =
    useState("");

  const [reportDate, setReportDate] =
    useState("");

  const [selectedFile, setSelectedFile] =
    useState(null);

  const [previewUrl, setPreviewUrl] =
    useState("");

  const [cameraOpen, setCameraOpen] =
    useState(false);

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState("");

  const [success, setSuccess] =
    useState("");

  const handleFileSelect = (event) => {
    const file =
      event.target.files?.[0];

    if (!file) {
      return;
    }

    setSelectedFile(file);
    setPreviewUrl(
      URL.createObjectURL(file)
    );

    setCameraOpen(false);
    setError("");
    setSuccess("");
  };

  const capturePhoto =
    useCallback(() => {
      const imageSrc =
        webcamRef.current?.getScreenshot();

      if (!imageSrc) {
        setError(
          "Could not capture the image."
        );

        return;
      }

      fetch(imageSrc)
        .then((response) =>
          response.blob()
        )
        .then((blob) => {
          const file = new File(
            [blob],
            `report-${Date.now()}.jpg`,
            {
              type:
                blob.type ||
                "image/jpeg",
            }
          );

          setSelectedFile(file);
          setPreviewUrl(imageSrc);
          setCameraOpen(false);

          setError("");
          setSuccess("");
        })
        .catch(() => {
          setError(
            "Could not prepare the captured image."
          );
        });
    }, []);

  const removeImage = () => {
    if (
      previewUrl &&
      previewUrl.startsWith(
        "blob:"
      )
    ) {
      URL.revokeObjectURL(
        previewUrl
      );
    }

    setSelectedFile(null);
    setPreviewUrl("");
  };

  const resetForm = () => {
    removeImage();

    setReportName("");
    setReportDate("");
    setCameraOpen(false);

    setError("");
    setSuccess("");
  };

  const handleSubmit = async (
    event
  ) => {
    event.preventDefault();

    setError("");
    setSuccess("");

    if (!reportName.trim()) {
      setError(
        "Please enter a report name."
      );

      return;
    }

    if (!reportDate) {
      setError(
        "Please select the report date."
      );

      return;
    }

    if (!selectedFile) {
      setError(
        "Please capture or upload a report image."
      );

      return;
    }

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
      "photo",
      selectedFile
    );

    try {
      setLoading(true);

      await createPatientReport(
        formData
      );

      setSuccess(
        "Report uploaded successfully."
      );

      removeImage();

      setReportName("");
      setReportDate("");
    } catch (err) {
      console.error(
        "Report upload error:",
        err
      );

      const responseData =
        err.response?.data;

      if (
        responseData &&
        typeof responseData ===
          "object"
      ) {
        const firstError =
          Object.values(
            responseData
          )[0];

        if (
          Array.isArray(firstError)
        ) {
          setError(
            firstError[0]
          );
        } else {
          setError(
            String(firstError)
          );
        }
      } else {
        setError(
          "Could not upload the report to the server."
        );
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="report-capture-page">
        <Link
  to="/patient/report-vault"
  className="report-capture-back"
>
  ← Back to Report Vault
</Link>
      <header className="report-capture-header">
        <div>
          <span className="report-capture-kicker">
            Medical Records
          </span>

          <h1>
            Report Capture
          </h1>

          <p>
            Capture a report using your
            camera or upload an image
            from your device.
          </p>
        </div>
      </header>

      <form
        className="report-capture-form"
        onSubmit={handleSubmit}
      >
        <section className="report-capture-panel">
          <div className="report-capture-panel-header">
            <div>
              <h2>
                Report details
              </h2>

              <p>
                Add basic information
                about this medical
                report.
              </p>
            </div>
          </div>

          <div className="report-form-grid">
            <label className="report-field">
              <span>
                Report name
              </span>

              <input
                type="text"
                value={reportName}
                onChange={(event) =>
                  setReportName(
                    event.target
                      .value
                  )
                }
                placeholder="e.g. Blood Test Report"
              />
            </label>

            <label className="report-field">
              <span>
                Report date
              </span>

              <input
                type="date"
                value={reportDate}
                onChange={(event) =>
                  setReportDate(
                    event.target
                      .value
                  )
                }
              />
            </label>
          </div>
        </section>

        <section className="report-capture-panel">
          <div className="report-capture-panel-header">
            <div>
              <h2>
                Report image
              </h2>

              <p>
                Use the camera or choose
                an image file.
              </p>
            </div>
          </div>

          {!previewUrl &&
            !cameraOpen && (
              <div className="report-source-grid">
                <button
                  type="button"
                  className="report-source-card"
                  onClick={() =>
                    setCameraOpen(
                      true
                    )
                  }
                >
                  <div>
                    <Camera
                      size={26}
                    />
                  </div>

                  <strong>
                    Use camera
                  </strong>

                  <span>
                    Take a clear photo
                    of the report.
                  </span>
                </button>

                <label className="report-source-card">
                  <div>
                    <Upload
                      size={26}
                    />
                  </div>

                  <strong>
                    Upload image
                  </strong>

                  <span>
                    Choose an existing
                    image from your
                    device.
                  </span>

                  <input
                    type="file"
                    accept="image/*"
                    onChange={
                      handleFileSelect
                    }
                    hidden
                  />
                </label>
              </div>
            )}

          {cameraOpen &&
            !previewUrl && (
              <div className="report-camera-container">
                <Webcam
                  ref={webcamRef}
                  audio={false}
                  screenshotFormat="image/jpeg"
                  videoConstraints={{
                    facingMode:
                      "environment",
                  }}
                  className="report-webcam"
                />

                <div className="report-camera-actions">
                  <button
                    type="button"
                    onClick={
                      capturePhoto
                    }
                    className="report-primary-button"
                  >
                    <Camera
                      size={17}
                    />

                    Capture
                  </button>

                  <button
                    type="button"
                    onClick={() =>
                      setCameraOpen(
                        false
                      )
                    }
                    className="report-secondary-button"
                  >
                    <X size={17} />

                    Cancel
                  </button>
                </div>
              </div>
            )}

          {previewUrl && (
            <div className="report-preview-container">
              <img
                src={previewUrl}
                alt="Selected medical report"
                className="report-preview-image"
              />

              <div className="report-preview-info">
                <div>
                  <FileImage
                    size={18}
                  />

                  <span>
                    {selectedFile?.name ||
                      "Captured report"}
                  </span>
                </div>

                <button
                  type="button"
                  onClick={
                    removeImage
                  }
                  className="report-remove-button"
                >
                  <X size={16} />

                  Remove
                </button>
              </div>
            </div>
          )}
        </section>

        {error && (
          <div className="report-capture-message error">
            {error}
          </div>
        )}

        {success && (
          <div className="report-capture-message success">
            <CheckCircle2
              size={18}
            />

            <span>
              {success}
            </span>
          </div>
        )}

        <div className="report-form-actions">
          <button
            type="button"
            onClick={resetForm}
            className="report-secondary-button"
            disabled={loading}
          >
            Reset
          </button>

          <button
            type="submit"
            className="report-primary-button"
            disabled={loading}
          >
            {loading ? (
              <>
                <RefreshCw
                  size={17}
                  className="report-button-spinner"
                />

                Uploading...
              </>
            ) : (
              <>
                <Upload
                  size={17}
                />

                Save Report
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

export default PatientReportCapture;