// src/services/dashboardService.js
import { fetchAPI } from './api';

export const getDashboardSummary = () => fetchAPI('/dashboard/summary');

export const getAttendanceTrend = (days = 7) =>
  fetchAPI(`/dashboard/attendance-trend?days=${days}`);

export const getTodayAttendance = () => fetchAPI('/dashboard/today-attendance');

export const getCalendar = (year, month) => {
  const params = [];
  if (year) params.push(`year=${year}`);
  if (month) params.push(`month=${month}`);
  const qs = params.length ? `?${params.join('&')}` : '';
  return fetchAPI(`/dashboard/calendar${qs}`);
};

export const getRecentActivities = (limit = 10, page = 1) =>
  fetchAPI(`/dashboard/recent-activity?limit=${limit}&page=${page}`);

export const getNotifications = (limit = 20) =>
  fetchAPI(`/dashboard/notifications?limit=${limit}`);

export const markNotificationRead = (id) =>
  fetchAPI(`/dashboard/notifications/${id}/read`, { method: 'PUT' });

export const markAllNotificationsRead = () =>
  fetchAPI('/dashboard/notifications/mark-all-read', { method: 'PUT' });

export const searchRecords = (query) =>
  fetchAPI(`/dashboard/search?q=${encodeURIComponent(query)}`);

export const getAdminProfile = () => fetchAPI('/dashboard/admin-profile');
