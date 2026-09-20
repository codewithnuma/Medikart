import axiosInstance from "../axiosInstance";

export const getPatientOrders = () => {
  return axiosInstance.get("/orders/");
};

export const getPatientOrder = (id) => {
  return axiosInstance.get(
    `/orders/${id}/`
  );
};

export const createOrder = (data) => {
  return axiosInstance.post(
    "/orders/",
    data
  );
};

export const getPharmacyOrders = () => {
  return axiosInstance.get(
    "/pharmacy/orders/"
  );
};

export const getPharmacyOrder = (id) => {
  return axiosInstance.get(
    `/pharmacy/orders/${id}/`
  );
};

export const approveOrder = (id) => {
  return axiosInstance.post(
    `/pharmacy/orders/${id}/approve/`
  );
};

export const denyOrder = (
  id,
  denialReason
) => {
  return axiosInstance.post(
    `/pharmacy/orders/${id}/deny/`,
    {
      denial_reason: denialReason,
    }
  );
};

export const markOrderDelivered = (id) => {
  return axiosInstance.post(
    `/pharmacy/orders/${id}/deliver/`
  );
};