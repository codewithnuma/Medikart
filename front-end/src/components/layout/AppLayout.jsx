import React from "react";
import { Outlet } from "react-router-dom";

import Sidebar from "./Sidebar";

const AppLayout = () => {
  return (
    <div
      style={{
        minHeight: "100vh",
        background: "#f5f7fa",
      }}
    >
      <Sidebar />

      <main
        style={{
          marginLeft: "248px",
          minHeight: "100vh",
          padding: "32px",
        }}
      >
        <Outlet />
      </main>
    </div>
  );
};

export default AppLayout;