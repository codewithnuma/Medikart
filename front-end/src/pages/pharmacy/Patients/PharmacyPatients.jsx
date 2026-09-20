import React, {
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  AlertCircle,
  RefreshCw,
  Search,
  UserRound,
} from "lucide-react";

import {
  getPatients,
} from "../../../services/patientApi";

import "./PharmacyPatients.css";

const PharmacyPatients = () => {
  const [patients, setPatients] =
    useState([]);

  const [search, setSearch] =
    useState("");

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");

  const loadPatients = async () => {
    try {
      setLoading(true);
      setError("");

      const response =
        await getPatients();

      const data =
        Array.isArray(response.data)
          ? response.data
          : response.data?.results || [];

      setPatients(data);
    } catch (err) {
      console.error(
        "Pharmacy patients API error:",
        err
      );

      setError(
        "Could not load patients."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPatients();
  }, []);

  const filteredPatients =
    useMemo(() => {
      const query =
        search.trim().toLowerCase();

      if (!query) {
        return patients;
      }

      return patients.filter(
        (patient) => {
          const searchableText = [
            patient.id,
            patient.username,
            patient.email,
          ]
            .filter(Boolean)
            .join(" ")
            .toLowerCase();

          return searchableText.includes(
            query
          );
        }
      );
    }, [patients, search]);

  if (loading) {
    return (
      <div className="pharmacy-patients-loading">
        <RefreshCw
          size={28}
          className="pharmacy-patients-spinner"
        />

        <span>
          Loading patients...
        </span>
      </div>
    );
  }

  return (
    <div className="pharmacy-patients-page">
      <header className="pharmacy-patients-header">
        <div>
          <span className="pharmacy-patients-kicker">
            Patient Directory
          </span>

          <h1>
            Patients
          </h1>

          <p>
            Patients who have placed
            medicine requests with your
            pharmacy.
          </p>
        </div>

        <button
          type="button"
          onClick={loadPatients}
          className="pharmacy-patients-refresh"
        >
          <RefreshCw size={16} />
          Refresh
        </button>
      </header>

      <div className="pharmacy-patients-search">
        <Search size={18} />

        <input
          type="text"
          placeholder="Search patient by name or email..."
          value={search}
          onChange={(event) =>
            setSearch(
              event.target.value
            )
          }
        />
      </div>

      {error && (
        <div className="pharmacy-patients-error">
          <AlertCircle size={18} />

          <span>
            {error}
          </span>
        </div>
      )}

      <div className="pharmacy-patients-count">
        {filteredPatients.length}{" "}
        patient
        {filteredPatients.length === 1
          ? ""
          : "s"}
      </div>

      {filteredPatients.length === 0 ? (
        <div className="pharmacy-patients-empty">
          <UserRound size={38} />

          <strong>
            No patients found
          </strong>

          <span>
            Patients who interact with
            your pharmacy will appear
            here.
          </span>
        </div>
      ) : (
        <section className="pharmacy-patients-grid">
          {filteredPatients.map(
            (patient) => (
              <article
                key={patient.id}
                className="pharmacy-patient-card"
              >
                <div className="pharmacy-patient-avatar">
                  <UserRound size={22} />
                </div>

                <div className="pharmacy-patient-card-content">
                  <span className="pharmacy-patient-id">
                    Patient #{patient.id}
                  </span>

                  <h2>
                    {patient.username ||
                      "Unnamed Patient"}
                  </h2>

                  <p>
                    {patient.email ||
                      "No email available"}
                  </p>

                  <div className="pharmacy-patient-meta">
                    <div>
                      <span>
                        Account Status
                      </span>

                      <strong>
                        {patient.is_active
                          ? "Active"
                          : "Inactive"}
                      </strong>
                    </div>

                    <div>
                      <span>
                        Joined
                      </span>

                      <strong>
                        {patient.date_joined
                          ? new Date(
                              patient.date_joined
                            ).toLocaleDateString()
                          : "Not available"}
                      </strong>
                    </div>
                  </div>
                </div>
              </article>
            )
          )}
        </section>
      )}
    </div>
  );
};

export default PharmacyPatients;