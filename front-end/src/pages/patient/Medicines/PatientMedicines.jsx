import { Link } from "react-router-dom";
import React, {
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  AlertCircle,
  Building2,
  Package,
  Pill,
  RefreshCw,
  Search,
} from "lucide-react";

import {
  getMedicines,
} from "../../../services/medicineApi";

import "./PatientMedicines.css";

const PatientMedicines = () => {
  const [medicines, setMedicines] =
    useState([]);

  const [search, setSearch] =
    useState("");

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");

  const loadMedicines = async () => {
    try {
      setLoading(true);
      setError("");

      const response =
        await getMedicines();

      const data =
        Array.isArray(response.data)
          ? response.data
          : response.data?.results || [];

      setMedicines(data);
    } catch (err) {
      console.error(
        "Medicine API error:",
        err
      );

      setError(
        "Could not load medicines from the server."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMedicines();
  }, []);

  const filteredMedicines =
    useMemo(() => {
      const query =
        search.trim().toLowerCase();

      if (!query) {
        return medicines;
      }

      return medicines.filter(
        (medicine) => {
          const searchableText = [
            medicine.medicine_name,
            medicine.company_name,
            medicine.mg,
            medicine.short_description,
            medicine.pharmacy_name,
          ]
            .filter(Boolean)
            .join(" ")
            .toLowerCase();

          return searchableText.includes(
            query
          );
        }
      );
    }, [medicines, search]);

  if (loading) {
    return (
      <div className="medicine-loading">
        <RefreshCw
          size={28}
          className="medicine-spinner"
        />

        <span>
          Loading medicines...
        </span>
      </div>
    );
  }

  return (
    <div className="patient-medicines-page">
      <header className="medicine-page-header">
        <div>
          <span className="medicine-kicker">
            Pharmacy Inventory
          </span>

          <h1>Medicines</h1>

          <p>
            Browse medicines currently
            available through registered
            pharmacies.
          </p>
        </div>

        <button
          type="button"
          onClick={loadMedicines}
          className="medicine-refresh-button"
        >
          <RefreshCw size={17} />
          Refresh
        </button>
      </header>

      <div className="medicine-search-bar">
        <Search size={18} />

        <input
          type="text"
          placeholder="Search medicine, company or dosage..."
          value={search}
          onChange={(event) =>
            setSearch(
              event.target.value
            )
          }
        />
      </div>

      {error && (
        <div className="medicine-error">
          <AlertCircle size={18} />

          <span>{error}</span>
        </div>
      )}

      <div className="medicine-result-row">
        <span>
          {filteredMedicines.length}{" "}
          medicine
          {filteredMedicines.length === 1
            ? ""
            : "s"}
        </span>
      </div>

      {filteredMedicines.length === 0 ? (
        <div className="medicine-empty">
          <Pill size={34} />

          <strong>
            No medicines found
          </strong>

          <span>
            Try a different search or
            check again later.
          </span>
        </div>
      ) : (
        <section className="medicine-grid">
          {filteredMedicines.map(
            (medicine) => (
              <article
                key={medicine.id}
                className="medicine-card"
              >
                <div className="medicine-image-wrapper">
                  {medicine.medicine_photo ? (
                    <img
                      src={
                        medicine.medicine_photo
                      }
                      alt={
                        medicine.medicine_name
                      }
                      className="medicine-image"
                    />
                  ) : (
                    <div className="medicine-image-placeholder">
                      <Pill size={34} />
                    </div>
                  )}
                </div>

                <div className="medicine-card-content">
                  <div className="medicine-card-heading">
                    <div>
                      <h2>
                        {
                          medicine.medicine_name
                        }
                      </h2>

                      <span>
                        {medicine.company_name ||
                          "Company not provided"}
                      </span>
                    </div>

                    {medicine.mg && (
                      <span className="medicine-dose">
                        {medicine.mg}
                      </span>
                    )}
                  </div>

                  {medicine.short_description && (
                    <p className="medicine-description">
                      {
                        medicine.short_description
                      }
                    </p>
                  )}

                  <div className="medicine-meta">
                    <div>
                      <Package size={16} />

                      <span>
                        {
                          medicine.available_quantity
                        }{" "}
                        available
                      </span>
                    </div>

                    <div>
                      <Building2
                        size={16}
                      />

                      <span>
                        {medicine.pharmacy_name ||
                          medicine.pharmacy?.username ||
                          "Registered pharmacy"}
                      </span>
                    </div>
                  </div>

                  <div
                    className={`medicine-stock ${
                      Number(
                        medicine.available_quantity
                      ) > 0
                        ? "in-stock"
                        : "out-of-stock"
                    }`}
                  >
                    {Number(
                      medicine.available_quantity
                    ) > 0
                      ? "In stock"
                      : "Out of stock"}
                  </div>
                  <Link
  to={`/patient/medicines/${medicine.id}`}
  className="medicine-details-button"
>
  View Details
</Link>
                </div>
              </article>
            )
          )}
        </section>
      )}
    </div>
  );
};

export default PatientMedicines;