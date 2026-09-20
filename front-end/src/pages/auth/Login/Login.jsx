import React, { useState } from "react";
import { useFormik } from "formik";
import * as Yup from "yup";
import {
  Button,
  Form,
  Input,
  message,
} from "antd";

import {
  ArrowRight,
  CalendarDays,
  FileText,
  HeartPulse,
  LockKeyhole,
  Mail,
  ShieldCheck,
  ShoppingBag,
} from "lucide-react";

import {
  Link,
  useNavigate,
} from "react-router-dom";

import { useAuth } from "../../../context/AuthContext";

import "./Login.css";

const Login = () => {
  const [loading, setLoading] =
    useState(false);

  const navigate = useNavigate();

  const { login } = useAuth();

  const formik = useFormik({
    initialValues: {
      email: "",
      password: "",
    },

    validationSchema: Yup.object({
      email: Yup.string()
        .email(
          "Enter a valid email address"
        )
        .required(
          "Email is required"
        ),

      password: Yup.string()
        .min(
          6,
          "Password must be at least 6 characters"
        )
        .required(
          "Password is required"
        ),
    }),

    onSubmit: async (values) => {
      setLoading(true);

      try {
        const result = await login(
          values.email
            .trim()
            .toLowerCase(),

          values.password
        );

        if (!result?.success) {
          message.error(
            result?.error ||
              "Unable to sign in."
          );

          return;
        }

        const loggedInUser =
          result.user;

        if (!loggedInUser) {
          message.error(
            "User information could not be loaded."
          );

          return;
        }

        const role = String(
          loggedInUser.role || ""
        )
          .trim()
          .toLowerCase();

        message.success(
          "Welcome back to NirogNepal."
        );

        if (role === "patient") {
          navigate(
            "/patient/dashboard",
            {
              replace: true,
            }
          );

          return;
        }

        if (role === "pharmacy") {
          navigate(
            "/pharmacy/dashboard",
            {
              replace: true,
            }
          );

          return;
        }

        if (role === "admin") {
          navigate(
            "/admin/dashboard",
            {
              replace: true,
            }
          );

          return;
        }

        message.error(
          "Your account role is not supported."
        );
      } catch (error) {
        console.error(
          "Login error:",
          error
        );

        const responseData =
          error?.response?.data;

        const errorMessage =
          responseData?.detail ||
          responseData?.message ||
          responseData
            ?.non_field_errors?.[0] ||
          "Unable to sign in.";

        message.error(
          errorMessage
        );
      } finally {
        setLoading(false);
      }
    },
  });

  const getFieldStatus = (
    field
  ) =>
    formik.touched[field] &&
    formik.errors[field]
      ? "error"
      : undefined;

  return (
    <main className="login-page">
      {/* LEFT SIDE */}

      <section className="login-panel">
        <div className="login-container">
          <div className="login-brand">
            <span className="login-brand-icon">
              <HeartPulse
                size={22}
              />
            </span>

            <span className="login-brand-name">
              Nirog
              <span>Nepal</span>
            </span>
          </div>

          <div className="login-heading">
            <div className="login-kicker">
              Secure patient portal
            </div>

            <h1>
              Welcome back.
            </h1>

            <p>
              Sign in to access
              your medical reports,
              appointments and pharmacy
              services.
            </p>
          </div>

          <Form
            layout="vertical"
            className="login-form"
            onFinish={() =>
              formik.handleSubmit()
            }
          >
            <Form.Item
              label={
                <span className="login-label">
                  Email address
                </span>
              }
              validateStatus=
                {getFieldStatus(
                  "email"
                )}
              help={
                formik.touched
                  .email &&
                formik.errors.email
              }
            >
              <Input
                name="email"
                type="email"
                autoComplete="email"
                placeholder=
                  "you@example.com"
                prefix={
                  <Mail
                    size={17}
                    className=
                      "login-input-icon"
                  />
                }
                value=
                  {formik.values.email}
                onChange=
                  {formik.handleChange}
                onBlur=
                  {formik.handleBlur}
                className=
                  "login-input"
              />
            </Form.Item>

            <Form.Item
              label={
                <span className="login-label">
                  Password
                </span>
              }
              validateStatus=
                {getFieldStatus(
                  "password"
                )}
              help={
                formik.touched
                  .password &&
                formik.errors
                  .password
              }
            >
              <Input.Password
                name="password"
                autoComplete=
                  "current-password"
                placeholder=
                  "Enter your password"
                prefix={
                  <LockKeyhole
                    size={17}
                    className=
                      "login-input-icon"
                  />
                }
                value={
                  formik.values
                    .password
                }
                onChange={
                  formik.handleChange
                }
                onBlur={
                  formik.handleBlur
                }
                className=
                  "login-input"
              />
            </Form.Item>

            <div className="login-form-links">
              <span />

              <Link
                to="/forgot-password"
                className=
                  "login-text-link"
              >
                Forgot password?
              </Link>
            </div>

            <Button
              htmlType="submit"
              loading={loading}
              disabled={loading}
              className=
                "login-submit"
              block
            >
              <span>
                Sign in
              </span>

              {!loading && (
                <ArrowRight
                  size={18}
                />
              )}
            </Button>
          </Form>

          <div className="login-signup">
            <span>
              Don't have an
              account?
            </span>

            <Link
              to="/signup"
              className=
                "login-text-link"
            >
              Create account
            </Link>
          </div>

          <div className=
            "login-security-note"
          >
            <ShieldCheck
              size={16}
            />

            <span>
              Protected by secure
              server authentication.
            </span>
          </div>
        </div>
      </section>

      {/* RIGHT SIDE */}

      <section className=
        "login-visual"
      >
        <div className=
          "login-visual-glow login-visual-glow-one"
        />

        <div className=
          "login-visual-glow login-visual-glow-two"
        />

        <div className=
          "login-visual-content"
        >
          <div className=
            "login-visual-badge"
          >
            <HeartPulse
              size={15}
            />

            <span>
              NirogNepal Healthcare
            </span>
          </div>

          <h2>
            Your healthcare,
            <br />
            connected.
          </h2>

          <p>
            Access important
            healthcare services
            through one connected
            platform.
          </p>

          <div className=
            "login-feature-grid"
          >
            <article className=
              "login-feature-card"
            >
              <div className=
                "login-feature-icon"
              >
                <FileText
                  size={20}
                />
              </div>

              <div>
                <strong>
                  Report Vault
                </strong>

                <span>
                  Access your
                  medical reports.
                </span>
              </div>
            </article>

            <article className=
              "login-feature-card"
            >
              <div className=
                "login-feature-icon"
              >
                <CalendarDays
                  size={20}
                />
              </div>

              <div>
                <strong>
                  Appointments
                </strong>

                <span>
                  Book and manage
                  consultations.
                </span>
              </div>
            </article>

            <article className=
              "login-feature-card"
            >
              <div className=
                "login-feature-icon"
              >
                <ShoppingBag
                  size={20}
                />
              </div>

              <div>
                <strong>
                  Pharmacy
                </strong>

                <span>
                  Connect with
                  participating
                  pharmacies.
                </span>
              </div>
            </article>
          </div>
        </div>
      </section>
    </main>
  );
};

export default Login;