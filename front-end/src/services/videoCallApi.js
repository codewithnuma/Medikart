import axiosInstance from "../axiosInstance";

export const getVideoCallByRoomId = (roomId) => {
  return axiosInstance.get(
    `/video-calls/join/${roomId}/`
  );
};

export const endPharmacyVideoCall = (roomId) => {
  return axiosInstance.post(
    `/video-calls/pharmacy/${roomId}/end/`
  );
};
