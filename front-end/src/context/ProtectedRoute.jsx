import React from "react";
import {
  Navigate,
  Outlet,
} from "react-router-dom";

import { useAuth } from "./AuthContext";

const ProtectedRoute = ({
  allowedRoles,
}) => {
  const {
    user,
    loading,
    isAuthenticated,
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

  if (!isAuthenticated) {
    return (
      <Navigate
        to="/login"
        replace
      />
    );
  }

  if (
    allowedRoles &&
    !allowedRoles.includes(user?.role)
  ) {
    return (
      <Navigate
        to="/unauthorized"
        replace
      />
    );
  }

  return <Outlet />;
};

export default ProtectedRoute;