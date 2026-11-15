// src/components/TodayAttendanceCard.jsx
import React, { useState, useEffect } from 'react';
import { Coffee, CheckCircle2, UserX, Users } from 'lucide-react';
import { getTodayAttendance } from '../services/dashboardService';

export default function TodayAttendanceCard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;
    async function loadToday() {
      try {
        const res = await getTodayAttendance();
        if (isMounted) setData(res);
      } catch (err) {
        // Safe fallback
      } finally {
        if (isMounted) setLoading(false);
      }
    }
    loadToday();
    return () => {
      isMounted = false;
    };
  }, []);

  if (loading) {
    return (
      <div className="card today-card compact-today-card skeleton-card">
        <div className="stat-skeleton-title" />
        <div className="donut-skeleton compact-donut-skeleton" />
      </div>
    );
  }

  if (data?.isWeekend || data?.isHoliday) {
    return (
      <div className="card today-card compact-today-card holiday-card">
        <div className="today-header">
          <div>
            <h3 className="card-title">Today&apos;s Attendance</h3>
            <p className="card-subtitle">{data.date} • {data.dayName}</p>
          </div>
          <span className="holiday-status-tag">Holiday</span>
        </div>

        <div className="holiday-banner-body compact-holiday-body">
          <Coffee size={24} className="text-amber" />
          <h4 className="holiday-main-title" style={{ fontSize: '0.95rem', margin: '0.35rem 0' }}>
            {data.isWeekend ? `${data.dayName} – Weekend Holiday` : data.holidayReason}
          </h4>
          <p className="holiday-explanation" style={{ fontSize: '0.75rem', margin: 0 }}>
            Attendance recording is suspended on weekend holidays.
          </p>
        </div>
      </div>
    );
  }

  const present = data?.present || 0;
  const absent = data?.absent || 0;
  const total = data?.totalEligible || 0;
  const percentage = data?.attendancePercentage || 0.0;

  const size = 96;
  const strokeWidth = 9;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (percentage / 100) * circumference;

  return (
    <div className="card today-card compact-today-card">
      <div className="today-header">
        <div>
          <h3 className="card-title">Today&apos;s Attendance</h3>
          <p className="card-subtitle">Real-time status</p>
        </div>
        <span className="live-pulse-badge">
          <span className="live-dot" /> Live
        </span>
      </div>

      <div className="today-content-layout compact-content-layout">
        {/* Compact SVG Donut */}
        <div className="donut-chart-wrapper">
          <svg width={size} height={size} className="donut-svg">
            <defs>
              <linearGradient id="donutGradientCompact" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stopColor="#0066cc" />
                <stop offset="100%" stopColor="#34c759" />
              </linearGradient>
            </defs>

            <circle
              cx={size / 2}
              cy={size / 2}
              r={radius}
              fill="transparent"
              stroke="var(--donut-track, #E8E9F5)"
              strokeWidth={strokeWidth}
            />

            <circle
              cx={size / 2}
              cy={size / 2}
              r={radius}
              fill="transparent"
              stroke="url(#donutGradientCompact)"
              strokeWidth={strokeWidth}
              strokeDasharray={circumference}
              strokeDashoffset={strokeDashoffset}
              strokeLinecap="round"
              transform={`rotate(-90 ${size / 2} ${size / 2})`}
              className="donut-fill-circle"
            />
          </svg>

          <div className="donut-center-label">
            <span className="donut-percentage" style={{ fontSize: '1.15rem' }}>{percentage}%</span>
            <span className="donut-sublabel" style={{ fontSize: '0.65rem' }}>Present</span>
          </div>
        </div>

        {/* Compact Legend / Metrics */}
        <div className="today-metrics-list compact-metrics-list">
          <div className="today-metric-item present compact-metric-item">
            <CheckCircle2 size={13} className="text-green" />
            <span className="metric-title">Present</span>
            <span className="metric-count">{present}</span>
          </div>

          <div className="today-metric-item absent compact-metric-item">
            <UserX size={13} className="text-red" />
            <span className="metric-title">Absent</span>
            <span className="metric-count">{absent}</span>
          </div>

          <div className="today-metric-item total compact-metric-item">
            <Users size={13} className="text-purple" />
            <span className="metric-title">Total</span>
            <span className="metric-count">{total}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
