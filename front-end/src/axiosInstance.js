import axios from "axios";

export const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ||
  "http://127.0.0.1:8000/api"
).replace(/\/$/, "");

const defaultHeaders = API_BASE_URL.includes("ngrok")
  ? {
      "ngrok-skip-browser-warning": "69420",
    }
  : {};

const axiosInstance = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
  headers: defaultHeaders,
});

let isRefreshing = false;
let refreshPromise = null;
let isLoggedOut = false;

export const markLoggedOut = () => {
  isLoggedOut = true;
};

export const resetLogoutState = () => {
  isLoggedOut = false;
};

axiosInstance.interceptors.response.use(
  (response) => response,

  async (error) => {
    const originalRequest = error.config;

    if (isLoggedOut) {
      return Promise.reject(error);
    }

    const noRefreshUrls = [
      "/accounts/login/",
      "/accounts/logout/",
      "/accounts/refresh/",
      "/accounts/register/",
    ];

    const shouldRefresh =
      error.response?.status === 401 &&
      originalRequest &&
      !originalRequest._retry &&
      !noRefreshUrls.some((url) =>
        originalRequest.url?.includes(url)
      );

    if (!shouldRefresh) {
      return Promise.reject(error);
    }

    originalRequest._retry = true;

    try {
      if (!isRefreshing) {
        isRefreshing = true;

        refreshPromise = axios
          .post(
            `${API_BASE_URL}/accounts/refresh/`,
            {},
            {
              withCredentials: true,
              headers: defaultHeaders,
            }
          )
          .finally(() => {
            isRefreshing = false;
            refreshPromise = null;
          });
      }

      await refreshPromise;

      return axiosInstance(originalRequest);
    } catch (refreshError) {
      isLoggedOut = true;

      return Promise.reject(refreshError);
    }
  }
);

export default axiosInstance;