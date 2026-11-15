// src/pages/Students.jsx
import React, { useEffect, useState } from 'react';
import Loading from '../components/Loading';
import ErrorMessage from '../components/ErrorMessage';
import { getStudents, deleteStudent } from '../services/studentService';
import { getClasses } from '../services/classService';

export default function Students() {
  const [students, setStudents] = useState([]);
  const [classes, setClasses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const loadData = async () => {
    try {
      const [stList, clsList] = await Promise.all([getStudents(), getClasses()]);
      const stArr = Array.isArray(stList) ? stList : (stList?.students || []);
      const clsArr = Array.isArray(clsList) ? clsList : (clsList?.classes || []);
      setStudents(stArr);
      setClasses(clsArr);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this student?')) return;
    try {
      await deleteStudent(id);
      loadData();
    } catch (err) {
      setError(err.message);
    }
  };

  if (loading) return <Loading />;

  return (
    <div>
      <h1 style={{ marginBottom: '0.5rem', fontSize: '1.75rem', fontWeight: 800 }}>Students Directory</h1>
      <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem', fontSize: '0.95rem' }}>
        View all enrolled students and their registered face photos
      </p>

      <ErrorMessage message={error} />

      <div className="card" style={{ padding: '1rem', width: '100%', overflow: 'hidden' }}>
        <div className="responsive-table-wrapper" style={{ overflowX: 'auto', WebkitOverflowScrolling: 'touch', width: '100%' }}>
          <table style={{ minWidth: '650px', borderCollapse: 'collapse', margin: 0 }}>
            <thead>
              <tr>
                <th style={{ width: '60px' }}>Photo</th>
                <th>Roll / Student ID</th>
                <th>Name</th>
                <th>Semester</th>
                <th>Section Name</th>
                <th>Face Registered</th>
                <th style={{ textAlign: 'center', width: '90px' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {students.length === 0 ? (
                <tr>
                  <td colSpan="7" style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-secondary)' }}>
                    No students found. Register students via the Register Student page.
                  </td>
                </tr>
              ) : (
                students.map((st) => {
                  const id = st.student_id || st.id;
                  const cls = classes.find((c) => (c.class_id || c.id) === st.class_id);
                  const semesterName = cls?.semester ? `Semester ${cls.semester}` : '-';
                  const sectionName = cls ? cls.class_name : (st.class_id ? `Section #${st.class_id}` : '-');
                  return (
                    <tr key={id}>
                      <td>
                        {st.face_image ? (
                          <img
                            src={st.face_image}
                            alt={st.student_name}
                            style={{
                              width: '40px',
                              height: '40px',
                              borderRadius: '50%',
                              objectFit: 'cover',
                              border: '2px solid var(--border-color)',
                            }}
                          />
                        ) : (
                          <div
                            style={{
                              width: '40px',
                              height: '40px',
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
                            {st.student_name ? st.student_name[0].toUpperCase() : 'S'}
                          </div>
                        )}
                      </td>
                      <td><strong>{id}</strong></td>
                      <td style={{ fontWeight: 600 }}>{st.student_name || st.name}</td>
                      <td>{semesterName}</td>
                      <td>{sectionName}</td>
                      <td>
                        <span className={st.face_registered ? 'badge badge-present' : 'badge badge-absent'}>
                          {st.face_registered ? 'Registered' : 'Not Registered'}
                        </span>
                      </td>
                      <td style={{ textAlign: 'center' }}>
                        <button
                          className="btn btn-secondary text-red"
                          onClick={() => handleDelete(id)}
                          style={{ padding: '0.3rem 0.65rem', fontSize: '0.8rem' }}
                        >
                          Delete
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
