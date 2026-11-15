// src/pages/Classes.jsx
import React, { useEffect, useState, useMemo } from 'react';
import Loading from '../components/Loading';
import ErrorMessage from '../components/ErrorMessage';
import {
  getClasses,
  createClass,
  updateClass,
  deleteClass,
  getClassStudents,
} from '../services/classService';
import { getStudents } from '../services/studentService';
import { Users, X, CheckCircle2, Search, Info } from 'lucide-react';

export default function Classes() {
  const [classes, setClasses] = useState([]);
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [editingId, setEditingId] = useState(null);

  // Selected Section & Students Modal State
  const [selectedClass, setSelectedClass] = useState(null);
  const [sectionStudents, setSectionStudents] = useState([]);
  const [studentLoading, setStudentLoading] = useState(false);
  const [studentSearch, setStudentSearch] = useState('');

  const [formData, setFormData] = useState({
    class_name: '',
    department: 'CSE',
    semester: '1',
  });

  const loadData = async () => {
    try {
      const [clsData, stData] = await Promise.all([getClasses(), getStudents()]);
      const classList = Array.isArray(clsData) ? clsData : (clsData?.classes || []);
      const studentList = Array.isArray(stData) ? stData : (stData?.students || []);
      setClasses(classList);
      setStudents(studentList);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    try {
      const payload = {
        class_name: formData.class_name.trim(),
        department: formData.department.trim(),
        semester: Number(formData.semester),
      };

      if (editingId) {
        await updateClass(editingId, payload);
      } else {
        await createClass(payload);
      }

      setFormData({
        class_name: '',
        department: 'CSE',
        semester: '1',
      });

      setEditingId(null);
      await loadData();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleEdit = (cls) => {
    const id = cls.class_id || cls.id;
    setEditingId(id);
    setFormData({
      class_name: cls.class_name || '',
      department: cls.department || 'CSE',
      semester: cls.semester ? String(cls.semester) : '1',
    });
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Delete section?')) return;
    try {
      await deleteClass(id);
      if (selectedClass && (selectedClass.class_id === id || selectedClass.id === id)) {
        setSelectedClass(null);
      }
      await loadData();
    } catch (err) {
      setError(err.message);
    }
  };

  // Open Section Students View
  const handleViewStudents = async (cls) => {
    setSelectedClass(cls);
    setStudentSearch('');
    const id = cls.class_id || cls.id;

    // Fast initial fill from cached students list
    const cached = students.filter((s) => s.class_id === id);
    setSectionStudents(cached);

    // Fetch fresh records from backend
    try {
      setStudentLoading(true);
      const res = await getClassStudents(id);
      const list = Array.isArray(res) ? res : (res?.students || []);
      setSectionStudents(list);
    } catch {
      // Keep cached if API call fails
    } finally {
      setStudentLoading(false);
    }
  };

  // Filter students by search in modal
  const filteredSectionStudents = useMemo(() => {
    if (!studentSearch.trim()) return sectionStudents;
    const q = studentSearch.toLowerCase();
    return sectionStudents.filter(
      (s) =>
        (s.student_name && s.student_name.toLowerCase().includes(q)) ||
        (s.student_id && String(s.student_id).toLowerCase().includes(q))
    );
  }, [sectionStudents, studentSearch]);

  if (loading) return <Loading />;

  return (
    <div style={{ maxWidth: '1100px', margin: '0 auto', width: '100%' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem', flexWrap: 'wrap', gap: '0.75rem' }}>
        <div>
          <h1 style={{ fontSize: '1.4rem', fontWeight: 800, margin: 0, color: 'var(--text-color)' }}>
            Manage Sections
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.825rem', marginTop: '0.2rem' }}>
            Academic classes, departments, and enrolled student rosters
          </p>
        </div>
      </div>

      <ErrorMessage message={error} />

      {/* Add / Edit Section Form */}
      <form
        onSubmit={handleSubmit}
        className="card"
        style={{
          maxWidth: '520px',
          marginBottom: '1.75rem',
          padding: '1.25rem 1.5rem',
        }}
      >
        <h3 style={{ fontSize: '1.05rem', fontWeight: 700, marginBottom: '1rem', color: 'var(--text-color)' }}>
          {editingId ? 'Edit Section' : 'Add Section'}
        </h3>

        <div style={{ marginBottom: '0.85rem' }}>
          <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>
            Section Name
          </label>
          <input
            type="text"
            value={formData.class_name}
            placeholder="e.g. CSE-09, IT-26"
            onChange={(e) =>
              setFormData({
                ...formData,
                class_name: e.target.value,
              })
            }
            required
            style={{ width: '100%' }}
          />
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', marginBottom: '1.2rem' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>
              Department
            </label>
            <select
              value={formData.department}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  department: e.target.value,
                })
              }
              required
              style={{ width: '100%' }}
            >
              <option value="CSE">CSE</option>
              <option value="IT">IT</option>
            </select>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>
              Semester
            </label>
            <select
              value={formData.semester}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  semester: e.target.value,
                })
              }
              required
              style={{ width: '100%' }}
            >
              <option value="1">Semester 1</option>
              <option value="2">Semester 2</option>
              <option value="3">Semester 3</option>
              <option value="4">Semester 4</option>
              <option value="5">Semester 5</option>
              <option value="6">Semester 6</option>
              <option value="7">Semester 7</option>
              <option value="8">Semester 8</option>
            </select>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button type="submit" className="btn" style={{ flex: 1 }}>
            {editingId ? 'Update Section' : 'Add Section'}
          </button>

          {editingId && (
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => {
                setEditingId(null);
                setFormData({
                  class_name: '',
                  department: 'CSE',
                  semester: '1',
                });
              }}
            >
              Cancel
            </button>
          )}
        </div>
      </form>

      {/* Sections Table Card */}
      <div className="card" style={{ padding: '1.25rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem', flexWrap: 'wrap', gap: '0.5rem' }}>
          <h3 style={{ fontSize: '1rem', fontWeight: 700, margin: 0, color: 'var(--text-color)' }}>
            All Academic Sections ({classes.length})
          </h3>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', display: 'inline-flex', alignItems: 'center', gap: '0.35rem' }}>
            <Info size={13} /> Click any section row or &quot;Students&quot; button to view student list
          </span>
        </div>

        <div style={{ overflowX: 'auto', WebkitOverflowScrolling: 'touch' }}>
          <table style={{ width: '100%', minWidth: '600px', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ backgroundColor: 'var(--hover-bg)' }}>
                <th style={{ padding: '10px 12px' }}>Section Name</th>
                <th style={{ padding: '10px 12px' }}>Department</th>
                <th style={{ padding: '10px 12px' }}>Semester</th>
                <th style={{ padding: '10px 12px' }}>Total Students</th>
                <th style={{ padding: '10px 12px', textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {classes.length === 0 ? (
                <tr>
                  <td colSpan={5} style={{ textAlign: 'center', padding: '2rem 1rem', color: 'var(--text-secondary)' }}>
                    No sections added yet. Create one using the form above.
                  </td>
                </tr>
              ) : (
                classes.map((c) => {
                  const id = c.class_id || c.id;
                  const totalStudents = students.filter(
                    (s) => s.class_id === id
                  ).length;

                  return (
                    <tr
                      key={id}
                      onClick={() => handleViewStudents(c)}
                      style={{
                        cursor: 'pointer',
                        transition: 'background-color 0.15s ease',
                      }}
                      title={`Click to view students in ${c.class_name}`}
                    >
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem' }}>
                          <strong style={{ color: 'var(--text-color)', fontSize: '0.9rem' }}>
                            {c.class_name}
                          </strong>
                          <span
                            style={{
                              fontSize: '0.68rem',
                              color: 'var(--primary-purple)',
                              fontWeight: 600,
                              opacity: 0.85,
                            }}
                          >
                            (view list)
                          </span>
                        </div>
                      </td>
                      <td style={{ color: 'var(--text-secondary)' }}>{c.department || '-'}</td>
                      <td style={{ color: 'var(--text-secondary)' }}>Semester {c.semester || '-'}</td>
                      <td>
                        <span
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '0.35rem',
                            padding: '0.25rem 0.65rem',
                            borderRadius: 'var(--radius-full)',
                            fontSize: '0.78rem',
                            fontWeight: 700,
                            backgroundColor: totalStudents > 0 ? 'var(--status-blue-bg)' : 'var(--hover-bg)',
                            color: totalStudents > 0 ? 'var(--status-blue)' : 'var(--text-secondary)',
                          }}
                        >
                          <Users size={12} />
                          {totalStudents} {totalStudents === 1 ? 'Student' : 'Students'}
                        </span>
                      </td>
                      <td style={{ textAlign: 'right' }}>
                        <div style={{ display: 'inline-flex', gap: '0.4rem', alignItems: 'center' }}>
                          <button
                            className="btn btn-secondary"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleViewStudents(c);
                            }}
                            style={{ fontSize: '0.75rem', padding: '0.3rem 0.65rem' }}
                            title="View student list"
                          >
                            <Users size={13} style={{ marginRight: '4px' }} /> Students
                          </button>
                          <button
                            className="btn"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleEdit(c);
                            }}
                            style={{ fontSize: '0.75rem', padding: '0.3rem 0.65rem' }}
                          >
                            Edit
                          </button>
                          <button
                            className="btn text-red"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDelete(id);
                            }}
                            style={{ fontSize: '0.75rem', padding: '0.3rem 0.65rem' }}
                          >
                            Delete
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* MODAL: Enrolled Students of Section */}
      {selectedClass && (
        <div className="modal-backdrop" onClick={() => setSelectedClass(null)}>
          <div
            className="modal-content"
            style={{
              maxWidth: '640px',
              width: '95%',
              maxHeight: '85vh',
              backgroundColor: 'var(--card-bg)',
              borderRadius: 'var(--radius-lg)',
              border: '1px solid var(--border-color)',
              boxShadow: 'var(--shadow-hover)',
              display: 'flex',
              flexDirection: 'column',
              overflow: 'hidden',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div
              className="modal-header"
              style={{
                padding: '1.15rem 1.4rem',
                borderBottom: '1px solid var(--border-color)',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}
            >
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
                  <h3 style={{ margin: 0, fontSize: '1.2rem', fontWeight: 800, color: 'var(--text-color)' }}>
                    {selectedClass.class_name}
                  </h3>
                  <span
                    style={{
                      fontSize: '0.75rem',
                      fontWeight: 700,
                      padding: '0.2rem 0.55rem',
                      borderRadius: '6px',
                      backgroundColor: 'var(--status-blue-bg)',
                      color: 'var(--status-blue)',
                    }}
                  >
                    {selectedClass.department} • Semester {selectedClass.semester}
                  </span>
                </div>
                <p style={{ margin: '0.3rem 0 0', fontSize: '0.825rem', color: 'var(--text-secondary)' }}>
                  Enrolled Students ({filteredSectionStudents.length} of {sectionStudents.length})
                </p>
              </div>

              <button
                onClick={() => setSelectedClass(null)}
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: 'var(--text-secondary)',
                  cursor: 'pointer',
                  padding: '0.4rem',
                  borderRadius: '6px',
                  display: 'flex',
                  alignItems: 'center',
                }}
                aria-label="Close modal"
              >
                <X size={20} />
              </button>
            </div>

            {/* Optional Search Filter in Modal */}
            {sectionStudents.length > 3 && (
              <div
                style={{
                  padding: '0.65rem 1.4rem',
                  borderBottom: '1px solid var(--border-color)',
                  backgroundColor: 'var(--hover-bg)',
                }}
              >
                <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
                  <Search
                    size={14}
                    style={{
                      position: 'absolute',
                      left: '10px',
                      color: 'var(--text-secondary)',
                    }}
                  />
                  <input
                    type="text"
                    placeholder="Search students by name or roll number..."
                    value={studentSearch}
                    onChange={(e) => setStudentSearch(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '0.45rem 0.75rem 0.45rem 2rem',
                      fontSize: '0.825rem',
                      borderRadius: 'var(--radius-sm)',
                    }}
                  />
                </div>
              </div>
            )}

            {/* Modal Body: Student List Table */}
            <div
              className="modal-body"
              style={{
                padding: '1.25rem 1.4rem',
                overflowY: 'auto',
                flex: 1,
              }}
            >
              {studentLoading ? (
                <div style={{ textAlign: 'center', padding: '2rem 0', color: 'var(--text-secondary)' }}>
                  Loading students...
                </div>
              ) : filteredSectionStudents.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '2.5rem 1rem' }}>
                  <Users size={36} style={{ color: 'var(--text-secondary)', opacity: 0.5, marginBottom: '0.75rem' }} />
                  <h4 style={{ margin: '0 0 0.4rem', color: 'var(--text-color)', fontSize: '1rem' }}>
                    {studentSearch ? 'No matching students' : 'No Students Enrolled'}
                  </h4>
                  <p style={{ margin: 0, fontSize: '0.825rem', color: 'var(--text-secondary)' }}>
                    {studentSearch
                      ? `No students in ${selectedClass.class_name} match "${studentSearch}"`
                      : `No students have been assigned to section ${selectedClass.class_name} yet.`}
                  </p>
                </div>
              ) : (
                <div style={{ overflowX: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', margin: 0 }}>
                    <thead>
                      <tr style={{ backgroundColor: 'var(--hover-bg)' }}>
                        <th style={{ width: '40px', textAlign: 'center', padding: '8px 6px', fontSize: '0.72rem' }}>#</th>
                        <th style={{ padding: '8px 10px', fontSize: '0.72rem' }}>ROLL NO.</th>
                        <th style={{ padding: '8px 10px', fontSize: '0.72rem' }}>STUDENT NAME</th>
                        <th style={{ padding: '8px 10px', fontSize: '0.72rem', textAlign: 'center' }}>FACE STATUS</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredSectionStudents.map((st, idx) => (
                        <tr key={st.student_id} style={{ borderBottom: '1px solid var(--border-color)' }}>
                          <td style={{ textAlign: 'center', color: 'var(--text-secondary)', fontSize: '0.8rem' }}>
                            {idx + 1}
                          </td>
                          <td style={{ fontWeight: 700, fontSize: '0.85rem', color: 'var(--text-color)' }}>
                            {st.student_id}
                          </td>
                          <td style={{ fontSize: '0.85rem', color: 'var(--text-color)' }}>
                            {st.student_name}
                          </td>
                          <td style={{ textAlign: 'center' }}>
                            {st.face_registered ? (
                              <span
                                style={{
                                  fontSize: '0.72rem',
                                  fontWeight: 700,
                                  padding: '0.2rem 0.55rem',
                                  borderRadius: 'var(--radius-full)',
                                  backgroundColor: 'var(--status-green-bg)',
                                  color: 'var(--status-green)',
                                  display: 'inline-flex',
                                  alignItems: 'center',
                                  gap: '0.3rem',
                                }}
                              >
                                <CheckCircle2 size={12} /> Registered
                              </span>
                            ) : (
                              <span
                                style={{
                                  fontSize: '0.72rem',
                                  fontWeight: 700,
                                  padding: '0.2rem 0.55rem',
                                  borderRadius: 'var(--radius-full)',
                                  backgroundColor: 'var(--status-amber-bg)',
                                  color: 'var(--status-amber)',
                                }}
                              >
                                Pending
                              </span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div
              style={{
                padding: '0.75rem 1.4rem',
                borderTop: '1px solid var(--border-color)',
                display: 'flex',
                justifyContent: 'flex-end',
                backgroundColor: 'var(--hover-bg)',
              }}
            >
              <button
                className="btn btn-secondary"
                onClick={() => setSelectedClass(null)}
                style={{ fontSize: '0.825rem', padding: '0.4rem 1rem' }}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
