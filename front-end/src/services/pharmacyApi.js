import axiosInstance from "../axiosInstance";

export const getPharmacies = () => {
  return axiosInstance.get("/pharmacies/");
};
export const getPharmacyVideoCalls = () => {
  return axiosInstance.get("/video-calls/pharmacy/");
};

export const createPharmacyVideoCall = (data) => {
  return axiosInstance.post(
    "/video-calls/pharmacy/",
    data
  );
};
