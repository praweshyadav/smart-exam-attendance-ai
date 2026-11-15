// src/components/AttendanceCalendar.jsx
import React, { useState, useEffect } from 'react';
import {
  ChevronLeft,
  ChevronRight,
  Calendar as CalendarIcon,
  CheckCircle2,
  AlertCircle,
  Coffee,
  X,
  Info,
} from 'lucide-react';
import { getCalendar } from '../services/dashboardService';

const WEEKDAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

export default function AttendanceCalendar() {
  const today = new Date();
  const [currentYear, setCurrentYear] = useState(today.getFullYear());
  const [currentMonth, setCurrentMonth] = useState(today.getMonth() + 1); // 1-12
  const [calendarData, setCalendarData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedDay, setSelectedDay] = useState(null);

  useEffect(() => {
    let isMounted = true;
    async function loadCal() {
      setLoading(true);
      try {
        const res = await getCalendar(currentYear, currentMonth);
        if (isMounted) {
          setCalendarData(res);
          // Auto select today if in the current viewed month
          if (
            today.getFullYear() === currentYear &&
            today.getMonth() + 1 === currentMonth
          ) {
            const todayItem = res?.days?.find((d) => d.isToday);
            if (todayItem) setSelectedDay(todayItem);
          }
        }
      } catch (err) {
        // Safe fallback
      } finally {
        if (isMounted) setLoading(false);
      }
    }
    loadCal();
    return () => {
      isMounted = false;
    };
  }, [currentYear, currentMonth]);

  const handlePrevMonth = () => {
    if (currentMonth === 1) {
      setCurrentMonth(12);
      setCurrentYear((y) => y - 1);
    } else {
      setCurrentMonth((m) => m - 1);
    }
    setSelectedDay(null);
  };

  const handleNextMonth = () => {
    if (currentMonth === 12) {
      setCurrentMonth(1);
      setCurrentYear((y) => y + 1);
    } else {
      setCurrentMonth((m) => m + 1);
    }
    setSelectedDay(null);
  };

  const handleDayClick = (dayItem) => {
    setSelectedDay(dayItem);
  };

  // Calculate empty leading cells before the 1st day of the month
  const firstDayOfWeek = calendarData?.days?.[0]?.dayOfWeek ?? 0;
  const emptyLeadingDays = Array.from({ length: firstDayOfWeek });

  return (
    <div className="card calendar-card">
      <div className="calendar-card-header">
        <div className="calendar-title-box">
          <CalendarIcon size={20} className="calendar-header-icon" />
          <div>
            <h3 className="card-title">Attendance Calendar</h3>
            <p className="card-subtitle">
              {calendarData?.monthName || 'Month'} {currentYear}
            </p>
          </div>
        </div>

        <div className="calendar-nav-controls">
          <button
            className="cal-nav-btn"
            onClick={handlePrevMonth}
            aria-label="Previous month"
          >
            <ChevronLeft size={18} />
          </button>
          <span className="cal-nav-current-label">
            {calendarData?.monthName} {currentYear}
          </span>
          <button
            className="cal-nav-btn"
            onClick={handleNextMonth}
            aria-label="Next month"
          >
            <ChevronRight size={18} />
          </button>
        </div>
      </div>

      <div className="calendar-grid-wrapper">
        {/* Weekday headers */}
        <div className="calendar-weekdays-row">
          {WEEKDAYS.map((wd, idx) => (
            <div
              key={wd}
              className={`calendar-weekday-cell ${
                idx === 0 || idx === 6 ? 'weekend-header' : ''
              }`}
            >
              {wd}
            </div>
          ))}
        </div>

        {/* Days grid */}
        <div className="calendar-days-grid">
          {emptyLeadingDays.map((_, i) => (
            <div key={`empty-${i}`} className="calendar-day-cell empty" />
          ))}

          {calendarData?.days?.map((dayItem) => {
            const isSelected = selectedDay?.date === dayItem.date;
            const isWknd = dayItem.isWeekend;
            const isHol = dayItem.isHoliday;
            const hasAtt = dayItem.hasAttendance;

            let cellClass = 'calendar-day-cell';
            if (isWknd) cellClass += ' weekend-cell';
            if (isHol) cellClass += ' holiday-cell';
            if (dayItem.isToday) cellClass += ' today-cell';
            if (isSelected) cellClass += ' selected-cell';
            if (hasAtt) cellClass += ' has-attendance';

            return (
              <div
                key={dayItem.day}
                className={cellClass}
                onClick={() => handleDayClick(dayItem)}
                title={
                  isWknd
                    ? `${dayItem.weekdayName} – Weekend Holiday`
                    : isHol
                    ? `${dayItem.holidayName} (Holiday)`
                    : hasAtt
                    ? `Attendance: ${dayItem.attendancePercentage}%`
                    : 'No sessions'
                }
              >
                <span className="day-number">{dayItem.day}</span>

                {/* Badges / Dots */}
                <div className="day-indicators">
                  {hasAtt && (
                    <span className="att-indicator-dot" title="Session Recorded" />
                  )}
                  {isWknd && <span className="wknd-badge-tiny">W</span>}
                  {isHol && !isWknd && <span className="hol-badge-tiny">H</span>}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Selected Day Details Panel */}
      {selectedDay && (
        <div className="calendar-day-detail-panel">
          <div className="day-detail-header">
            <div>
              <span className="day-detail-date">
                {selectedDay.weekdayName}, {calendarData?.monthName}{' '}
                {selectedDay.day}, {currentYear}
              </span>
              <span className="day-detail-sub">
                {selectedDay.isToday ? 'Today' : selectedDay.date}
              </span>
            </div>
            <button
              className="day-detail-close"
              onClick={() => setSelectedDay(null)}
              aria-label="Close details"
            >
              <X size={16} />
            </button>
          </div>

          <div className="day-detail-body">
            {selectedDay.isWeekend ? (
              <div className="day-detail-alert weekend">
                <Coffee size={18} />
                <div>
                  <strong>{selectedDay.weekdayName} – Weekend Holiday</strong>
                  <p>Attendance is not conducted on weekends.</p>
                </div>
              </div>
            ) : selectedDay.isHoliday ? (
              <div className="day-detail-alert holiday">
                <Coffee size={18} />
                <div>
                  <strong>{selectedDay.holidayName || 'Official Holiday'}</strong>
                  <p>Attendance is blocked on configured academic holidays.</p>
                </div>
              </div>
            ) : selectedDay.hasAttendance ? (
              <div className="day-detail-stats">
                <div className="day-stat-card">
                  <span className="stat-label">Present</span>
                  <span className="stat-val text-green">
                    {selectedDay.presentCount}
                  </span>
                </div>
                <div className="day-stat-card">
                  <span className="stat-label">Eligible</span>
                  <span className="stat-val">
                    {selectedDay.totalEligible}
                  </span>
                </div>
                <div className="day-stat-card">
                  <span className="stat-label">Rate</span>
                  <span className="stat-val text-purple">
                    {selectedDay.attendancePercentage}%
                  </span>
                </div>
              </div>
            ) : (
              <div className="day-detail-empty">
                <Info size={16} />
                <span>No attendance sessions conducted on this date.</span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
