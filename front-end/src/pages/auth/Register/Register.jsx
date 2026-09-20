import React, { useState } from "react";

import {
  AlertCircle,
  ArrowLeft,
  CheckCircle2,
  FileUp,
  UserPlus,
} from "lucide-react";

import { Link } from "react-router-dom";

import { registerAccount } from "../../../services/registrationApi";

import "./Register.css";

// ------------------------------------------------------------
// Small presentational helpers (same markup as before)
// ------------------------------------------------------------

const Field = ({ id, label, full = false, ...inputProps }) => (
  <div className={`register-field${full ? " register-full" : ""}`}>
    <label htmlFor={id}>{label}</label>
    <input id={id} name={id} {...inputProps} />
  </div>
);

const UploadField = ({
  label,
  file,
  placeholder,
  accept,
  onChange,
  full = false,
}) => (
  <div className={`register-field${full ? " register-full" : ""}`}>
    <label>{label}</label>

    <label className="register-upload">
      <FileUp size={19} />

      <span>{file ? file.name : placeholder}</span>

      <input
        type="file"
        accept={accept}
        onChange={(event) => onChange(event.target.files?.[0] || null)}
        hidden
      />
    </label>
  </div>
);

// ------------------------------------------------------------

const Register = () => {
  const [role, setRole] = useState("patient");

  const [formData, setFormData] = useState({
    username: "",
    email: "",
    phone_number: "",
    password: "",
    confirmPassword: "",
    citizenship_number: "",
    pharmacy_license_number: "",
  });

  const [citizenshipFront, setCitizenshipFront] = useState(null);
  const [citizenshipBack, setCitizenshipBack] = useState(null);
  const [pharmacyLicenseDocument, setPharmacyLicenseDocument] =
    useState(null);

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);

  const handleChange = (event) => {
    const { name, value } = event.target;

    setFormData((current) => ({
      ...current,
      [name]: value,
    }));
  };

  const getApiError = (err) => {
    const data = err.response?.data;

    if (!data) {
      return "Could not submit registration.";
    }

    if (typeof data === "string") {
      return data;
    }

    if (data.detail) {
      return data.detail;
    }

    const firstKey = Object.keys(data)[0];

    if (!firstKey) {
      return "Could not submit registration.";
    }

    const message = data[firstKey];

    if (Array.isArray(message)) {
      return message[0];
    }

    return String(message);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    setError("");

    if (
      !formData.username.trim() ||
      !formData.email.trim() ||
      !formData.password
    ) {
      setError("Please complete all required fields.");
      return;
    }

    if (formData.password.length < 6) {
      setError("Password must be at least 6 characters.");
      return;
    }

    if (formData.password !== formData.confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    if (role === "patient") {
      if (
        !formData.citizenship_number.trim() ||
        !citizenshipFront ||
        !citizenshipBack
      ) {
        setError(
          "Citizenship number and both citizenship images are required."
        );
        return;
      }
    }

    if (role === "pharmacy") {
      if (
        !formData.pharmacy_license_number.trim() ||
        !pharmacyLicenseDocument
      ) {
        setError(
          "Pharmacy licence number and licence document are required."
        );
        return;
      }
    }

    try {
      setSubmitting(true);

      const data = new FormData();

      data.append("username", formData.username.trim());
      data.append("email", formData.email.trim());
      data.append("password", formData.password);
      data.append("role", role);

      if (formData.phone_number.trim()) {
        data.append("phone_number", formData.phone_number.trim());
      }

      if (role === "patient") {
        data.append("citizenship_number", formData.citizenship_number.trim());
        data.append("citizenship_front", citizenshipFront);
        data.append("citizenship_back", citizenshipBack);
      }

      if (role === "pharmacy") {
        data.append(
          "pharmacy_license_number",
          formData.pharmacy_license_number.trim()
        );
        data.append("pharmacy_license_document", pharmacyLicenseDocument);
      }

      await registerAccount(data);

      setSuccess(true);
    } catch (err) {
      console.error("Registration error:", err);

      setError(getApiError(err));
    } finally {
      setSubmitting(false);
    }
  };

  // ----------------------------------------------------------
  // SUCCESS SCREEN
  // ----------------------------------------------------------

  if (success) {
    const isPharmacy = role === "pharmacy";

    return (
      <div className="register-page">
        <div className="register-success-card">
          <CheckCircle2 size={44} />

          {isPharmacy ? (
            <>
              <h1>Verifying Your Licence</h1>

              <p>
                We are checking your pharmacy registration number against the
                Nepal Pharmacy Council records.
              </p>

              <p>
                You will receive an email at{" "}
                <strong>{formData.email.trim()}</strong> shortly, telling you
                whether your Medicart account was approved or denied. If it
                is approved, you can log in with the email and password you
                registered with.
              </p>
            </>
          ) : (
            <>
              <h1>Registration Submitted</h1>

              <p>
                Your registration request has been sent for administrator
                approval.
              </p>

              <p>
                Once your account is approved, you can log in using the email
                and password you registered with.
              </p>
            </>
          )}

          <Link to="/login" className="register-login-link">
            Go to Login
          </Link>
        </div>
      </div>
    );
  }

  // ----------------------------------------------------------
  // FORM
  // ----------------------------------------------------------

  return (
    <div className="register-page">
      <div className="register-container">
        <Link to="/login" className="register-back">
          <ArrowLeft size={16} />
          Back to Login
        </Link>

        <header className="register-header">
          <span>Medicart</span>

          <h1>Create an Account</h1>

          <p>
            {role === "pharmacy"
              ? "Your pharmacy licence is verified automatically with the Nepal Pharmacy Council."
              : "Submit your details for verification and account approval."}
          </p>
        </header>

        {error && (
          <div className="register-error">
            <AlertCircle size={17} />

            <span>{error}</span>
          </div>
        )}

        <form className="register-form" onSubmit={handleSubmit}>
          <div className="register-role-section">
            <label>Register as</label>

            <div className="register-role-options">
              <button
                type="button"
                className={role === "patient" ? "active" : ""}
                onClick={() => setRole("patient")}
              >
                Patient
              </button>

              <button
                type="button"
                className={role === "pharmacy" ? "active" : ""}
                onClick={() => setRole("pharmacy")}
              >
                Pharmacy
              </button>
            </div>
          </div>

          <div className="register-grid">
            <Field
              id="username"
              label={role === "pharmacy" ? "Pharmacy Name *" : "Full Name *"}
              type="text"
              value={formData.username}
              onChange={handleChange}
            />

            <Field
              id="email"
              label="Email *"
              type="email"
              value={formData.email}
              onChange={handleChange}
            />

            <Field
              id="phone_number"
              label="Phone Number"
              full
              type="text"
              value={formData.phone_number}
              onChange={handleChange}
            />

            <Field
              id="password"
              label="Password *"
              type="password"
              value={formData.password}
              onChange={handleChange}
              minLength={6}
            />

            <Field
              id="confirmPassword"
              label="Confirm Password *"
              type="password"
              value={formData.confirmPassword}
              onChange={handleChange}
            />

            {role === "patient" && (
              <>
                <Field
                  id="citizenship_number"
                  label="Citizenship Number *"
                  full
                  type="text"
                  value={formData.citizenship_number}
                  onChange={handleChange}
                />

                <UploadField
                  label="Citizenship Front *"
                  file={citizenshipFront}
                  placeholder="Choose front image"
                  accept="image/*"
                  onChange={setCitizenshipFront}
                />

                <UploadField
                  label="Citizenship Back *"
                  file={citizenshipBack}
                  placeholder="Choose back image"
                  accept="image/*"
                  onChange={setCitizenshipBack}
                />
              </>
            )}

            {role === "pharmacy" && (
              <>
                <Field
                  id="pharmacy_license_number"
                  label="Pharmacy Licence Number *"
                  full
                  type="text"
                  value={formData.pharmacy_license_number}
                  onChange={handleChange}
                />

                <UploadField
                  label="Pharmacy Licence Document *"
                  full
                  file={pharmacyLicenseDocument}
                  placeholder="Choose licence document"
                  accept="image/*,.pdf"
                  onChange={setPharmacyLicenseDocument}
                />
              </>
            )}
          </div>

          <button
            type="submit"
            className="register-submit"
            disabled={submitting}
          >
            <UserPlus size={17} />

            {submitting ? "Submitting..." : "Submit Registration"}
          </button>

          <p className="register-existing-account">
            Already approved? <Link to="/login">Log in</Link>
          </p>
        </form>
      </div>
    </div>
  );
};

export default Register;