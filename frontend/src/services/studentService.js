// src/services/studentService.js
import { fetchAPI } from './api';

export const getStudents = () => fetchAPI('/students/');
export const getStudentById = (studentId) => fetchAPI(`/students/${studentId}`);
export const createStudent = (data) => fetchAPI('/students/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(data),
});
export const updateStudent = (studentId, data) => fetchAPI(`/students/${studentId}`, {
  method: 'PUT',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(data),
});
export const deleteStudent = (studentId) => fetchAPI(`/students/${studentId}`, { method: 'DELETE' });