// src/components/DashboardHeader.jsx
import React, { useState, useEffect } from 'react';
import { Calendar as CalendarIcon } from 'lucide-react';

function getGreeting(hour) {
  if (hour >= 4 && hour < 12) return 'Good Morning';
  if (hour >= 12 && hour < 17) return 'Good Afternoon';
  return 'Good Evening';
}

function formatDate(date) {
  const options = {
    weekday: 'short',
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  };
  return date.toLocaleDateString('en-US', options);
}

export default function DashboardHeader({ adminName = 'Admin' }) {
  const [currentDate, setCurrentDate] = useState(() => new Date());

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentDate(new Date());
    }, 60000);
    return () => clearInterval(timer);
  }, []);

  const greeting = getGreeting(currentDate.getHours());
  const dateFormatted = formatDate(currentDate);

  return (
    <div className="dashboard-header-container">
      <div className="dashboard-header-left">
        <h2 className="dashboard-greeting-title">
          {greeting}, {adminName} <span className="greeting-wave">👋</span>
        </h2>
        <p className="dashboard-greeting-subtitle">
          Here&apos;s your real-time academic attendance overview
        </p>
      </div>

      <div className="dashboard-header-right">
        <div className="date-badge">
          <CalendarIcon size={14} className="date-badge-icon" />
          <span className="date-badge-text">{dateFormatted}</span>
        </div>
      </div>
    </div>
  );
}
