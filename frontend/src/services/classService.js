// src/services/classService.js
import { fetchAPI } from './api';

export const getClasses = () => fetchAPI('/classes/');
export const getClassById = (id) => fetchAPI(`/classes/${id}`);
export const createClass = (data) => fetchAPI('/classes/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(data),
});
export const updateClass = (id, data) => fetchAPI(`/classes/${id}`, {
  method: 'PUT',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(data),
});
export const deleteClass = (id) => fetchAPI(`/classes/${id}`, { method: 'DELETE' });
export const getClassStudents = (id) => fetchAPI(`/classes/${id}/students`);