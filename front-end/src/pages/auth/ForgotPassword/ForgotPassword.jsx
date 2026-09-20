import React, {
  useState,
} from "react";

import {
  ArrowLeft,
  CheckCircle2,
  KeyRound,
  Mail,
  ShieldCheck,
} from "lucide-react";

import {
  Link,
  useNavigate,
} from "react-router-dom";

import axiosInstance from "../../../axiosInstance";

import "./ForgotPassword.css";

const ForgotPassword = () => {
  const navigate = useNavigate();

  const [step, setStep] =
    useState(1);

  const [email, setEmail] =
    useState("");

  const [otp, setOtp] =
    useState("");

  const [
    newPassword,
    setNewPassword,
  ] = useState("");

  const [
    confirmPassword,
    setConfirmPassword,
  ] = useState("");

  const [message, setMessage] =
    useState("");

  const [error, setError] =
    useState("");

  const [loading, setLoading] =
    useState(false);

  const getErrorMessage = (
    err,
    fallback
  ) => {
    const data =
      err.response?.data;

    if (!data) {
      return fallback;
    }

    if (typeof data === "string") {
      return data;
    }

    if (data.detail) {
      return data.detail;
    }

    if (data.email) {
      return Array.isArray(data.email)
        ? data.email[0]
        : data.email;
    }

    if (data.otp) {
      return Array.isArray(data.otp)
        ? data.otp[0]
        : data.otp;
    }

    const firstKey =
      Object.keys(data)[0];

    if (!firstKey) {
      return fallback;
    }

    const value =
      data[firstKey];

    return Array.isArray(value)
      ? value[0]
      : String(value);
  };

  const handleSendOTP = async (
    event
  ) => {
    event.preventDefault();

    if (!email.trim()) {
      setError(
        "Please enter your email address."
      );

      return;
    }

    try {
      setLoading(true);
      setError("");
      setMessage("");

      const response =
        await axiosInstance.post(
          "/accounts/forgot-password/",
          {
            email: email.trim(),
          }
        );

      setMessage(
        response.data?.message ||
          "Verification code sent to your email."
      );

      setStep(2);
    } catch (err) {
      console.error(
        "Forgot password error:",
        err
      );

      setError(
        getErrorMessage(
          err,
          "Failed to send verification code."
        )
      );
    } finally {
      setLoading(false);
    }
  };

  const handleResetPassword = async (
    event
  ) => {
    event.preventDefault();

    if (!otp.trim()) {
      setError(
        "Please enter the verification code."
      );

      return;
    }

    if (
      newPassword.length < 6
    ) {
      setError(
        "Password must be at least 6 characters."
      );

      return;
    }

    if (
      newPassword !==
      confirmPassword
    ) {
      setError(
        "Passwords do not match."
      );

      return;
    }

    try {
      setLoading(true);
      setError("");
      setMessage("");

      const response =
        await axiosInstance.post(
          "/accounts/reset-password/",
          {
            email: email.trim(),
            otp: otp.trim(),
            new_password:
              newPassword,
          }
        );

      setMessage(
        response.data?.message ||
          "Password changed successfully."
      );

      setStep(3);
    } catch (err) {
      console.error(
        "Reset password error:",
        err
      );

      setError(
        getErrorMessage(
          err,
          "Invalid verification code or password reset failed."
        )
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="forgot-password-page">
      <div className="forgot-password-card">
        {step < 3 && (
          <Link
            to="/login"
            className="forgot-password-back"
          >
            <ArrowLeft size={16} />
            Back to Login
          </Link>
        )}

        <header className="forgot-password-header">
          <span>
            NirogNepal
          </span>

          <h1>
            {step === 3
              ? "Password Reset"
              : "Reset Password"}
          </h1>

          <p>
            {step === 1 &&
              "Enter your registered email address to receive a verification code."}

            {step === 2 &&
              "Enter the code sent to your email and choose a new password."}

            {step === 3 &&
              "Your password has been updated successfully."}
          </p>
        </header>

        <div className="forgot-password-progress">
          <div
            className={`forgot-password-progress-step ${
              step >= 1
                ? "active"
                : ""
            }`}
          >
            <Mail size={16} />

            <span>
              Email
            </span>
          </div>

          <div
            className={`forgot-password-progress-line ${
              step >= 2
                ? "active"
                : ""
            }`}
          />

          <div
            className={`forgot-password-progress-step ${
              step >= 2
                ? "active"
                : ""
            }`}
          >
            <ShieldCheck size={16} />

            <span>
              Verify
            </span>
          </div>

          <div
            className={`forgot-password-progress-line ${
              step >= 3
                ? "active"
                : ""
            }`}
          />

          <div
            className={`forgot-password-progress-step ${
              step >= 3
                ? "active"
                : ""
            }`}
          >
            <CheckCircle2 size={16} />

            <span>
              Done
            </span>
          </div>
        </div>

        {message && (
          <div className="forgot-password-message success">
            {message}
          </div>
        )}

        {error && (
          <div className="forgot-password-message error">
            {error}
          </div>
        )}

        {step === 1 && (
          <form
            className="forgot-password-form"
            onSubmit={
              handleSendOTP
            }
          >
            <div className="forgot-password-field">
              <label htmlFor="email">
                Email Address
              </label>

              <div className="forgot-password-input-wrap">
                <Mail size={17} />

                <input
                  id="email"
                  type="email"
                  placeholder="your@email.com"
                  value={email}
                  onChange={(event) =>
                    setEmail(
                      event.target.value
                    )
                  }
                  autoComplete="email"
                />
              </div>
            </div>

            <button
              type="submit"
              className="forgot-password-submit"
              disabled={
                loading ||
                !email.trim()
              }
            >
              {loading
                ? "Sending..."
                : "Send Verification Code"}
            </button>
          </form>
        )}

        {step === 2 && (
          <form
            className="forgot-password-form"
            onSubmit={
              handleResetPassword
            }
          >
            <div className="forgot-password-field">
              <label htmlFor="otp">
                Verification Code
              </label>

              <div className="forgot-password-input-wrap">
                <ShieldCheck
                  size={17}
                />

                <input
                  id="otp"
                  type="text"
                  inputMode="numeric"
                  placeholder="000000"
                  value={otp}
                  onChange={(event) =>
                    setOtp(
                      event.target.value
                    )
                  }
                  maxLength={6}
                />
              </div>

              <small>
                Enter the 6-digit code
                sent to {email}.
              </small>
            </div>

            <div className="forgot-password-field">
              <label htmlFor="newPassword">
                New Password
              </label>

              <div className="forgot-password-input-wrap">
                <KeyRound size={17} />

                <input
                  id="newPassword"
                  type="password"
                  value={
                    newPassword
                  }
                  onChange={(event) =>
                    setNewPassword(
                      event.target.value
                    )
                  }
                  placeholder="Enter new password"
                  autoComplete="new-password"
                />
              </div>
            </div>

            <div className="forgot-password-field">
              <label htmlFor="confirmPassword">
                Confirm Password
              </label>

              <div className="forgot-password-input-wrap">
                <KeyRound size={17} />

                <input
                  id="confirmPassword"
                  type="password"
                  value={
                    confirmPassword
                  }
                  onChange={(event) =>
                    setConfirmPassword(
                      event.target.value
                    )
                  }
                  placeholder="Repeat new password"
                  autoComplete="new-password"
                />
              </div>
            </div>

            <button
              type="submit"
              className="forgot-password-submit"
              disabled={
                loading ||
                !otp.trim() ||
                !newPassword ||
                !confirmPassword
              }
            >
              {loading
                ? "Resetting..."
                : "Reset Password"}
            </button>
          </form>
        )}

        {step === 3 && (
          <div className="forgot-password-success">
            <div className="forgot-password-success-icon">
              <CheckCircle2
                size={34}
              />
            </div>

            <h2>
              Password Reset Successful
            </h2>

            <p>
              You can now log in using
              your new password.
            </p>

            <button
              type="button"
              className="forgot-password-submit"
              onClick={() =>
                navigate("/login")
              }
            >
              Return to Login
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default ForgotPassword;