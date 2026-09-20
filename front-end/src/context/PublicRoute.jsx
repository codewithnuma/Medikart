import React from "react";
import {
  Navigate,
  Outlet,
} from "react-router-dom";

import { useAuth } from "./AuthContext";

const PublicRoute = () => {
  const {
    user,
    loading,
  } = useAuth();

  if (loading) {
    return (
      <div
        style={{
          minHeight: "100vh",
          display: "grid",
          placeItems: "center",
          fontFamily: "sans-serif",
        }}
      >
        Loading...
      </div>
    );
  }

  if (user?.role === "patient") {
    return (
      <Navigate
        to="/patient/dashboard"
        replace
      />
    );
  }

  if (user?.role === "pharmacy") {
    return (
      <Navigate
        to="/pharmacy/dashboard"
        replace
      />
    );
  }

  if (user?.role === "admin") {
    return (
      <Navigate
        to="/admin/dashboard"
        replace
      />
    );
  }

  return <Outlet />;
};

export default PublicRoute;