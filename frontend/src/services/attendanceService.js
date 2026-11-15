// src/services/attendanceService.js
import { fetchAPI } from './api';

// Attendance Sessions
export const createSession = (examId) =>
  fetchAPI(examId ? `/sessions/?exam_id=${examId}` : '/sessions/', { method: 'POST' });
export const getSessions = () => fetchAPI('/sessions/');
export const getSessionById = (id) => fetchAPI(`/sessions/${id}`);
export const getSessionsByExam = (examId) => fetchAPI(`/sessions/exam/${examId}`);
export const endSession = (sessionId) => fetchAPI(`/sessions/${sessionId}/end`, { method: 'PUT' });

// Stateful Challenge-Response Verification Operations
export const verifyAttendance = (formData) =>
  fetchAPI('/attendance/verify', {
    method: 'POST',
    body: formData,
  });

export const startVerificationSession = (sessionId) =>
  fetchAPI(`/attendance/verify/start?session_id=${encodeURIComponent(sessionId)}`, {
    method: 'POST',
  });

export const processVerificationFrame = (verificationSessionId, formData) =>
  fetchAPI(
    `/attendance/verify/frame?verification_session_id=${encodeURIComponent(verificationSessionId)}`,
    { method: 'POST', body: formData }
  );

export const completeVerification = (verificationSessionId, formData) =>
  fetchAPI(
    `/attendance/verify/complete?verification_session_id=${encodeURIComponent(verificationSessionId)}`,
    { method: 'POST', body: formData }
  );

export const resetVerificationSession = (verificationSessionId) =>
  fetchAPI(
    `/attendance/verify/reset?verification_session_id=${encodeURIComponent(verificationSessionId)}`,
    { method: 'POST' }
  );

export const closeVerificationSessionById = (verificationSessionId) =>
  fetchAPI(
    `/attendance/verify/close-session?verification_session_id=${encodeURIComponent(verificationSessionId)}`,
    { method: 'POST' }
  );

export const closeVerificationSession = () =>
  fetchAPI('/attendance/verify/close', { method: 'POST' });

export const getAttendance = () => fetchAPI('/attendance/');
export const getMyAttendance = () => fetchAPI('/attendance/my');
export const getAttendanceByDate = (date) => fetchAPI(`/attendance/date/${date}`);
export const getAttendanceByStudent = (studentId) => fetchAPI(`/attendance/student/${encodeURIComponent(studentId)}`);
export const getAttendanceBySession = (sessionId) => fetchAPI(`/attendance/session/${sessionId}`);

// Verification Attempts
export const getVerificationLogs = () => fetchAPI('/verification-attempts/');
export const getVerificationLogById = (attemptId) => fetchAPI(`/verification-attempts/${attemptId}`);
export const getVerificationLogsByStudent = (studentId) =>
  fetchAPI(`/verification-attempts/student/${encodeURIComponent(studentId)}`);
export const getVerificationLogsByResult = (result) =>
  fetchAPI(`/verification-attempts/result/${encodeURIComponent(result)}`);
