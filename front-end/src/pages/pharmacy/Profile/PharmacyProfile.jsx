import React, {
  useEffect,
  useState,
} from "react";

import {
  AlertCircle,
  Camera,
  Save,
  UserRound,
} from "lucide-react";

import {
  getCurrentUser,
  getProfile,
  updateProfile,
} from "../../../services/profileApi";

import "./PharmacyProfile.css";

const PharmacyProfile = () => {
  const [user, setUser] =
    useState(null);

  const [formData, setFormData] =
    useState({
      phone_number: "",
      location: "",
      bio: "",
    });

  const [profileImage, setProfileImage] =
    useState(null);

  const [preview, setPreview] =
    useState("");

  const [loading, setLoading] =
    useState(true);

  const [saving, setSaving] =
    useState(false);

  const [error, setError] =
    useState("");

  const [success, setSuccess] =
    useState("");

  useEffect(() => {
    const loadProfile = async () => {
      try {
        setLoading(true);
        setError("");

        const [
          userResponse,
          profileResponse,
        ] = await Promise.all([
          getCurrentUser(),
          getProfile(),
        ]);

        setUser(
          userResponse.data
        );

        const profile =
          profileResponse.data;

        setFormData({
          phone_number:
            profile.phone_number || "",
          location:
            profile.location || "",
          bio:
            profile.bio || "",
        });

        setPreview(
          profile.profile_image || ""
        );
      } catch (err) {
        console.error(
          "Load pharmacy profile error:",
          err
        );

        setError(
          "Could not load pharmacy profile."
        );
      } finally {
        setLoading(false);
      }
    };

    loadProfile();
  }, []);

  const handleChange = (event) => {
    const {
      name,
      value,
    } = event.target;

    setFormData(
      (current) => ({
        ...current,
        [name]: value,
      })
    );
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

    setPreview(
      URL.createObjectURL(file)
    );
  };

  const handleSubmit = async (
    event
  ) => {
    event.preventDefault();

    try {
      setSaving(true);
      setError("");
      setSuccess("");

      const data =
        new FormData();

      data.append(
        "phone_number",
        formData.phone_number
      );

      data.append(
        "location",
        formData.location
      );

      data.append(
        "bio",
        formData.bio
      );

      if (profileImage) {
        data.append(
          "profile_image",
          profileImage
        );
      }

      await updateProfile(data);

      setSuccess(
        "Profile updated successfully."
      );

      setProfileImage(null);
    } catch (err) {
      console.error(
        "Update pharmacy profile error:",
        err
      );

      setError(
        err.response?.data?.detail ||
          "Could not update profile."
      );
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="pharmacy-profile-loading">
        Loading profile...
      </div>
    );
  }

  return (
    <div className="pharmacy-profile-page">
      <header className="pharmacy-profile-header">
        <span>
          Pharmacy Account
        </span>

        <h1>
          Profile
        </h1>

        <p>
          Manage your pharmacy account
          information.
        </p>
      </header>

      {error && (
        <div className="pharmacy-profile-error">
          <AlertCircle size={17} />

          <span>{error}</span>
        </div>
      )}

      {success && (
        <div className="pharmacy-profile-success">
          {success}
        </div>
      )}

      <form
        className="pharmacy-profile-form"
        onSubmit={handleSubmit}
      >
        <div className="pharmacy-profile-photo-section">
          <div className="pharmacy-profile-photo">
            {preview ? (
              <img
                src={preview}
                alt="Pharmacy profile"
              />
            ) : (
              <UserRound size={34} />
            )}
          </div>

          <label
            htmlFor="profileImage"
            className="pharmacy-profile-photo-button"
          >
            <Camera size={16} />
            Change Photo
          </label>

          <input
            id="profileImage"
            type="file"
            accept="image/*"
            onChange={
              handleImageChange
            }
            hidden
          />
        </div>

        <div className="pharmacy-profile-grid">
          <div className="pharmacy-profile-field">
            <label>
              Pharmacy Name
            </label>

            <input
              type="text"
              value={
                user?.username || ""
              }
              disabled
            />
          </div>

          <div className="pharmacy-profile-field">
            <label>
              Email
            </label>

            <input
              type="email"
              value={
                user?.email || ""
              }
              disabled
            />
          </div>

          <div className="pharmacy-profile-field">
            <label htmlFor="phone_number">
              Phone Number
            </label>

            <input
              id="phone_number"
              name="phone_number"
              type="text"
              value={
                formData.phone_number
              }
              onChange={
                handleChange
              }
              placeholder="Enter phone number"
            />
          </div>

          <div className="pharmacy-profile-field">
            <label htmlFor="location">
              Location
            </label>

            <input
              id="location"
              name="location"
              type="text"
              value={
                formData.location
              }
              onChange={
                handleChange
              }
              placeholder="Enter pharmacy location"
            />
          </div>

          <div className="pharmacy-profile-field pharmacy-profile-full">
            <label htmlFor="bio">
              About Pharmacy
            </label>

            <textarea
              id="bio"
              name="bio"
              rows={4}
              value={
                formData.bio
              }
              onChange={
                handleChange
              }
              placeholder="Write a short description about your pharmacy..."
            />
          </div>
        </div>

        <button
          type="submit"
          className="pharmacy-profile-save"
          disabled={saving}
        >
          <Save size={17} />

          {saving
            ? "Saving..."
            : "Save Changes"}
        </button>
      </form>
    </div>
  );
};

export default PharmacyProfile;