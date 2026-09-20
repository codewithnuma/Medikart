import { Link } from "react-router-dom";
import React, {
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  AlertCircle,
  PackagePlus,
  Pill,
  RefreshCw,
  Search,
  Trash2,
} from "lucide-react";

import {
  deleteMedicine,
  getMyMedicines,
} from "../../../services/medicineApi";

import "./PharmacyMedicines.css";

const PharmacyMedicines = () => {
  const [medicines, setMedicines] =
    useState([]);

  const [search, setSearch] =
    useState("");

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");
    const [
  deletingMedicineId,
  setDeletingMedicineId,
] = useState(null);

  const loadMedicines = async () => {
    try {
      setLoading(true);
      setError("");

      const response =
        await getMyMedicines();

      const data =
        Array.isArray(response.data)
          ? response.data
          : response.data?.results || [];

      setMedicines(data);
    } catch (err) {
      console.error(
        "Pharmacy medicines API error:",
        err
      );

      setError(
        "Could not load your medicines."
      );
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteMedicine = async (
  medicine
) => {
  const confirmed = window.confirm(
    `Delete "${medicine.medicine_name}" from your inventory?`
  );

  if (!confirmed) {
    return;
  }

  try {
    setDeletingMedicineId(
      medicine.id
    );

    setError("");

    await deleteMedicine(
      medicine.id
    );

    setMedicines(
      (currentMedicines) =>
        currentMedicines.filter(
          (item) =>
            item.id !==
            medicine.id
        )
    );
  } catch (err) {
    console.error(
      "Delete medicine error:",
      err
    );

    setError(
      "Could not delete this medicine."
    );
  } finally {
    setDeletingMedicineId(
      null
    );
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
      <div className="pharmacy-medicines-loading">
        <RefreshCw
          size={28}
          className="pharmacy-medicines-spinner"
        />

        <span>
          Loading your medicines...
        </span>
      </div>
    );
  }

  return (
    <div className="pharmacy-medicines-page">
      <header className="pharmacy-medicines-header">
        <div>
          <span className="pharmacy-medicines-kicker">
            Inventory
          </span>

          <h1>
            My Medicines
          </h1>

          <p>
            Manage medicines listed by
            your pharmacy.
          </p>
        </div>

        <Link
  to="/pharmacy/medicines/add"
  className="pharmacy-add-medicine-button"
>
  <PackagePlus size={17} />
  Add Medicine
</Link>
      </header>

      <div className="pharmacy-medicines-toolbar">
        <div className="pharmacy-medicine-search">
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

        <button
          type="button"
          onClick={loadMedicines}
          className="pharmacy-medicines-refresh"
        >
          <RefreshCw size={17} />
          Refresh
        </button>
      </div>

      {error && (
        <div className="pharmacy-medicines-error">
          <AlertCircle size={18} />
          <span>{error}</span>
        </div>
      )}

      <div className="pharmacy-medicines-count">
        {filteredMedicines.length}{" "}
        medicine
        {filteredMedicines.length === 1
          ? ""
          : "s"}
      </div>

      {filteredMedicines.length === 0 ? (
        <div className="pharmacy-medicines-empty">
          <Pill size={38} />

          <strong>
            No medicines found
          </strong>

          <span>
            Medicines added by your
            pharmacy will appear here.
          </span>
        </div>
      ) : (
        <section className="pharmacy-medicines-grid">
          {filteredMedicines.map(
            (medicine) => (
              <article
                key={medicine.id}
                className="pharmacy-medicine-card"
              >
                <div className="pharmacy-medicine-photo">
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
                    <Pill size={34} />
                  )}
                </div>

                <div className="pharmacy-medicine-card-content">
                  <span className="pharmacy-medicine-label">
                    Medicine
                  </span>

                  <h2>
                    {
                      medicine.medicine_name
                    }
                  </h2>

                  <p>
                    {medicine.company_name ||
                      "Company not provided"}
                  </p>

                  <div className="pharmacy-medicine-meta">
                    <div>
                      <span>
                        Dosage
                      </span>

                      <strong>
                        {medicine.mg ||
                          "Not provided"}
                      </strong>
                    </div>

                    <div>
                      <span>
                        Stock
                      </span>

                      <strong>
                        {
                          medicine.available_quantity
                        }
                      </strong>
                    </div>
                  </div>

                  <div
                    className={`pharmacy-stock-status ${
                      Number(
                        medicine.available_quantity
                      ) <= 5
                        ? "low"
                        : "good"
                    }`}
                  >
                    {Number(
                      medicine.available_quantity
                    ) <= 5
                      ? "Low stock"
                      : "In stock"}
                  </div>
                  <div className="pharmacy-medicine-actions">
  <Link
    to={`/pharmacy/medicines/${medicine.id}/edit`}
    className="pharmacy-edit-medicine-button"
  >
    Edit Medicine
  </Link>

  <button
    type="button"
    className="pharmacy-delete-medicine-button"
    onClick={() =>
      handleDeleteMedicine(medicine)
    }
    disabled={
      deletingMedicineId === medicine.id
    }
  >
    <Trash2 size={15} />

    {deletingMedicineId === medicine.id
      ? "Deleting..."
      : "Delete"}
  </button>
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

export default PharmacyMedicines;