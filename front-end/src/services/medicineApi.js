import axiosInstance from "../axiosInstance";

export const getMedicines = () => {
  return axiosInstance.get("/medicines/");
};

export const getMyMedicines = () => {
  return axiosInstance.get("/medicines/my/");
};

export const createMedicine = (data) => {
  return axiosInstance.post(
    "/medicines/create/",
    data
  );
};

export const getMedicine = (id) => {
  return axiosInstance.get(
    `/medicines/${id}/`
  );
};

export const updateMedicine = (
  id,
  data
) => {
  return axiosInstance.patch(
    `/medicines/${id}/`,
    data
  );
};

export const deleteMedicine = (id) => {
  return axiosInstance.delete(
    `/medicines/${id}/`
  );
};