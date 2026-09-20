import axiosInstance from "../axiosInstance";

export const registerAccount = (data) =>
  axiosInstance.post(
    "/accounts/register/",
    data
  );