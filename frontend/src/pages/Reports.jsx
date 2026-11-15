// src/pages/Reports.jsx
import React, { useState, useEffect } from 'react';
import {
  Calendar,
  Download,
  FileCheck,
  CheckCircle2,
  FileText,
  Clock,
  UserCheck,
} from 'lucide-react';
import { getAttendanceByDate } from '../services/attendanceService';
import { downloadAuthenticatedFile } from '../services/api';

export default function Reports() {
  const [selectedDate, setSelectedDate] = useState(() => {
    return new Date().toISOString().split('T')[0];
  });
  const [attendanceRecords, setAttendanceRecords] = useState([]);
  const [loading, setLoading] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [statusMessage, setStatusMessage] = useState('');

  // Fetch preview attendance records for the selected date
  useEffect(() => {
    let isMounted = true;
    async function loadAttendancePreview() {
      if (!selectedDate) return;
      setLoading(true);
      try {
        const res = await getAttendanceByDate(selectedDate);
        const list = Array.isArray(res) ? res : res?.attendance || [];
        if (isMounted) setAttendanceRecords(list);
      } catch (err) {
        if (isMounted) setAttendanceRecords([]);
      } finally {
        if (isMounted) setLoading(false);
      }
    }
    loadAttendancePreview();
    return () => {
      isMounted = false;
    };
  }, [selectedDate]);

  const triggerDownload = async (format) => {
    if (!selectedDate) {
      setStatusMessage('Please select a valid date.');
      return;
    }
    setDownloading(true);
    setStatusMessage('');
    const ext = format === 'excel' ? 'xlsx' : format;
    try {
      await downloadAuthenticatedFile(
        `/exports/daily/${selectedDate}/${format}`,
        `daily_attendance_${selectedDate}.${ext}`
      );
      setStatusMessage(`Attendance report (${format.toUpperCase()}) downloaded.`);
    } catch (err) {
      setStatusMessage(err.message || 'Download failed.');
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div className="reports-page-container">
      <div className="page-header">
        <div>
          <h1 className="page-title">Attendance Report</h1>
          <p className="page-subtitle">
            Generate and export official daily attendance reports in CSV, Excel, or PDF formats
          </p>
        </div>
      </div>

      {statusMessage && (
        <div className="status-banner">
          <CheckCircle2 size={16} className="text-emerald-500" />
          <span>{statusMessage}</span>
        </div>
      )}

      {/* Configuration & Export Card */}
      <div className="card report-config-card" style={{ marginBottom: '1.5rem' }}>
        <div className="report-config-header">
          <FileCheck size={26} className="text-purple" />
          <div>
            <h3 className="card-title">Daily Attendance Report</h3>
            <p className="card-subtitle">
              Select date to preview records and download official reports
            </p>
          </div>
        </div>

        <div className="report-config-body">
          <div className="form-group" style={{ maxWidth: '320px' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontWeight: 600 }}>
              <Calendar size={15} className="text-purple" /> Attendance Date
            </label>
            <input
              type="date"
              className="input-field"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              style={{ marginTop: '0.35rem' }}
            />
          </div>

          <div className="export-actions-row">
            <span className="export-label">Download Report:</span>
            <div className="export-btn-group">
              <button
                className="btn-export csv"
                onClick={() => triggerDownload('csv')}
                disabled={downloading}
              >
                <Download size={14} /> CSV Format
              </button>
              <button
                className="btn-export excel"
                onClick={() => triggerDownload('excel')}
                disabled={downloading}
              >
                <Download size={14} /> Excel (.xlsx)
              </button>
              <button
                className="btn-export pdf"
                onClick={() => triggerDownload('pdf')}
                disabled={downloading}
              >
                <Download size={14} /> PDF Document
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Attendance Records Preview Table */}
      <div className="card" style={{ padding: '1.25rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <div>
            <h3 style={{ fontSize: '1.05rem', fontWeight: 700, margin: 0 }}>
              Attendance Records Preview ({selectedDate})
            </h3>
            <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
              {attendanceRecords.length} student(s) marked present
            </span>
          </div>
        </div>

        {loading ? (
          <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
            Loading records for {selectedDate}...
          </div>
        ) : attendanceRecords.length === 0 ? (
          <div style={{ padding: '2.5rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
            <FileText size={32} style={{ opacity: 0.4, marginBottom: '0.5rem' }} />
            <p>No attendance records found for {selectedDate}.</p>
          </div>
        ) : (
          <div className="responsive-table-wrapper" style={{ overflowX: 'auto', WebkitOverflowScrolling: 'touch', width: '100%' }}>
            <table style={{ minWidth: '550px', borderCollapse: 'collapse', margin: 0 }}>
              <thead>
                <tr style={{ backgroundColor: 'var(--hover-bg)' }}>
                  <th style={{ width: '40px' }}>#</th>
                  <th>Roll / Student ID</th>
                  <th>Student Name</th>
                  <th>Time</th>
                  <th>Status</th>
                  <th>Match Score</th>
                </tr>
              </thead>
              <tbody>
                {attendanceRecords.map((rec, idx) => (
                  <tr key={rec.id || idx}>
                    <td>{idx + 1}</td>
                    <td><strong>{rec.student_id}</strong></td>
                    <td>{rec.student_name}</td>
                    <td>{rec.attendance_time}</td>
                    <td>
                      <span className="text-green font-semibold">
                        {rec.status || 'Present'}
                      </span>
                    </td>
                    <td>
                      {rec.verification_score
                        ? `${(rec.verification_score * 100).toFixed(1)}%`
                        : 'Verified'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
