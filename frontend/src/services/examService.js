// src/services/examService.js
import { fetchAPI } from './api';

export const getExams = () => fetchAPI('/exams/');
export const getExamById = (id) => fetchAPI(`/exams/${id}`);
export const getExamsByClass = (classId) => fetchAPI(`/exams/class/${classId}`);
export const createExam = (data) => fetchAPI('/exams/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(data),
});
export const updateExam = (id, data) => fetchAPI(`/exams/${id}`, {
  method: 'PUT',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(data),
});
export const deleteExam = (id) => fetchAPI(`/exams/${id}`, { method: 'DELETE' });