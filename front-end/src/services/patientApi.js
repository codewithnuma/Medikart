import axiosInstance from "../axiosInstance";

export const getPatients = () =>
  axiosInstance.get("/accounts/patients/");