import React, {
  useState,
} from "react";

import {
  AlertCircle,
  ArrowLeft,
  CheckCircle2,
  Image as ImageIcon,
  RefreshCw,
  Save,
  Upload,
  X,
} from "lucide-react";

import {
  Link,
  useNavigate,
} from "react-router-dom";

import {
  createMedicine,
} from "../../../services/medicineApi";

import "./AddMedicine.css";

const AddMedicine = () => {
  const navigate = useNavigate();

  const [formData, setFormData] =
    useState({
      medicine_name: "",
      company_name: "",
      short_description: "",
      mg: "",
      available_quantity: "",
    });

  const [medicinePhoto, setMedicinePhoto] =
    useState(null);

  const [previewUrl, setPreviewUrl] =
    useState("");

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState("");

  const [success, setSuccess] =
    useState("");

  const handleChange = (event) => {
    const {
      name,
      value,
    } = event.target;

    setFormData((current) => ({
      ...current,
      [name]: value,
    }));

    setError("");
    setSuccess("");
  };

  const handlePhotoChange = (
    event
  ) => {
    const file =
      event.target.files?.[0];

    if (!file) {
      return;
    }

    setMedicinePhoto(file);

    setPreviewUrl(
      URL.createObjectURL(file)
    );

    setError("");
    setSuccess("");
  };

  const removePhoto = () => {
    if (
      previewUrl &&
      previewUrl.startsWith("blob:")
    ) {
      URL.revokeObjectURL(
        previewUrl
      );
    }

    setMedicinePhoto(null);
    setPreviewUrl("");
  };

  const handleSubmit = async (
    event
  ) => {
    event.preventDefault();

    setError("");
    setSuccess("");

    if (!formData.medicine_name.trim()) {
      setError(
        "Please enter the medicine name."
      );
      return;
    }

    if (!formData.company_name.trim()) {
      setError(
        "Please enter the company name."
      );
      return;
    }

    if (!formData.mg.trim()) {
      setError(
        "Please enter the dosage."
      );
      return;
    }

    if (
      formData.available_quantity === ""
    ) {
      setError(
        "Please enter the available quantity."
      );
      return;
    }

    const quantity = Number(
      formData.available_quantity
    );

    if (
      Number.isNaN(quantity) ||
      quantity < 0
    ) {
      setError(
        "Available quantity must be 0 or more."
      );
      return;
    }

    const payload =
      new FormData();

    payload.append(
      "medicine_name",
      formData.medicine_name.trim()
    );

    payload.append(
      "company_name",
      formData.company_name.trim()
    );

    payload.append(
      "short_description",
      formData.short_description.trim()
    );

    payload.append(
      "mg",
      formData.mg.trim()
    );

    payload.append(
      "available_quantity",
      String(quantity)
    );

    if (medicinePhoto) {
      payload.append(
        "medicine_photo",
        medicinePhoto
      );
    }

    try {
      setLoading(true);

      await createMedicine(
        payload
      );

      setSuccess(
        "Medicine added successfully."
      );

      setTimeout(() => {
        navigate(
          "/pharmacy/medicines"
        );
      }, 900);
    } catch (err) {
      console.error(
        "Create medicine error:",
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
          "Could not add the medicine."
        );
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="add-medicine-page">
      <Link
        to="/pharmacy/medicines"
        className="add-medicine-back"
      >
        <ArrowLeft size={16} />
        Back to Medicines
      </Link>

      <header className="add-medicine-header">
        <div>
          <span className="add-medicine-kicker">
            Inventory
          </span>

          <h1>
            Add Medicine
          </h1>

          <p>
            Add a new medicine to your
            pharmacy inventory.
          </p>
        </div>
      </header>

      <form
        className="add-medicine-form"
        onSubmit={handleSubmit}
      >
        <section className="add-medicine-panel">
          <div className="add-medicine-panel-header">
            <h2>
              Medicine information
            </h2>

            <p>
              Enter the basic medicine
              and stock details.
            </p>
          </div>

          <div className="add-medicine-grid">
            <label className="add-medicine-field">
              <span>
                Medicine name
              </span>

              <input
                type="text"
                name="medicine_name"
                value={
                  formData.medicine_name
                }
                onChange={
                  handleChange
                }
                placeholder="e.g. Paracetamol"
              />
            </label>

            <label className="add-medicine-field">
              <span>
                Company name
              </span>

              <input
                type="text"
                name="company_name"
                value={
                  formData.company_name
                }
                onChange={
                  handleChange
                }
                placeholder="e.g. Nepal Pharma"
              />
            </label>

            <label className="add-medicine-field">
              <span>
                Dosage
              </span>

              <input
                type="text"
                name="mg"
                value={
                  formData.mg
                }
                onChange={
                  handleChange
                }
                placeholder="e.g. 500 mg"
              />
            </label>

            <label className="add-medicine-field">
              <span>
                Available quantity
              </span>

              <input
                type="number"
                min="0"
                name="available_quantity"
                value={
                  formData.available_quantity
                }
                onChange={
                  handleChange
                }
                placeholder="e.g. 25"
              />
            </label>

            <label className="add-medicine-field add-medicine-field-full">
              <span>
                Description
              </span>

              <textarea
                name="short_description"
                value={
                  formData.short_description
                }
                onChange={
                  handleChange
                }
                placeholder="Short description of the medicine"
                rows={5}
              />
            </label>
          </div>
        </section>

        <section className="add-medicine-panel">
          <div className="add-medicine-panel-header">
            <h2>
              Medicine photo
            </h2>

            <p>
              Add an optional medicine
              image.
            </p>
          </div>

          {!previewUrl ? (
            <label className="add-medicine-upload">
              <div>
                <Upload size={25} />
              </div>

              <strong>
                Upload medicine image
              </strong>

              <span>
                Choose an image from
                your device.
              </span>

              <input
                type="file"
                accept="image/*"
                hidden
                onChange={
                  handlePhotoChange
                }
              />
            </label>
          ) : (
            <div className="add-medicine-preview">
              <img
                src={previewUrl}
                alt="Medicine preview"
              />

              <div className="add-medicine-preview-footer">
                <div>
                  <ImageIcon
                    size={17}
                  />

                  <span>
                    {medicinePhoto?.name}
                  </span>
                </div>

                <button
                  type="button"
                  onClick={
                    removePhoto
                  }
                  className="add-medicine-remove"
                >
                  <X size={15} />
                  Remove
                </button>
              </div>
            </div>
          )}
        </section>

        {error && (
          <div className="add-medicine-message error">
            <AlertCircle
              size={18}
            />

            <span>
              {error}
            </span>
          </div>
        )}

        {success && (
          <div className="add-medicine-message success">
            <CheckCircle2
              size={18}
            />

            <span>
              {success}
            </span>
          </div>
        )}

        <div className="add-medicine-actions">
          <Link
            to="/pharmacy/medicines"
            className="add-medicine-cancel"
          >
            Cancel
          </Link>

          <button
            type="submit"
            className="add-medicine-save"
            disabled={loading}
          >
            {loading ? (
              <>
                <RefreshCw
                  size={17}
                  className="add-medicine-spinner"
                />
                Saving...
              </>
            ) : (
              <>
                <Save size={17} />
                Add Medicine
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

export default AddMedicine;