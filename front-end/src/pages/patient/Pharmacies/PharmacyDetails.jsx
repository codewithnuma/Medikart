import React, {
  useEffect,
  useState,
} from "react";

import {
  ArrowLeft,
  Building2,
  Mail,
  MapPin,
  Phone,
  Pill,
  RefreshCw,
  UserRound,
} from "lucide-react";

import {
  Link,
  useParams,
} from "react-router-dom";

import {
  getPharmacies,
} from "../../../services/pharmacyApi";

import {
  getMedicines,
} from "../../../services/medicineApi";

import "./PharmacyDetails.css";

const PharmacyDetails = () => {
  const { id } = useParams();

  const [pharmacy, setPharmacy] =
    useState(null);

  const [medicines, setMedicines] =
    useState([]);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");

  const loadPharmacy = async () => {
    try {
      setLoading(true);
      setError("");

      const [
        pharmacyResponse,
        medicineResponse,
      ] = await Promise.all([
        getPharmacies(),
        getMedicines(),
      ]);

      const pharmacyData =
        Array.isArray(
          pharmacyResponse.data
        )
          ? pharmacyResponse.data
          : pharmacyResponse.data
              ?.results || [];

      const medicineData =
        Array.isArray(
          medicineResponse.data
        )
          ? medicineResponse.data
          : medicineResponse.data
              ?.results || [];

      const selectedPharmacy =
        pharmacyData.find(
          (item) =>
            Number(item.id) ===
            Number(id)
        );

      if (!selectedPharmacy) {
        throw new Error(
          "Pharmacy not found."
        );
      }

      setPharmacy(
        selectedPharmacy
      );

      const pharmacyMedicines =
        medicineData.filter(
          (medicine) =>
            Number(
              medicine.pharmacy
            ) === Number(id)
        );

      setMedicines(
        pharmacyMedicines
      );
    } catch (err) {
      console.error(
        "Pharmacy details error:",
        err
      );

      setError(
        "Could not load this pharmacy."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPharmacy();
  }, [id]);

  if (loading) {
    return (
      <div className="pharmacy-detail-loading">
        <RefreshCw
          size={28}
          className="pharmacy-detail-spinner"
        />

        <span>
          Loading pharmacy...
        </span>
      </div>
    );
  }

  if (error || !pharmacy) {
    return (
      <div className="pharmacy-detail-error">
        <Building2 size={36} />

        <strong>
          Pharmacy unavailable
        </strong>

        <span>
          {error}
        </span>

        <Link
          to="/patient/pharmacies"
          className="pharmacy-detail-back-link"
        >
          <ArrowLeft size={16} />
          Back to pharmacies
        </Link>
      </div>
    );
  }

  return (
    <div className="pharmacy-detail-page">
      <Link
        to="/patient/pharmacies"
        className="pharmacy-detail-back"
      >
        <ArrowLeft size={16} />
        Back to pharmacies
      </Link>

      <section className="pharmacy-profile-card">
        <div className="pharmacy-profile-image">
          {pharmacy.profile_image_url ? (
            <img
              src={
                pharmacy.profile_image_url
              }
              alt={
                pharmacy.username
              }
            />
          ) : (
            <UserRound size={45} />
          )}
        </div>

        <div className="pharmacy-profile-main">
          <span className="pharmacy-detail-kicker">
            Registered Pharmacy
          </span>

          <h1>
            {pharmacy.username}
          </h1>

          {pharmacy.bio && (
            <p className="pharmacy-detail-bio">
              {pharmacy.bio}
            </p>
          )}

          <div className="pharmacy-contact-list">
            {pharmacy.email && (
              <div>
                <Mail size={16} />

                <span>
                  {pharmacy.email}
                </span>
              </div>
            )}

            {pharmacy.phone_number && (
              <div>
                <Phone size={16} />

                <span>
                  {
                    pharmacy.phone_number
                  }
                </span>
              </div>
            )}

            {pharmacy.location && (
              <div>
                <MapPin size={16} />

                <span>
                  {pharmacy.location}
                </span>
              </div>
            )}
          </div>
        </div>
      </section>

      <section className="pharmacy-medicines-section">
        <div className="pharmacy-medicines-header">
          <div>
            <span>
              Pharmacy Inventory
            </span>

            <h2>
              Available Medicines
            </h2>

            <p>
              Medicines currently
              listed by this pharmacy.
            </p>
          </div>

          <strong>
            {medicines.length}
          </strong>
        </div>

        {medicines.length === 0 ? (
          <div className="pharmacy-medicines-empty">
            <Pill size={35} />

            <strong>
              No medicines listed
            </strong>

            <span>
              This pharmacy currently
              has no medicines visible
              in the system.
            </span>
          </div>
        ) : (
          <div className="pharmacy-medicine-grid">
            {medicines.map(
              (medicine) => (
                <article
                  key={medicine.id}
                  className="pharmacy-medicine-card"
                >
                  <div className="pharmacy-medicine-image">
                    {medicine.medicine_photo ? (
                      <img
                        src={
                          medicine.medicine_photo
                        }
                        alt={
                          medicine.medicine_name
                        }
                      />
                    ) : (
                      <Pill size={30} />
                    )}
                  </div>

                  <div className="pharmacy-medicine-content">
                    <div>
                      <h3>
                        {
                          medicine.medicine_name
                        }
                      </h3>

                      <span>
                        {medicine.mg ||
                          "Dosage not provided"}
                      </span>
                    </div>

                    <p>
                      {
                        medicine.company_name
                      }
                    </p>

                    <div className="pharmacy-medicine-stock">
                      {
                        medicine.available_quantity
                      }{" "}
                      available
                    </div>

                    <Link
                      to={`/patient/medicines/${medicine.id}`}
                      className="pharmacy-medicine-link"
                    >
                      View Medicine
                    </Link>
                  </div>
                </article>
              )
            )}
          </div>
        )}
      </section>
    </div>
  );
};

export default PharmacyDetails;