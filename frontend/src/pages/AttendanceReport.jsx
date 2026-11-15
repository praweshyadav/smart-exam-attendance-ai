// src/pages/AttendanceReport.jsx
import React, { useEffect, useState } from 'react';
import {
  FileSpreadsheet,
  Printer,
  Download,
  Filter,
} from 'lucide-react';
import Loading from '../components/Loading';
import ErrorMessage from '../components/ErrorMessage';
import { getClasses } from '../services/classService';
import { getStudents } from '../services/studentService';
import { getAttendance } from '../services/attendanceService';

export default function AttendanceReport() {
  const [classes, setClasses] = useState([]);
  const [allStudents, setAllStudents] = useState([]);
  const [allAttendance, setAllAttendance] = useState([]);

  const [selectedBranch, setSelectedBranch] = useState('CSE');
  const [selectedSemester, setSelectedSemester] = useState('7');
  const [selectedSection, setSelectedSection] = useState('');

  const [uniqueDates, setUniqueDates] = useState([]);
  const [registerRows, setRegisterRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searched, setSearched] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    async function initData() {
      try {
        const [clsRes, stRes, attRes] = await Promise.all([
          getClasses(),
          getStudents(),
          getAttendance().catch(() => []),
        ]);
        const classList = Array.isArray(clsRes) ? clsRes : clsRes?.classes || [];
        const studentList = Array.isArray(stRes) ? stRes : stRes?.students || [];
        const attList = Array.isArray(attRes) ? attRes : attRes?.attendance || [];

        setClasses(classList);
        setAllStudents(studentList);
        setAllAttendance(attList);

        // Pre-select first matching section
        const defaultSec = classList.find(
          (c) =>
            String(c.department || '').toUpperCase() === 'CSE' &&
            String(c.semester) === '7'
        );
        if (defaultSec) {
          setSelectedSection(String(defaultSec.class_id || defaultSec.id));
        } else if (classList.length > 0) {
          setSelectedSection(String(classList[0].class_id || classList[0].id));
        }
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    initData();
  }, []);

  // Filter available sections
  const availableSections = classes.filter(
    (c) =>
      String(c.department || '').trim().toUpperCase() === String(selectedBranch).trim().toUpperCase() &&
      String(c.semester) === String(selectedSemester)
  );

  const getSectionName = () => {
    const sec = classes.find((c) => String(c.class_id || c.id) === String(selectedSection));
    return sec ? sec.class_name : 'Selected Section';
  };

  const handleGenerateReport = () => {
    if (!selectedSection) {
      setError('Please select a valid section.');
      return;
    }
    setError('');

    // 1. Filter students in this class/section
    const secStudents = allStudents.filter(
      (s) => String(s.class_id) === String(selectedSection)
    );

    const studentIds = new Set(secStudents.map((s) => String(s.student_id)));

    // 2. Filter attendance records for these students
    const classAttendance = allAttendance.filter((a) =>
      studentIds.has(String(a.student_id))
    );

    // 3. Find unique attendance dates (newest first)
    const datesSet = new Set();
    classAttendance.forEach((a) => {
      if (a.attendance_date) datesSet.add(a.attendance_date);
    });
    const sortedDates = Array.from(datesSet).sort((a, b) => (a < b ? 1 : -1));

    // 4. Build student report rows
    const rows = secStudents.map((st) => {
      const studentRecords = classAttendance.filter(
        (a) => String(a.student_id) === String(st.student_id) && a.status === 'Present'
      );
      const presentDates = new Set(studentRecords.map((r) => r.attendance_date));

      return {
        student_id: st.student_id,
        student_name: st.student_name,
        presentDates,
        totalPresent: presentDates.size,
      };
    });

    // Sort by roll number or student name
    rows.sort((a, b) => a.student_id.localeCompare(b.student_id));

    setUniqueDates(sortedDates);
    setRegisterRows(rows);
    setSearched(true);
  };

  // Auto generate on initial load if default section is found
  useEffect(() => {
    if (!searched && selectedSection && allStudents.length > 0) {
      handleGenerateReport();
    }
  }, [selectedSection, allStudents]);

  const handlePrint = () => {
    window.print();
  };

  const handleExportCSV = () => {
    if (registerRows.length === 0) return;
    const dateHeaders = uniqueDates.map((d) => `"${d}"`).join(',');
    const csvHeader = `"Roll No","Student Name",${dateHeaders},"Total Present","Total Sessions"\n`;

    const csvRows = registerRows
      .map((r) => {
        const dateValues = uniqueDates
          .map((d) => (r.presentDates.has(d) ? '"P"' : '"A"'))
          .join(',');
        return `"${r.student_id}","${r.student_name}",${dateValues},"${r.totalPresent}","${uniqueDates.length}"`;
      })
      .join('\n');

    const blob = new Blob([csvHeader + csvRows], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `${getSectionName()}_Attendance_Report.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  if (loading) return <Loading />;

  return (
    <div className="attendance-report-page-container" style={{ maxWidth: '1200px', margin: '0 auto', width: '100%' }}>
      {/* Controls Bar (Hidden during Print) */}
      <div className="no-print" style={{ marginBottom: '1.25rem' }}>
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '1rem',
            flexWrap: 'wrap',
            gap: '0.75rem',
          }}
        >
          <div>
            <h1 style={{ fontSize: '1.4rem', fontWeight: 800, margin: 0, color: 'var(--text-color)' }}>
              Attendance Report
            </h1>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.825rem', marginTop: '0.2rem' }}>
              Academic attendance report & verified student attendance register
            </p>
          </div>

          <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
            <button
              className="btn btn-secondary"
              onClick={handleExportCSV}
              disabled={registerRows.length === 0}
              style={{ fontSize: '0.8rem', padding: '0.45rem 0.85rem' }}
            >
              <Download size={14} /> Export CSV
            </button>
            <button
              className="btn"
              onClick={handlePrint}
              disabled={registerRows.length === 0}
              style={{ fontSize: '0.8rem', padding: '0.45rem 0.85rem' }}
            >
              <Printer size={14} /> Print / Save PDF
            </button>
          </div>
        </div>

        {/* Filter Card */}
        <div
          className="card"
          style={{
            padding: '0.85rem 1.15rem',
            display: 'flex',
            gap: '0.85rem',
            alignItems: 'flex-end',
            flexWrap: 'wrap',
          }}
        >
          <div style={{ flex: '1', minWidth: '120px' }}>
            <label style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-secondary)' }}>Branch</label>
            <select
              value={selectedBranch}
              onChange={(e) => {
                setSelectedBranch(e.target.value);
                setSelectedSection('');
              }}
              style={{ margin: '0.25rem 0 0', padding: '0.45rem 0.65rem', fontSize: '0.85rem' }}
            >
              <option value="CSE">CSE</option>
              <option value="IT">IT</option>
            </select>
          </div>

          <div style={{ flex: '1', minWidth: '120px' }}>
            <label style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-secondary)' }}>Semester</label>
            <select
              value={selectedSemester}
              onChange={(e) => {
                setSelectedSemester(e.target.value);
                setSelectedSection('');
              }}
              style={{ margin: '0.25rem 0 0', padding: '0.45rem 0.65rem', fontSize: '0.85rem' }}
            >
              {[1, 2, 3, 4, 5, 6, 7, 8].map((s) => (
                <option key={s} value={String(s)}>
                  Semester {s}
                </option>
              ))}
            </select>
          </div>

          <div style={{ flex: '1.2', minWidth: '160px' }}>
            <label style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-secondary)' }}>Section</label>
            <select
              value={selectedSection}
              onChange={(e) => setSelectedSection(e.target.value)}
              style={{ margin: '0.25rem 0 0', padding: '0.45rem 0.65rem', fontSize: '0.85rem' }}
            >
              <option value="">-- Choose Section --</option>
              {availableSections.map((c) => (
                <option key={c.class_id || c.id} value={String(c.class_id || c.id)}>
                  {c.class_name}
                </option>
              ))}
            </select>
          </div>

          <button
            className="btn"
            onClick={handleGenerateReport}
            style={{ padding: '0.45rem 1.15rem', fontSize: '0.85rem', height: '36px' }}
          >
            <Filter size={14} /> Filter
          </button>
        </div>
      </div>

      <ErrorMessage message={error} />

      {/* Official Attendance Report Document View */}
      {searched && (
        <div
          className="card report-official-document"
          style={{
            padding: '1.5rem',
            backgroundColor: 'var(--card-bg)',
            color: 'var(--text-color)',
            border: '1px solid var(--border-color)',
            boxShadow: 'var(--shadow-card)',
            borderRadius: 'var(--radius-md)',
          }}
        >
          {/* Header Banner */}
          <div
            style={{
              textAlign: 'center',
              borderBottom: '2px solid var(--border-color)',
              paddingBottom: '12px',
              marginBottom: '16px',
            }}
          >
            <h2
              style={{
                fontSize: '1.2rem',
                fontWeight: 900,
                textTransform: 'uppercase',
                letterSpacing: '0.5px',
                color: 'var(--text-color)',
                margin: 0,
              }}
            >
              SMART EXAM ATTENDANCE SYSTEM
            </h2>
            <h3
              style={{
                fontSize: '0.92rem',
                fontWeight: 700,
                margin: '4px 0',
                color: 'var(--text-secondary)',
              }}
            >
              OFFICIAL ATTENDANCE REPORT & REGISTER
            </h3>
            <div
              style={{
                fontSize: '0.825rem',
                display: 'flex',
                justifyContent: 'space-between',
                marginTop: '10px',
                color: 'var(--text-color)',
                fontWeight: 600,
                flexWrap: 'wrap',
                gap: '0.5rem',
              }}
            >
              <span><strong>Branch:</strong> {selectedBranch}</span>
              <span><strong>Semester:</strong> {selectedSemester}</span>
              <span><strong>Section:</strong> {getSectionName()}</span>
              <span><strong>Report Date:</strong> {new Date().toLocaleDateString('en-GB')}</span>
            </div>
          </div>

          {/* Date-Wise Attendance Report Table */}
          <div>
            <h4
              style={{
                fontSize: '0.875rem',
                fontWeight: 800,
                margin: '0 0 10px 0',
                textTransform: 'uppercase',
                color: 'var(--text-color)',
                letterSpacing: '0.03em',
              }}
            >
              DATE–WISE ATTENDANCE REPORT (P = PRESENT, A = ABSENT)
            </h4>

            {registerRows.length === 0 ? (
              <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', fontStyle: 'italic', padding: '1.5rem 0', textAlign: 'center' }}>
                No students enrolled in this section.
              </p>
            ) : (
              <div
                className="report-table-scroll-container"
                style={{
                  overflowX: 'auto',
                  WebkitOverflowScrolling: 'touch',
                  border: '1px solid var(--border-color)',
                  borderRadius: 'var(--radius-sm)',
                }}
              >
                <table style={{ width: '100%', minWidth: '600px', borderCollapse: 'collapse', margin: 0 }}>
                  <thead>
                    <tr style={{ backgroundColor: 'var(--hover-bg)' }}>
                      <th style={{ width: '40px', textAlign: 'center', fontSize: '0.75rem', padding: '8px 6px', color: 'var(--text-secondary)' }}>#</th>
                      <th style={{ width: '130px', fontSize: '0.75rem', padding: '8px 10px', color: 'var(--text-secondary)' }}>ROLL NO.</th>
                      <th style={{ fontSize: '0.75rem', padding: '8px 10px', color: 'var(--text-secondary)' }}>STUDENT NAME</th>
                      {uniqueDates.map((d) => (
                        <th
                          key={d}
                          style={{
                            textAlign: 'center',
                            fontSize: '0.75rem',
                            padding: '8px 8px',
                            color: 'var(--text-secondary)',
                            minWidth: '90px',
                          }}
                        >
                          {d}
                        </th>
                      ))}
                      <th
                        style={{
                          width: '110px',
                          textAlign: 'center',
                          fontSize: '0.75rem',
                          padding: '8px 10px',
                          color: 'var(--text-secondary)',
                        }}
                      >
                        TOTAL PRESENT
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {registerRows.map((r, i) => (
                      <tr
                        key={r.student_id}
                        style={{
                          borderBottom: '1px solid var(--border-color)',
                          transition: 'background-color 0.15s ease',
                        }}
                      >
                        <td style={{ textAlign: 'center', color: 'var(--text-secondary)', fontSize: '0.825rem' }}>
                          {i + 1}
                        </td>
                        <td style={{ fontWeight: 700, fontSize: '0.85rem', color: 'var(--text-color)' }}>
                          {r.student_id}
                        </td>
                        <td style={{ fontSize: '0.85rem', color: 'var(--text-color)' }}>
                          {r.student_name}
                        </td>
                        {uniqueDates.map((d) => {
                          const isPresent = r.presentDates.has(d);
                          return (
                            <td
                              key={d}
                              style={{
                                textAlign: 'center',
                                fontWeight: 800,
                                fontSize: '0.85rem',
                                color: isPresent ? 'var(--status-green)' : 'var(--status-red)',
                              }}
                            >
                              {isPresent ? 'P' : 'A'}
                            </td>
                          );
                        })}
                        <td style={{ textAlign: 'center', fontWeight: 800, fontSize: '0.85rem', color: 'var(--text-color)' }}>
                          {r.totalPresent} / {uniqueDates.length}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
