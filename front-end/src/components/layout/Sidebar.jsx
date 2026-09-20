import React from "react";
import {
  FileText,
  HeartPulse,
  LayoutDashboard,
  LogOut,
  MapPin,
  PackageSearch,
  Pill,
  ScanLine,
  UserRound,
  UsersRound,
  Video,
} from "lucide-react";
import {
  NavLink,
  useNavigate,
} from "react-router-dom";

import { useAuth } from "../../context/AuthContext";
import styles from "./Sidebar.module.css";

const patientNavigation = [
  {
    label: "Dashboard",
    path: "/patient/dashboard",
    icon: LayoutDashboard,
  },
  {
    label: "Medicines",
    path: "/patient/medicines",
    icon: Pill,
  },
  {
    label: "Pharmacies",
    path: "/patient/pharmacies",
    icon: MapPin,
  },
  {
    label: "Orders",
    path: "/patient/orders",
    icon: PackageSearch,
  },
  {
    label: "Report Capture",
    path: "/patient/report-capture",
    icon: ScanLine,
  },
  {
    label: "Report Vault",
    path: "/patient/report-vault",
    icon: FileText,
  },
  
  {
    label: "Video Consultations",
    path: "/patient/video-calls",
    icon: Video,
  },
  {
    label: "Profile",
    path: "/patient/profile",
    icon: UserRound,
  },
];

const pharmacyNavigation = [
  {
    label: "Dashboard",
    path: "/pharmacy/dashboard",
    icon: LayoutDashboard,
  },
  {
    label: "Medicines",
    path: "/pharmacy/medicines",
    icon: Pill,
  },
  {
    label: "Orders",
    path: "/pharmacy/orders",
    icon: PackageSearch,
  },
  {
    label: "Patient Reports",
    path: "/pharmacy/reports",
    icon: FileText,
  },
  {
    label: "Patients",
    path: "/pharmacy/patients",
    icon: UsersRound,
  },
  {
    label: "Video Consultations",
    path: "/pharmacy/video-calls",
    icon: Video,
  },
  {
    label: "Profile",
    path: "/pharmacy/profile",
    icon: UserRound,
  },
];

const Sidebar = () => {
  const {
    user,
    logout,
  } = useAuth();

  const navigate = useNavigate();

  const role = String(
    user?.role || ""
  ).toLowerCase();

  const navigation =
    role === "pharmacy"
      ? pharmacyNavigation
      : patientNavigation;

  const displayName =
    user?.username ||
    user?.email ||
    "NirogNepal User";

  const initial = displayName
    .charAt(0)
    .toUpperCase();

  const handleLogout = async () => {
    await logout();

    navigate(
      "/login",
      {
        replace: true,
      }
    );
  };

  return (
    <aside className={styles.sidebar}>
      <div>
        <div className={styles.brand}>
          <div className={styles.logo}>
            <HeartPulse size={22} />
          </div>

          <div className={styles.brandText}>
            Nirog
            <span>Nepal</span>
          </div>
        </div>

        <div className={styles.roleBadge}>
          {role === "pharmacy"
            ? "Pharmacy Portal"
            : "Patient Portal"}
        </div>
      </div>

      <nav className={styles.navigation}>
        {navigation.map(
          ({
            label,
            path,
            icon: Icon,
          }) => (
            <NavLink
              key={path}
              to={path}
              className={({
                isActive,
              }) =>
                `${styles.navItem} ${
                  isActive
                    ? styles.active
                    : ""
                }`
              }
            >
              <Icon
                size={19}
                strokeWidth={1.9}
              />

              <span>
                {label}
              </span>
            </NavLink>
          )
        )}
      </nav>

      <div className={styles.footer}>
        <div className={styles.userCard}>
          <div className={styles.avatar}>
            {initial}
          </div>

          <div className={styles.userDetails}>
            <strong>
              {displayName}
            </strong>

            <span>
              {role || "account"}
            </span>
          </div>
        </div>

        <button
          type="button"
          onClick={handleLogout}
          className={styles.logoutButton}
        >
          <LogOut size={18} />

          <span>
            Sign out
          </span>
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;


