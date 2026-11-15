// src/pages/CalendarPage.jsx
import React from 'react';
import AttendanceCalendar from '../components/AttendanceCalendar';

export default function CalendarPage() {
  return (
    <div style={{ maxWidth: '1000px', margin: '0 auto' }}>
      <div style={{ marginBottom: '1.25rem' }}>
        <h1 style={{ fontSize: '1.45rem', fontWeight: 800, margin: 0, color: 'var(--text-color)' }}>
          Attendance Calendar Explorer
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.825rem', marginTop: '0.2rem' }}>
          Monthly schedule, weekend holiday markers, and historical session logs
        </p>
      </div>

      <AttendanceCalendar />
    </div>
  );
}
