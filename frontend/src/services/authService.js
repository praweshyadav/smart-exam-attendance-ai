// src/services/authService.js
import { fetchAPI } from './api';

export const loginUser = (credentials) =>
  fetchAPI('/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(credentials),
  });

export const signupStudent = (data) =>
  fetchAPI('/auth/signup', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });

export const lookupStudent = (rollNo) =>
  fetchAPI(`/auth/student-lookup/${encodeURIComponent(rollNo)}`);

export const logoutUser = () =>
  fetchAPI('/auth/logout', { method: 'POST' });

export const getCurrentUser = () => fetchAPI('/auth/me');

export const registerAdmin = (data) =>
  fetchAPI('/auth/admin/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });

export const getAdmins = () => fetchAPI('/auth/admins');
export const getAllUsers = () => fetchAPI('/auth/users');
export const deleteUserAccount = (userId) =>
  fetchAPI(`/auth/users/${userId}`, { method: 'DELETE' });

export const updateMyPassword = (data) =>
  fetchAPI('/auth/me/password', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });

export const updateMyUsername = (data) =>
  fetchAPI('/auth/me/username', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
