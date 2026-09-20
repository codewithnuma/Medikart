import React, {
  useEffect,
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
  useParams,
} from "react-router-dom";

import {
  getMedicine,
  updateMedicine,
} from "../../../services/medicineApi";

import "./EditMedicine.css";

const EditMedicine = () => {
  const { id } = useParams();
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
    useState(true);

  const [saving, setSaving] =
    useState(false);

  const [error, setError] =
    useState("");

  const [success, setSuccess] =
    useState("");

  const loadMedicine = async () => {
    try {
      setLoading(true);
      setError("");

      const response =
        await getMedicine(id);

      const medicine = response.data;

      setFormData({
        medicine_name:
          medicine.medicine_name || "",

        company_name:
          medicine.company_name || "",

        short_description:
          medicine.short_description || "",

        mg:
          medicine.mg || "",

        available_quantity:
          medicine.available_quantity ?? "",
      });

      setPreviewUrl(
        medicine.medicine_photo || ""
      );
    } catch (err) {
      console.error(
        "Load medicine error:",
        err
      );

      setError(
        "Could not load this medicine."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMedicine();
  }, [id]);

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

    if (
      previewUrl &&
      previewUrl.startsWith("blob:")
    ) {
      URL.revokeObjectURL(
        previewUrl
      );
    }

    setMedicinePhoto(file);

    setPreviewUrl(
      URL.createObjectURL(file)
    );

    setError("");
    setSuccess("");
  };

  const removeNewPhoto = () => {
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
      setSaving(true);

      await updateMedicine(
        id,
        payload
      );

      setSuccess(
        "Medicine updated successfully."
      );

      setTimeout(() => {
        navigate(
          "/pharmacy/medicines"
        );
      }, 900);
    } catch (err) {
      console.error(
        "Update medicine error:",
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
          "Could not update the medicine."
        );
      }
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="edit-medicine-loading">
        <RefreshCw
          size={28}
          className="edit-medicine-spinner"
        />

        <span>
          Loading medicine...
        </span>
      </div>
    );
  }

  return (
    <div className="edit-medicine-page">
      <Link
        to="/pharmacy/medicines"
        className="edit-medicine-back"
      >
        <ArrowLeft size={16} />
        Back to Medicines
      </Link>

      <header className="edit-medicine-header">
        <div>
          <span className="edit-medicine-kicker">
            Inventory
          </span>

          <h1>
            Edit Medicine
          </h1>

          <p>
            Update medicine details
            and available stock.
          </p>
        </div>
      </header>

      <form
        className="edit-medicine-form"
        onSubmit={handleSubmit}
      >
        <section className="edit-medicine-panel">
          <div className="edit-medicine-panel-header">
            <h2>
              Medicine information
            </h2>

            <p>
              Update the information
              stored for this medicine.
            </p>
          </div>

          <div className="edit-medicine-grid">
            <label className="edit-medicine-field">
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
              />
            </label>

            <label className="edit-medicine-field">
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
              />
            </label>

            <label className="edit-medicine-field">
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
              />
            </label>

            <label className="edit-medicine-field">
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
              />
            </label>

            <label className="edit-medicine-field edit-medicine-field-full">
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
                rows={5}
              />
            </label>
          </div>
        </section>

        <section className="edit-medicine-panel">
          <div className="edit-medicine-panel-header">
            <h2>
              Medicine photo
            </h2>

            <p>
              Replace the current
              medicine image if needed.
            </p>
          </div>

          {!previewUrl ? (
            <label className="edit-medicine-upload">
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
            <div className="edit-medicine-preview">
              <img
                src={previewUrl}
                alt="Medicine preview"
              />

              <div className="edit-medicine-preview-footer">
                <div>
                  <ImageIcon
                    size={17}
                  />

                  <span>
                    {medicinePhoto?.name ||
                      "Current medicine photo"}
                  </span>
                </div>

                <button
                  type="button"
                  onClick={
                    removeNewPhoto
                  }
                  className="edit-medicine-remove"
                >
                  <X size={15} />
                  Remove preview
                </button>
              </div>
            </div>
          )}
        </section>

        {error && (
          <div className="edit-medicine-message error">
            <AlertCircle
              size={18}
            />

            <span>
              {error}
            </span>
          </div>
        )}

        {success && (
          <div className="edit-medicine-message success">
            <CheckCircle2
              size={18}
            />

            <span>
              {success}
            </span>
          </div>
        )}

        <div className="edit-medicine-actions">
          <Link
            to="/pharmacy/medicines"
            className="edit-medicine-cancel"
          >
            Cancel
          </Link>

          <button
            type="submit"
            className="edit-medicine-save"
            disabled={saving}
          >
            {saving ? (
              <>
                <RefreshCw
                  size={17}
                  className="edit-medicine-spinner"
                />
                Saving...
              </>
            ) : (
              <>
                <Save size={17} />
                Save Changes
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

export default EditMedicine;