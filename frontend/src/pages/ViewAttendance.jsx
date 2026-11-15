import React, { useEffect, useState } from 'react';
import Loading from '../components/Loading';
import ErrorMessage from '../components/ErrorMessage';
import { getStudentById, getStudents } from '../services/studentService';
import { getClasses } from '../services/classService';
import { getAttendance, getMyAttendance } from '../services/attendanceService';
import { useAuth } from '../context/AuthContext';

export default function ViewAttendance() {
  const { user, isAdmin } = useAuth();
  const [classes, setClasses] = useState([]);
  const [allStudents, setAllStudents] = useState([]);
  const [selfStudent, setSelfStudent] = useState(null);
  const [selfRecords, setSelfRecords] = useState([]);

  const [selectedBranch, setSelectedBranch] = useState('');
  const [selectedSemester, setSelectedSemester] = useState('');
  const [selectedSection, setSelectedSection] = useState('');

  const [records, setRecords] = useState([]);
  const [uniqueDatesInClass, setUniqueDatesInClass] = useState([]);
  const [hasSearched, setHasSearched] = useState(false);
  const [loading, setLoading] = useState(true);
  const [searchLoading, setSearchLoading] = useState(false);
  const [error, setError] = useState('');

  // Table search & pagination state
  const [searchQuery, setSearchQuery] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 10;

  // Student Profile / Attendance Modal State
  const [selectedStudentForModal, setSelectedStudentForModal] = useState(null);
  const [studentStats, setStudentStats] = useState(null);

  useEffect(() => {
    async function initData() {
      try {
        if (isAdmin) {
          const [clsRes, stRes] = await Promise.all([getClasses(), getStudents()]);
          const classList = Array.isArray(clsRes) ? clsRes : (clsRes?.classes || []);
          const studentList = Array.isArray(stRes) ? stRes : (stRes?.students || []);
          setClasses(classList);
          setAllStudents(studentList);
        } else if (user?.username) {
          const [clsRes, stRes, attRes] = await Promise.all([
            getClasses().catch(() => []),
            getStudentById(user.username).catch(() => null),
            getMyAttendance().catch(() => ({ attendance: [] })),
          ]);
          const classList = Array.isArray(clsRes) ? clsRes : (clsRes?.classes || []);
          const stObj = stRes?.student || stRes;
          const attList = Array.isArray(attRes) ? attRes : (attRes?.attendance || []);
          setClasses(classList);
          setSelfStudent(stObj);
          setSelfRecords(attList);
        }
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    initData();
  }, [isAdmin, user]);

  // Filter sections by Branch and Semester
  const availableSections =
    selectedBranch && selectedSemester
      ? classes.filter(
          (c) =>
            String(c.department || '').trim().toUpperCase() === String(selectedBranch).trim().toUpperCase() &&
            String(c.semester) === String(selectedSemester)
        )
      : [];

  const getSectionName = () => {
    const sec = classes.find((c) => String(c.class_id || c.id) === String(selectedSection));
    return sec ? sec.class_name : `Section #${selectedSection}`;
  };

  const handleFetchAttendance = async (e) => {
    if (e) e.preventDefault();
    if (!selectedBranch || !selectedSemester || !selectedSection) {
      setError('Please select Branch, Semester, and Section first.');
      return;
    }

    setError('');
    setSearchLoading(true);
    setHasSearched(true);
    setCurrentPage(1);

    try {
      // Refresh students and all attendance records from MySQL
      const [allAttRes, freshStudentsRes] = await Promise.all([
        getAttendance().catch(() => []),
        getStudents().catch(() => allStudents),
      ]);

      const attList = Array.isArray(allAttRes) ? allAttRes : (allAttRes?.attendance || []);
      const currentStudents = Array.isArray(freshStudentsRes)
        ? freshStudentsRes
        : (freshStudentsRes?.students || allStudents);
      setAllStudents(currentStudents);

      // Filter students registered for the selected section
      const sectionStudents = currentStudents.filter(
        (st) => String(st.class_id) === String(selectedSection)
      );

      // Group all attendance records by student_id
      const attByStudent = {};
      const allDistinctDates = new Set();

      attList.forEach((att) => {
        const sid = String(att.student_id || '').trim();
        if (sid) {
          if (!attByStudent[sid]) attByStudent[sid] = [];
          attByStudent[sid].push(att);
        }
        if (att.attendance_date) {
          allDistinctDates.add(att.attendance_date);
        }
      });

      const sortedDates = Array.from(allDistinctDates).sort().reverse();
      setUniqueDatesInClass(sortedDates);

      // Combine student records with their attendance history and days present
      const combined = sectionStudents.map((st) => {
        const sid = String(st.student_id || st.id || '').trim();
        const studentAtts = attByStudent[sid] || [];

        // Sort descending by date & time
        studentAtts.sort((a, b) => {
          const dtA = `${a.attendance_date} ${a.attendance_time || ''}`;
          const dtB = `${b.attendance_date} ${b.attendance_time || ''}`;
          return dtB.localeCompare(dtA);
        });

        // Deduplicate records by date (1 record per day per student)
        const uniqueDayMap = new Map();
        studentAtts.forEach((att) => {
          if (!uniqueDayMap.has(att.attendance_date)) {
            uniqueDayMap.set(att.attendance_date, att);
          }
        });

        const deduplicatedRecords = Array.from(uniqueDayMap.values());
        const daysPresentList = Array.from(uniqueDayMap.keys()).sort().reverse();
        const latestRecord = deduplicatedRecords[0];

        return {
          student_id: sid,
          student_name: st.student_name || st.name || 'Unnamed',
          face_image: st.face_image,
          face_registered: st.face_registered,
          total_sessions: deduplicatedRecords.length,
          days_present_count: daysPresentList.length,
          days_present: daysPresentList,
          latest_date: latestRecord ? latestRecord.attendance_date : null,
          latest_time: latestRecord ? latestRecord.attendance_time : null,
          status: daysPresentList.length > 0 ? 'Present' : 'Absent',
          all_records: deduplicatedRecords,
        };
      });

      setRecords(combined);
    } catch (err) {
      setError(err.message);
    } finally {
      setSearchLoading(false);
    }
  };

  // Open Student History Modal
  const handleViewStudentHistory = (student) => {
    setSelectedStudentForModal(student);
    setStudentStats({
      totalAttendanceCount: student.days_present_count, // 1 mark per day
      daysPresentCount: student.days_present_count,
      daysPresent: student.days_present,
      history: student.all_records,
    });
  };

  // Filtered & Paginated records
  const filteredRecords = records.filter(
    (r) =>
      r.student_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      String(r.student_id).toLowerCase().includes(searchQuery.toLowerCase())
  );

  const totalStudentsCount = records.length;
  const presentCount = records.filter((r) => r.days_present_count > 0).length;
  const absentCount = totalStudentsCount - presentCount;
  const attendanceRate =
    totalStudentsCount > 0
      ? ((presentCount / totalStudentsCount) * 100).toFixed(1) + '%'
      : '0.0%';

  const totalPages = Math.ceil(filteredRecords.length / pageSize) || 1;
  const startIndex = (currentPage - 1) * pageSize;
  const paginatedRecords = filteredRecords.slice(startIndex, startIndex + pageSize);

  // Real, working CSV export with date-wise attendance columns
  const handleExportCSV = () => {
    if (records.length === 0) return;

    const secName = getSectionName();
    const dateHeaders = uniqueDatesInClass.map((d) => `"${d}"`);
    const headers = [
      '#',
      '"Roll No."',
      '"Student Name"',
      '"Total Days Present"',
      '"Latest Attendance Date"',
      '"Latest Attendance Time"',
      ...dateHeaders,
    ];

    const rows = records.map((r, i) => {
      const dateCols = uniqueDatesInClass.map((d) =>
        r.days_present.includes(d) ? '"Present (P)"' : '"Absent (A)"'
      );

      return [
        i + 1,
        `"${r.student_id}"`,
        `"${r.student_name}"`,
        r.days_present_count,
        r.latest_date ? `"${r.latest_date}"` : '"-"',
        r.latest_time ? `"${r.latest_time}"` : '"-"',
        ...dateCols,
      ].join(',');
    });

    const metadata = [
      `"Branch: ${selectedBranch}","Semester: ${selectedSemester}","Section: ${secName}"`,
      `"Total Enrolled: ${records.length}","Report Date: ${new Date().toLocaleDateString()}"`,
      '',
    ].join('\n');

    const csvContent = '\uFEFF' + metadata + headers.join(',') + '\n' + rows.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute(
      'download',
      `Attendance_Report_${selectedBranch}_Sem${selectedSemester}_${secName.replace(/\s+/g, '_')}.csv`
    );
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const handlePrint = () => {
    window.print();
  };

  if (loading) return <Loading />;

  // STUDENT SELF-VIEW: Only shows logged-in student's own attendance records
  if (!isAdmin) {
    const selfClass = classes.find((c) => String(c.class_id || c.id) === String(selfStudent?.class_id));
    const uniqueDayMap = new Map();
    selfRecords.forEach((att) => {
      if (att.attendance_date && !uniqueDayMap.has(att.attendance_date)) {
        uniqueDayMap.set(att.attendance_date, att);
      }
    });
    const dedupSelfRecords = Array.from(uniqueDayMap.values()).sort((a, b) =>
      `${b.attendance_date} ${b.attendance_time || ''}`.localeCompare(
        `${a.attendance_date} ${a.attendance_time || ''}`
      )
    );
    const filteredSelf = dedupSelfRecords.filter(
      (r) =>
        !searchQuery.trim() ||
        String(r.attendance_date).includes(searchQuery.trim()) ||
        String(r.status || '').toLowerCase().includes(searchQuery.trim().toLowerCase())
    );

    const handleExportSelfCSV = () => {
      const headers = ['#', '"Roll No."', '"Student Name"', '"Date"', '"Time"', '"Status"'];
      const rows = dedupSelfRecords.map((r, i) =>
        [
          i + 1,
          `"${user?.username || ''}"`,
          `"${selfStudent?.student_name || user?.full_name || ''}"`,
          `"${r.attendance_date}"`,
          `"${r.attendance_time || '-'}"`,
          `"${r.status || 'Present'}"`,
        ].join(',')
      );
      const csv = '\uFEFF' + headers.join(',') + '\n' + rows.join('\n');
      const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `My_Attendance_${user?.username || 'student'}.csv`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    };

    return (
      <div style={{ maxWidth: '1000px', margin: '0 auto' }}>
        <div style={{ marginBottom: '1.25rem' }}>
          <h1 style={{ fontSize: '1.65rem', fontWeight: 800, color: 'var(--text-color)', margin: 0 }}>
            My Attendance History
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginTop: '0.25rem' }}>
            Personal attendance records for Roll No. <strong>{user?.username}</strong>
          </p>
        </div>

        <ErrorMessage message={error} />

        {/* Profile & Summary Banner */}
        <div
          className="card"
          style={{
            padding: '1.25rem 1.5rem',
            marginBottom: '1.25rem',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: '1rem',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.9rem' }}>
            {selfStudent?.face_image ? (
              <img
                src={selfStudent.face_image}
                alt={selfStudent.student_name}
                style={{
                  width: '54px',
                  height: '54px',
                  borderRadius: '50%',
                  objectFit: 'cover',
                  border: '2px solid var(--status-green)',
                }}
              />
            ) : (
              <div
                style={{
                  width: '54px',
                  height: '54px',
                  borderRadius: '50%',
                  backgroundColor: 'var(--purple-subtle)',
                  color: 'var(--primary-purple)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontWeight: 800,
                  fontSize: '1.25rem',
                }}
              >
                {(selfStudent?.student_name || user?.full_name || 'S')[0].toUpperCase()}
              </div>
            )}
            <div>
              <h2 style={{ margin: 0, fontSize: '1.15rem', fontWeight: 800 }}>
                {selfStudent?.student_name || user?.full_name}
              </h2>
              <div style={{ fontSize: '0.84rem', color: 'var(--text-secondary)', marginTop: '0.2rem' }}>
                Roll No: <strong>{user?.username}</strong>
                {selfClass ? ` • ${selfClass.class_name} (${selfClass.department || ''} Sem ${selfClass.semester || ''})` : ''}
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '1.5rem', alignItems: 'center', flexWrap: 'wrap' }}>
            <div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', fontWeight: 700 }}>
                TOTAL DAYS PRESENT
              </div>
              <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--status-green)' }}>
                {dedupSelfRecords.length}
              </div>
            </div>
          </div>
        </div>

        {/* Self Attendance Table */}
        <div className="card" style={{ padding: '1.25rem 1.5rem' }}>
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              flexWrap: 'wrap',
              gap: '0.75rem',
              marginBottom: '1rem',
            }}
          >
            <input
              type="text"
              placeholder="Filter by date (YYYY-MM-DD)..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{ maxWidth: '260px', margin: 0, height: '38px' }}
            />
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <button type="button" className="btn btn-secondary" onClick={handleExportSelfCSV}>
                📥 Export My CSV
              </button>
              <button type="button" className="btn btn-secondary" onClick={() => window.print()}>
                🖨️ Print
              </button>
            </div>
          </div>

          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', minWidth: '500px', borderCollapse: 'collapse' }}>
              <thead>
                <tr>
                  <th style={{ width: '50px' }}>#</th>
                  <th>Date</th>
                  <th>Time</th>
                  <th>Status</th>
                  <th>Verification Score</th>
                </tr>
              </thead>
              <tbody>
                {filteredSelf.length === 0 ? (
                  <tr>
                    <td colSpan={5} style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-secondary)' }}>
                      No attendance records found yet.
                    </td>
                  </tr>
                ) : (
                  filteredSelf.map((rec, idx) => (
                    <tr key={rec.id || `${rec.attendance_date}-${idx}`}>
                      <td>{idx + 1}</td>
                      <td><strong>{rec.attendance_date}</strong></td>
                      <td>{rec.attendance_time || '-'}</td>
                      <td>
                        <span className="badge badge-present">{rec.status || 'Present'}</span>
                      </td>
                      <td style={{ color: 'var(--text-secondary)' }}>
                        {rec.verification_score ? `${(rec.verification_score * 100).toFixed(1)}%` : 'Live Verified'}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
      {/* Header & Breadcrumb (Hidden during Print) */}
      <div
        className="no-print"
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          marginBottom: '1.5rem',
        }}
      >
        <div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--text-color)' }}>
            View Attendance
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', marginTop: '0.25rem' }}>
            Check student attendance details and day-by-day attendance history
          </p>
        </div>
        <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
          Dashboard &nbsp;&gt;&nbsp; <span style={{ color: 'var(--primary-color)', fontWeight: 600 }}>View Attendance</span>
        </div>
      </div>

      <ErrorMessage message={error} />

      {/* Select Filters Card: ONLY Branch, Semester, Section (Hidden during Print) */}
      <div className="card no-print" style={{ marginBottom: '1.5rem', padding: '1.25rem 1.5rem' }}>
        <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '1rem', color: 'var(--text-color)' }}>
          Select Filters
        </h3>

        <form
          onSubmit={handleFetchAttendance}
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr)) auto',
            gap: '1.25rem',
            alignItems: 'end',
          }}
        >
          <div>
            <label style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)', display: 'block', marginBottom: '0.35rem' }}>
              Branch (Department)
            </label>
            <select
              value={selectedBranch}
              onChange={(e) => {
                setSelectedBranch(e.target.value);
                setSelectedSection('');
              }}
              style={{ margin: 0 }}
              required
            >
              <option value="">Select Branch</option>
              <option value="CSE">CSE (Computer Science & Engineering)</option>
              <option value="IT">IT (Information Technology)</option>
              <option value="ECE">ECE (Electronics & Communication)</option>
              <option value="ME">ME (Mechanical Engineering)</option>
              <option value="Civil">Civil Engineering</option>
            </select>
          </div>

          <div>
            <label style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)', display: 'block', marginBottom: '0.35rem' }}>
              Semester
            </label>
            <select
              value={selectedSemester}
              onChange={(e) => {
                setSelectedSemester(e.target.value);
                setSelectedSection('');
              }}
              style={{ margin: 0 }}
              required
            >
              <option value="">Select Semester</option>
              {[1, 2, 3, 4, 5, 6, 7, 8].map((s) => (
                <option key={s} value={s}>
                  Semester {s}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)', display: 'block', marginBottom: '0.35rem' }}>
              Section
            </label>
            <select
              value={selectedSection}
              onChange={(e) => setSelectedSection(e.target.value)}
              style={{ margin: 0 }}
              required
              disabled={!selectedBranch || !selectedSemester || availableSections.length === 0}
            >
              <option value="">
                {!selectedBranch || !selectedSemester
                  ? 'Select Branch & Semester first'
                  : availableSections.length === 0
                  ? 'No Sections Available'
                  : 'Select Section'}
              </option>
              {availableSections.map((c) => (
                <option key={c.class_id || c.id} value={c.class_id || c.id}>
                  {c.class_name} ({c.department || selectedBranch})
                </option>
              ))}
            </select>
          </div>

          <div>
            <button
              type="submit"
              className="btn"
              style={{
                height: '42px',
                padding: '0 1.5rem',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.5rem',
                fontWeight: 700,
                whiteSpace: 'nowrap',
              }}
              disabled={searchLoading}
            >
              <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              {searchLoading ? 'Fetching...' : 'View Attendance'}
            </button>
          </div>
        </form>
      </div>

      {/* =========================================================================
          SCREEN INTERACTIVE VIEW (Summary Cards, Main Table, Actions)
          ========================================================================= */}
      {hasSearched && (
        <>
          {/* Summary Stat Cards (Hidden during Print) */}
          <div
            className="no-print"
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
              gap: '1rem',
              marginBottom: '1.5rem',
            }}
          >
            {/* Total Students */}
            <div
              className="card"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '1rem',
                borderLeft: '4px solid var(--primary-color)',
              }}
            >
              <div
                style={{
                  width: '44px',
                  height: '44px',
                  borderRadius: '50%',
                  background: 'var(--primary-color)',
                  color: '#ffffff',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                👥
              </div>
              <div>
                <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', fontWeight: 600 }}>
                  Total Students in Class
                </div>
                <div style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--text-color)' }}>
                  {totalStudentsCount}
                </div>
              </div>
            </div>

            {/* Students Attended */}
            <div
              className="card"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '1rem',
                borderLeft: '4px solid var(--status-green)',
              }}
            >
              <div
                style={{
                  width: '44px',
                  height: '44px',
                  borderRadius: '50%',
                  background: 'var(--status-green)',
                  color: '#ffffff',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                ✓
              </div>
              <div>
                <div style={{ fontSize: '0.85rem', color: 'var(--status-green)', fontWeight: 600 }}>
                  Attended Students
                </div>
                <div style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--text-color)' }}>
                  {presentCount}
                </div>
              </div>
            </div>

            {/* Not Yet Attended */}
            <div
              className="card"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '1rem',
                borderLeft: '4px solid var(--status-red)',
              }}
            >
              <div
                style={{
                  width: '44px',
                  height: '44px',
                  borderRadius: '50%',
                  background: 'var(--status-red)',
                  color: '#ffffff',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                ✕
              </div>
              <div>
                <div style={{ fontSize: '0.85rem', color: 'var(--status-red)', fontWeight: 600 }}>
                  Zero Attendance
                </div>
                <div style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--text-color)' }}>
                  {absentCount}
                </div>
              </div>
            </div>

            {/* Class Attendance Rate */}
            <div
              className="card"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '1rem',
                borderLeft: '4px solid #8b5cf6',
              }}
            >
              <div
                style={{
                  width: '44px',
                  height: '44px',
                  borderRadius: '50%',
                  background: '#8b5cf6',
                  color: '#ffffff',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                📊
              </div>
              <div>
                <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', fontWeight: 600 }}>
                  Active Rate
                </div>
                <div style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--text-color)' }}>
                  {attendanceRate}
                </div>
              </div>
            </div>
          </div>

          {/* Student Attendance Table Card */}
          <div className="card no-print" style={{ padding: '1.25rem 1.5rem' }}>
            {/* Header: Title + Search + Export/Print */}
            <div
              style={{
                display: 'flex',
                flexWrap: 'wrap',
                justifyContent: 'space-between',
                alignItems: 'center',
                gap: '1rem',
                marginBottom: '1rem',
              }}
            >
              <div>
                <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--text-color)', margin: 0 }}>
                  Attendance Details
                </h3>
                <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                  {selectedBranch} — Semester {selectedSemester} ({getSectionName()})
                </span>
              </div>

              <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: '0.75rem' }}>
                {/* Search Field */}
                <div style={{ position: 'relative', minWidth: '240px' }}>
                  <input
                    type="text"
                    placeholder="Search by name or roll..."
                    value={searchQuery}
                    onChange={(e) => {
                      setSearchQuery(e.target.value);
                      setCurrentPage(1);
                    }}
                    style={{
                      margin: 0,
                      paddingLeft: '2.25rem',
                      height: '38px',
                      fontSize: '0.875rem',
                    }}
                  />
                  <svg
                    width="16"
                    height="16"
                    fill="none"
                    stroke="#94a3b8"
                    viewBox="0 0 24 24"
                    style={{ position: 'absolute', left: '10px', top: '11px' }}
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                </div>

                {/* Real CSV Export Button */}
                <button
                  type="button"
                  onClick={handleExportCSV}
                  className="btn btn-secondary"
                  title="Download complete attendance spreadsheet (.csv)"
                  style={{
                    height: '38px',
                    fontSize: '0.85rem',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '0.4rem',
                    padding: '0 0.85rem',
                    cursor: 'pointer',
                  }}
                >
                  📥 Export CSV
                </button>

                {/* Real Print / PDF Option */}
                <button
                  type="button"
                  onClick={handlePrint}
                  className="btn btn-secondary"
                  title="Print attendance sheet or Save as PDF"
                  style={{
                    height: '38px',
                    fontSize: '0.85rem',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '0.4rem',
                    padding: '0 0.85rem',
                    cursor: 'pointer',
                  }}
                >
                  🖨️ Print / PDF
                </button>
              </div>
            </div>

            {/* Main Table: #, Photo, Roll No., Student Name, Total Present, Latest Attendance, Action (Days Present REMOVED) */}
            <div className="responsive-table-wrapper" style={{ overflowX: 'auto', WebkitOverflowScrolling: 'touch', width: '100%' }}>
              <table style={{ minWidth: '600px' }}>
                <thead>
                  <tr>
                    <th style={{ width: '45px' }}>#</th>
                    <th style={{ width: '60px' }}>Photo</th>
                    <th>Roll No.</th>
                    <th>Student Name</th>
                    <th>Total Present</th>
                    <th>Latest Attendance</th>
                    <th style={{ textAlign: 'center', width: '90px' }}>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredRecords.length === 0 ? (
                    <tr>
                      <td colSpan="7" style={{ textAlign: 'center', padding: '2.5rem', color: 'var(--text-secondary)' }}>
                        No students found for this section / search filter.
                      </td>
                    </tr>
                  ) : (
                    paginatedRecords.map((r, idx) => {
                      const rowNum = startIndex + idx + 1;
                      const hasAttended = r.days_present_count > 0;
                      return (
                        <tr key={r.student_id}>
                          <td>{rowNum}</td>
                          <td>
                            {r.face_image ? (
                              <img
                                src={r.face_image}
                                alt={r.student_name}
                                style={{
                                  width: '38px',
                                  height: '38px',
                                  borderRadius: '50%',
                                  objectFit: 'cover',
                                  border: '2px solid var(--border-color)',
                                }}
                              />
                            ) : (
                              <div
                                style={{
                                  width: '38px',
                                  height: '38px',
                                  borderRadius: '50%',
                                  backgroundColor: 'var(--hover-bg)',
                                  color: 'var(--text-secondary)',
                                  display: 'flex',
                                  alignItems: 'center',
                                  justifyContent: 'center',
                                  fontWeight: 700,
                                  fontSize: '0.85rem',
                                  border: '1px solid var(--border-color)',
                                }}
                              >
                                {r.student_name ? r.student_name[0].toUpperCase() : 'S'}
                              </div>
                            )}
                          </td>
                          <td>
                            <strong>{r.student_id}</strong>
                          </td>
                          <td style={{ fontWeight: 600 }}>{r.student_name}</td>
                          <td>
                            <span className={hasAttended ? 'badge badge-present' : 'badge badge-absent'}>
                              {r.days_present_count} {r.days_present_count === 1 ? 'Day' : 'Days'} Present
                            </span>
                          </td>
                          <td>
                            {r.latest_date ? (
                              <span style={{ fontSize: '0.85rem' }}>
                                {r.latest_date} at {r.latest_time || ''}
                              </span>
                            ) : (
                              <span style={{ color: 'var(--text-secondary)' }}>-</span>
                            )}
                          </td>
                          <td style={{ textAlign: 'center' }}>
                            <button
                              type="button"
                              className="btn btn-secondary"
                              onClick={() => handleViewStudentHistory(r)}
                              style={{
                                padding: '0.3rem 0.75rem',
                                fontSize: '0.8rem',
                              }}
                            >
                              Details
                            </button>
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>

            {/* Footer / Pagination */}
            {filteredRecords.length > 0 && (
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginTop: '1.25rem',
                  paddingTop: '0.75rem',
                  borderTop: '1px solid var(--border-color)',
                  fontSize: '0.85rem',
                  color: 'var(--text-secondary)',
                }}
              >
                <div>
                  Showing {startIndex + 1} to {Math.min(startIndex + pageSize, filteredRecords.length)} of {filteredRecords.length} students
                </div>

                <div style={{ display: 'flex', gap: '0.25rem' }}>
                  <button
                    disabled={currentPage === 1}
                    onClick={() => setCurrentPage((p) => Math.max(p - 1, 1))}
                    style={{
                      padding: '0.35rem 0.65rem',
                      border: '1px solid var(--border-color)',
                      background: 'var(--card-bg)',
                      color: 'var(--text-color)',
                      borderRadius: '6px',
                      cursor: currentPage === 1 ? 'not-allowed' : 'pointer',
                      opacity: currentPage === 1 ? 0.5 : 1,
                    }}
                  >
                    &lt;
                  </button>

                  {Array.from({ length: totalPages }, (_, i) => i + 1).map((pageNum) => (
                    <button
                      key={pageNum}
                      onClick={() => setCurrentPage(pageNum)}
                      style={{
                        padding: '0.35rem 0.65rem',
                        border: '1px solid var(--border-color)',
                        background: pageNum === currentPage ? 'var(--primary-color)' : 'var(--card-bg)',
                        color: pageNum === currentPage ? '#ffffff' : 'var(--text-color)',
                        borderRadius: '6px',
                        cursor: 'pointer',
                        fontWeight: pageNum === currentPage ? 700 : 400,
                      }}
                    >
                      {pageNum}
                    </button>
                  ))}

                  <button
                    disabled={currentPage === totalPages}
                    onClick={() => setCurrentPage((p) => Math.min(p + 1, totalPages))}
                    style={{
                      padding: '0.35rem 0.65rem',
                      border: '1px solid var(--border-color)',
                      background: 'var(--card-bg)',
                      color: 'var(--text-color)',
                      borderRadius: '6px',
                      cursor: currentPage === totalPages ? 'not-allowed' : 'pointer',
                      opacity: currentPage === totalPages ? 0.5 : 1,
                    }}
                  >
                    &gt;
                  </button>
                </div>
              </div>
            )}
          </div>
        </>
      )}

      {/* Student Attendance Profile Modal */}
      {selectedStudentForModal && (
        <div
          className="no-print"
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.75)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            padding: '1rem',
          }}
        >
          <div
            className="card"
            style={{
              width: '95%',
              maxWidth: '560px',
              backgroundColor: 'var(--card-bg)',
              borderRadius: '12px',
              padding: '1.75rem',
              boxShadow: 'var(--shadow-md)',
              maxHeight: '90vh',
              overflowY: 'auto',
            }}
          >
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '1.25rem',
                borderBottom: '1px solid var(--border-color)',
                paddingBottom: '0.85rem',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
                {selectedStudentForModal.face_image ? (
                  <img
                    src={selectedStudentForModal.face_image}
                    alt={selectedStudentForModal.student_name}
                    style={{
                      width: '48px',
                      height: '48px',
                      borderRadius: '50%',
                      objectFit: 'cover',
                      border: '2px solid var(--status-green)',
                    }}
                  />
                ) : (
                  <div
                    style={{
                      width: '48px',
                      height: '48px',
                      borderRadius: '50%',
                      backgroundColor: 'var(--hover-bg)',
                      color: 'var(--text-color)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontWeight: 700,
                      fontSize: '1.1rem',
                      border: '1px solid var(--border-color)',
                    }}
                  >
                    {selectedStudentForModal.student_name ? selectedStudentForModal.student_name[0].toUpperCase() : 'S'}
                  </div>
                )}
                <div>
                  <h3 style={{ fontSize: '1.25rem', fontWeight: 800, margin: 0 }}>
                    {selectedStudentForModal.student_name}
                  </h3>
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', margin: '0.2rem 0 0' }}>
                    Roll / Student ID: <strong>{selectedStudentForModal.student_id}</strong>
                  </p>
                </div>
              </div>

              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => setSelectedStudentForModal(null)}
                style={{ padding: '0.35rem 0.75rem', fontSize: '0.9rem' }}
              >
                ✕ Close
              </button>
            </div>

            {studentStats && (
              <div>
                {/* Clean, Single Metric as requested: Total Attendance Marks (how many days present) */}
                <div
                  className="card"
                  style={{
                    padding: '1rem',
                    borderRadius: '8px',
                    borderLeft: '4px solid var(--primary-color)',
                    marginBottom: '1.25rem',
                  }}
                >
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', fontWeight: 600 }}>
                    Total Attendance Marks
                  </div>
                  <div style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--text-color)', marginTop: '0.25rem' }}>
                    {studentStats.daysPresentCount} {studentStats.daysPresentCount === 1 ? 'Day' : 'Days'} Present
                  </div>
                </div>

                <h4 style={{ fontSize: '0.95rem', fontWeight: 700, marginBottom: '0.5rem', color: 'var(--text-color)' }}>
                  Marked Attendance Dates
                </h4>

                {studentStats.history.length === 0 ? (
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', padding: '1rem', textAlign: 'center' }}>
                    No recorded attendance logs found for this student.
                  </p>
                ) : (
                  <div style={{ maxHeight: '220px', overflowY: 'auto' }}>
                    <table style={{ margin: 0 }}>
                      <thead>
                        <tr>
                          <th>Date</th>
                          <th>Time</th>
                          <th>Status</th>
                          <th>Score</th>
                        </tr>
                      </thead>
                      <tbody>
                        {studentStats.history.map((h, i) => (
                          <tr key={i}>
                            <td>📅 {h.attendance_date}</td>
                            <td>{h.attendance_time || '-'}</td>
                            <td className="text-green" style={{ fontWeight: 600 }}>{h.status || 'Present'}</td>
                            <td style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                              {h.verification_score ? `${(h.verification_score * 100).toFixed(1)}%` : '-'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
