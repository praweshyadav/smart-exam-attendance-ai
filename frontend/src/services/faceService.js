// src/services/faceService.js
import { fetchAPI } from './api';

export const startRegistrationLiveness = () =>
  fetchAPI('/face-registration/liveness/start', { method: 'POST' });

export const checkRegistrationLivenessFrame = (registrationSessionId, imageBlob) => {
  const formData = new FormData();
  formData.append('image', imageBlob, 'liveness.jpg');
  return fetchAPI(
    `/face-registration/liveness/frame?registration_session_id=${encodeURIComponent(registrationSessionId)}`,
    {
      method: 'POST',
      body: formData,
    }
  );
};

export const closeRegistrationLiveness = (registrationSessionId) =>
  fetchAPI(
    `/face-registration/liveness/close?registration_session_id=${encodeURIComponent(registrationSessionId)}`,
    { method: 'POST' }
  );

export const registerFace = (studentId, imageBlob, allowUpdate = true, registrationSessionId = null) => {
  const formData = new FormData();
  formData.append('student_id', studentId);
  formData.append('allow_update', allowUpdate ? 'true' : 'false');
  if (registrationSessionId) {
    formData.append('registration_session_id', registrationSessionId);
  }
  formData.append('image', imageBlob, 'face.jpg');
  return fetchAPI('/face-registration/', {
    method: 'POST',
    body: formData,
  });
};

export const analyzeRegistrationFrame = (imageBlob) => {
  const formData = new FormData();
  formData.append('image', imageBlob, 'frame.jpg');
  return fetchAPI('/face-registration/analyze-frame', {
    method: 'POST',
    body: formData,
  });
};
