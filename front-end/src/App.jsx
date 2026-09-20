import React from "react";
import PatientPharmacies from "./pages/patient/Pharmacies/PatientPharmacies";
import PatientOrders from "./pages/patient/Orders/PatientOrders";
import PatientReportVault from "./pages/patient/ReportVault/PatientReportVault";
import PatientReportCapture from "./pages/patient/ReportCapture/PatientReportCapture";
import PatientProfile from "./pages/patient/Profile/PatientProfile";
import PatientVideoCalls from "./pages/patient/VideoCalls/PatientVideoCalls";
import MedicineDetails from "./pages/patient/Medicines/MedicineDetails";
import MedicineRequest from "./pages/patient/Medicines/MedicineRequest";
import PharmacyDetails from "./pages/patient/Pharmacies/PharmacyDetails";
import OrderDetails from "./pages/patient/Orders/OrderDetails";
import ReportDetails from "./pages/patient/ReportVault/ReportDetails";

import Chatbot from "./chatbot/Chatbot";

import {
  Navigate,
  Route,
  Routes,
} from "react-router-dom";

import Login from "./pages/auth/Login/Login";
import Register from "./pages/auth/Register/Register";
import ForgotPassword from "./pages/auth/ForgotPassword/ForgotPassword";

import ProtectedRoute from "./context/ProtectedRoute";
import PublicRoute from "./context/PublicRoute";

import AppLayout from "./components/layout/AppLayout";

import PatientDashboard from "./pages/patient/Dashboard/PatientDashboard";
import PatientMedicines from "./pages/patient/Medicines/PatientMedicines";
import PharmacyDashboard from "./pages/pharmacy/Dashboard/PharmacyDashboard";
import PharmacyMedicines from "./pages/pharmacy/Medicines/PharmacyMedicines";
import AddMedicine from "./pages/pharmacy/Medicines/AddMedicine";
import EditMedicine from "./pages/pharmacy/Medicines/EditMedicine";
import PharmacyOrders from "./pages/pharmacy/Orders/PharmacyOrders";
import PharmacyOrderDetails from "./pages/pharmacy/Orders/PharmacyOrderDetails";
import PharmacyReports from "./pages/pharmacy/Reports/PharmacyReports";
import AddPharmacyReport from "./pages/pharmacy/Reports/AddPharmacyReport";
import EditPharmacyReport from "./pages/pharmacy/Reports/EditPharmacyReport";
import PharmacyPatients from "./pages/pharmacy/Patients/PharmacyPatients";
import PharmacyProfile from "./pages/pharmacy/Profile/PharmacyProfile";
import PharmacyVideoCalls from "./pages/pharmacy/VideoCalls/PharmacyVideoCalls";
import VideoCallRoom from "./pages/pharmacy/VideoCalls/VideoCallRoom";

function TemporaryAdminDashboard() {
  return (
    <div style={{ padding: "40px" }}>
      <h1>Admin Dashboard</h1>
    </div>
  );
}

function TemporarySignup() {
  return (
    <div style={{ padding: "40px" }}>
      <h1>Registration</h1>

      <p>
        Registration page will be connected later.
      </p>
    </div>
  );
}

function TemporaryForgotPassword() {
  return (
    <div style={{ padding: "40px" }}>
      <h1>Forgot Password</h1>
    </div>
  );
}

function Unauthorized() {
  return (
    <div style={{ padding: "40px" }}>
      <h1>Unauthorized</h1>

      <p>
        You do not have permission to access this page.
      </p>
    </div>
  );
}

function App() {
  return (
    <Routes>
      <Route element={<Chatbot />}>
      {/* PUBLIC ROUTES */}
      <Route element={<PublicRoute />}>
        <Route
          path="/login"
          element={<Login />}
        />

        <Route
  path="/Signup"
  element={<Register />}
/>

<Route
  path="/forgot-password"
  element={<ForgotPassword />}
/>

        <Route
          path="/signup"
          element={<TemporarySignup />}
        />

        <Route
          path="/forgot-password"
          element={<TemporaryForgotPassword />}
        />
      </Route>

      {/* PATIENT ROUTES */}
      <Route
        element={
          <ProtectedRoute
            allowedRoles={["patient"]}
          />
        }
      >
        <Route element={<AppLayout />}>
          <Route
            path="/patient/dashboard"
            element={<PatientDashboard />}
          />

          <Route
            path="/patient/medicines"
            element={<PatientMedicines />}
          />

          <Route
  path="/patient/medicines/:id"
  element={<MedicineDetails />}
/>

<Route
  path="/patient/medicines/:id/request"
  element={<MedicineRequest />}
/>

          <Route
  path="/patient/pharmacies"
  element={<PatientPharmacies />}
/>

<Route
  path="/patient/pharmacies/:id"
  element={<PharmacyDetails />}
/>

<Route
  path="/patient/orders"
  element={<PatientOrders />}
/>

<Route
  path="/patient/orders/:id"
  element={<OrderDetails />}
/>

<Route
  path="/patient/report-capture"
  element={<PatientReportCapture />}
/>

<Route
  path="/patient/report-vault"
  element={<PatientReportVault />}
/>

<Route
  path="/patient/report-vault/:id"
  element={<ReportDetails />}
/>

<Route
  path="/patient/profile"
  element={<PatientProfile />}
/>

<Route
  path="/patient/video-calls"
  element={<PatientVideoCalls />}
/>
        </Route>
      </Route>

      {/* PHARMACY ROUTES */}
      <Route
        element={
          <ProtectedRoute
            allowedRoles={["pharmacy"]}
          />
        }
      >
        <Route element={<AppLayout />}>
          <Route
            path="/pharmacy/dashboard"
            element={<PharmacyDashboard />}
          />

          <Route
  path="/pharmacy/medicines"
  element={<PharmacyMedicines />}
/>

<Route
  path="/pharmacy/medicines/add"
  element={<AddMedicine />}
/>

<Route
  path="/pharmacy/medicines/:id/edit"
  element={<EditMedicine />}
/>

<Route
  path="/pharmacy/orders"
  element={<PharmacyOrders />}
/>

<Route
  path="/pharmacy/orders/:id"
  element={<PharmacyOrderDetails />}
/>

<Route
  path="/pharmacy/reports"
  element={<PharmacyReports />}
/>

<Route
  path="/pharmacy/reports/add"
  element={<AddPharmacyReport />}
/>

<Route
  path="/pharmacy/reports/:id/edit"
  element={<EditPharmacyReport />}
/>

<Route
  path="/pharmacy/patients"
  element={<PharmacyPatients />}
/>

<Route
  path="/pharmacy/profile"
  element={<PharmacyProfile />}
/>

<Route
  path="/pharmacy/video-calls"
  element={<PharmacyVideoCalls />}
/>

<Route
  path="/pharmacy/video-calls/:roomId"
  element={<VideoCallRoom />}
/>
        </Route>
      </Route>

      {/* SHARED VIDEO CALL ROUTE */}
      <Route
        element={
          <ProtectedRoute
            allowedRoles={["patient", "pharmacy"]}
          />
        }
      >
        <Route element={<AppLayout />}>
          <Route
            path="/video-call/:roomId"
            element={<VideoCallRoom />}
          />
        </Route>
      </Route>

      {/* ADMIN ROUTES */}
      <Route
        element={
          <ProtectedRoute
            allowedRoles={["admin"]}
          />
        }
      >
        <Route
          path="/admin/dashboard"
          element={<TemporaryAdminDashboard />}
        />
      </Route>

      {/* OTHER ROUTES */}
      <Route
        path="/unauthorized"
        element={<Unauthorized />}
      />

      <Route
        path="/"
        element={
          <Navigate
            to="/login"
            replace
          />
        }
      />

      <Route
        path="*"
        element={
          <Navigate
            to="/login"
            replace
          />
        }
      />
      </Route>
    </Routes>
  );
}

export default App;






