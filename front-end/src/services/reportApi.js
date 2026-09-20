import axiosInstance from "../axiosInstance";

export const getPatientReports = () => {
  return axiosInstance.get(
    "/patient/reports/"
  );
};

export const getPatientReport = (id) => {
  return axiosInstance.get(
    `/patient/reports/${id}/`
  );
};

export const createPatientReport = (data) => {
  return axiosInstance.post(
    "/patient/reports/",
    data
  );
};

export const getPharmacyReports = () => {
  return axiosInstance.get(
    "/pharmacy/reports/"
  );
};

export const getPharmacyReport = (id) =>
  axiosInstance.get(
    `/pharmacy/reports/${id}/`
  );

export const createPharmacyReport = (
  data
) => {
  return axiosInstance.post(
    "/pharmacy/reports/",
    data
  );
};

export const updatePharmacyReport = (
  id,
  data
) => {
  return axiosInstance.patch(
    `/pharmacy/reports/${id}/`,
    data
  );
};

export const deletePharmacyReport = (
  id
) => {
  return axiosInstance.delete(
    `/pharmacy/reports/${id}/`
  );
};