import axiosInstance from "../axiosInstance";

export const getCurrentUser = () => {
  return axiosInstance.get(
    "/accounts/me/"
  );
};

export const getProfile = () => {
  return axiosInstance.get(
    "/accounts/profile/"
  );
};

export const updateProfile = (data) => {
  return axiosInstance.patch(
    "/accounts/profile/",
    data
  );
};