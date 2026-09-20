import { Link } from "react-router-dom";
import React, {
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  AlertCircle,
  Building2,
  Mail,
  RefreshCw,
  Search,
} from "lucide-react";

import {
  getPharmacies,
} from "../../../services/pharmacyApi";

import "./PatientPharmacies.css";

const PatientPharmacies = () => {
  const [pharmacies, setPharmacies] =
    useState([]);

  const [search, setSearch] =
    useState("");

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");

  const loadPharmacies = async () => {
    try {
      setLoading(true);
      setError("");

      const response =
        await getPharmacies();

      const data =
        Array.isArray(response.data)
          ? response.data
          : response.data?.results || [];

      setPharmacies(data);
    } catch (err) {
      console.error(
        "Pharmacy API error:",
        err
      );

      setError(
        "Could not load pharmacies from the server."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPharmacies();
  }, []);

  const filteredPharmacies =
    useMemo(() => {
      const query =
        search.trim().toLowerCase();

      if (!query) {
        return pharmacies;
      }

      return pharmacies.filter(
        (pharmacy) => {
          const searchableText = [
            pharmacy.username,
            pharmacy.email,
          ]
            .filter(Boolean)
            .join(" ")
            .toLowerCase();

          return searchableText.includes(
            query
          );
        }
      );
    }, [pharmacies, search]);

  if (loading) {
    return (
      <div className="pharmacy-loading">
        <RefreshCw
          size={28}
          className="pharmacy-spinner"
        />

        <span>
          Loading pharmacies...
        </span>
      </div>
    );
  }

  return (
    <div className="patient-pharmacies-page">
      <header className="pharmacy-page-header">
        <div>
          <span className="pharmacy-kicker">
            Registered Providers
          </span>

          <h1>Pharmacies</h1>

          <p>
            Browse pharmacies registered
            with NirogNepal.
          </p>
        </div>

        <button
          type="button"
          onClick={loadPharmacies}
          className="pharmacy-refresh-button"
        >
          <RefreshCw size={17} />
          Refresh
        </button>
      </header>

      <div className="pharmacy-search-bar">
        <Search size={18} />

        <input
          type="text"
          placeholder="Search pharmacy name or email..."
          value={search}
          onChange={(event) =>
            setSearch(
              event.target.value
            )
          }
        />
      </div>

      {error && (
        <div className="pharmacy-error">
          <AlertCircle size={18} />

          <span>
            {error}
          </span>
        </div>
      )}

      <div className="pharmacy-result-row">
        <span>
          {filteredPharmacies.length}{" "}
          pharmacy
          {filteredPharmacies.length === 1
            ? ""
            : "ies"}
        </span>
      </div>

      {filteredPharmacies.length === 0 ? (
        <div className="pharmacy-empty">
          <Building2 size={36} />

          <strong>
            No pharmacies found
          </strong>

          <span>
            Registered pharmacies will
            appear here.
          </span>
        </div>
      ) : (
        <section className="pharmacy-grid">
          {filteredPharmacies.map(
            (pharmacy) => (
              <article
                key={pharmacy.id}
                className="pharmacy-card"
              >
                <div className="pharmacy-card-icon">
                  <Building2 size={26} />
                </div>

                <div className="pharmacy-card-content">
                  <h2>
                    {pharmacy.username ||
                      "Registered Pharmacy"}
                  </h2>

                  {pharmacy.email && (
                    <div className="pharmacy-info-row">
                      <Mail size={15} />

                      <span>
                        {pharmacy.email}
                      </span>
                    </div>
                  )}

                  <div className="pharmacy-status">
                    Registered pharmacy
                  </div>
                  <Link
  to={`/patient/pharmacies/${pharmacy.id}`}
  className="pharmacy-view-button"
>
  View Pharmacy
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

export default PatientPharmacies;