import React, {
  useEffect,
  useState,
} from "react";

import {
  AlertCircle,
  Camera,
  CheckCircle2,
  RefreshCw,
  Save,
  UserRound,
} from "lucide-react";

import { useAuth } from "../../../context/AuthContext";

import {
  getProfile,
  updateProfile,
} from "../../../services/profileApi";

import "./PatientProfile.css";

const PatientProfile = () => {
  const { user } = useAuth();

  const [profile, setProfile] =
    useState(null);

  const [formData, setFormData] =
    useState({
      bio: "",
      birth_date: "",
      location: "",
      phone_number: "",
    });

  const [profileImage, setProfileImage] =
    useState(null);

  const [previewUrl, setPreviewUrl] =
    useState("");

  const [loading, setLoading] =
    useState(true);

  const [saving, setSaving] =
    useState(false);

  const [error, setError] =
    useState("");

  const [success, setSuccess] =
    useState("");

  const loadProfile = async () => {
    try {
      setLoading(true);
      setError("");

      const response =
        await getProfile();

      const data = response.data;

      setProfile(data);

      setFormData({
        bio: data?.bio || "",
        birth_date:
          data?.birth_date || "",
        location:
          data?.location || "",
        phone_number:
          data?.phone_number || "",
      });

      setPreviewUrl(
        data?.profile_image_url || ""
      );
    } catch (err) {
      console.error(
        "Profile API error:",
        err
      );

      setError(
        "Could not load your profile."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProfile();
  }, []);

  const handleChange = (event) => {
    const {
      name,
      value,
    } = event.target;

    setFormData((current) => ({
      ...current,
      [name]: value,
    }));

    setSuccess("");
  };

  const handleImageChange = (
    event
  ) => {
    const file =
      event.target.files?.[0];

    if (!file) {
      return;
    }

    setProfileImage(file);

    setPreviewUrl(
      URL.createObjectURL(file)
    );

    setSuccess("");
  };

  const handleSubmit = async (
    event
  ) => {
    event.preventDefault();

    setSaving(true);
    setError("");
    setSuccess("");

    try {
      const payload =
        new FormData();

      payload.append(
        "bio",
        formData.bio
      );

      payload.append(
        "birth_date",
        formData.birth_date
      );

      payload.append(
        "location",
        formData.location
      );

      payload.append(
        "phone_number",
        formData.phone_number
      );

      if (profileImage) {
        payload.append(
          "profile_image",
          profileImage
        );
      }

      const response =
        await updateProfile(
          payload
        );

      setProfile(response.data);

      setPreviewUrl(
        response.data
          ?.profile_image_url ||
          previewUrl
      );

      setProfileImage(null);

      setSuccess(
        "Profile updated successfully."
      );
    } catch (err) {
      console.error(
        "Profile update error:",
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
          "Could not update your profile."
        );
      }
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="profile-loading">
        <RefreshCw
          size={28}
          className="profile-spinner"
        />

        <span>
          Loading your profile...
        </span>
      </div>
    );
  }

  const displayName =
    user?.username ||
    user?.email ||
    "Patient";

  return (
    <div className="patient-profile-page">
      <header className="profile-page-header">
        <div>
          <span className="profile-kicker">
            Account
          </span>

          <h1>Profile</h1>

          <p>
            Manage your personal
            information stored in
            NirogNepal.
          </p>
        </div>

        <button
          type="button"
          onClick={loadProfile}
          className="profile-refresh-button"
        >
          <RefreshCw size={17} />
          Refresh
        </button>
      </header>

      <form
        className="profile-layout"
        onSubmit={handleSubmit}
      >
        <aside className="profile-card">
          <div className="profile-avatar-wrap">
            {previewUrl ? (
              <img
                src={previewUrl}
                alt="Profile"
                className="profile-avatar-image"
              />
            ) : (
              <div className="profile-avatar-placeholder">
                <UserRound
                  size={42}
                />
              </div>
            )}

            <label className="profile-image-button">
              <Camera size={15} />

              Change photo

              <input
                type="file"
                accept="image/*"
                hidden
                onChange={
                  handleImageChange
                }
              />
            </label>
          </div>

          <div className="profile-card-info">
            <h2>
              {displayName}
            </h2>

            <span>
              {profile?.email ||
                user?.email}
            </span>

            <div className="profile-role-badge">
              Patient
            </div>
          </div>
        </aside>

        <section className="profile-form-card">
          <div className="profile-form-header">
            <h2>
              Personal information
            </h2>

            <p>
  Keep your personal details
  accurate and up to date.
</p>
          </div>

          <div className="profile-form-grid">
            <label className="profile-field">
              <span>Email</span>

              <input
                type="email"
                value={
                  profile?.email || ""
                }
                readOnly
                className="profile-readonly-input"
              />
            </label>

            <label className="profile-field">
              <span>
                Phone number
              </span>

              <input
                type="text"
                name="phone_number"
                value={
                  formData.phone_number
                }
                onChange={handleChange}
                placeholder="Enter phone number"
              />
            </label>

            <label className="profile-field">
              <span>
                Birth date
              </span>

              <input
                type="date"
                name="birth_date"
                value={
                  formData.birth_date
                }
                onChange={handleChange}
              />
            </label>

            <label className="profile-field">
              <span>Location</span>

              <input
                type="text"
                name="location"
                value={
                  formData.location
                }
                onChange={handleChange}
                placeholder="Enter your location"
              />
            </label>

            <label className="profile-field profile-field-full">
              <span>Bio</span>

              <textarea
                name="bio"
                value={formData.bio}
                onChange={handleChange}
                placeholder="Tell us a little about yourself"
                rows={5}
              />
            </label>
          </div>

          {error && (
            <div className="profile-message error">
              <AlertCircle
                size={18}
              />

              <span>{error}</span>
            </div>
          )}

          {success && (
            <div className="profile-message success">
              <CheckCircle2
                size={18}
              />

              <span>
                {success}
              </span>
            </div>
          )}

          <div className="profile-form-actions">
            <button
              type="submit"
              className="profile-save-button"
              disabled={saving}
            >
              {saving ? (
                <>
                  <RefreshCw
                    size={17}
                    className="profile-button-spinner"
                  />

                  Saving...
                </>
              ) : (
                <>
                  <Save size={17} />

                  Save changes
                </>
              )}
            </button>
          </div>
        </section>
      </form>
    </div>
  );
};

export default PatientProfile;