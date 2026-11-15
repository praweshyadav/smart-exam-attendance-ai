// src/pages/Exams.jsx
import React, { useEffect, useState } from 'react';
import Loading from '../components/Loading';
import ErrorMessage from '../components/ErrorMessage';
import { getExams, createExam, updateExam, deleteExam } from '../services/examService';
import { getClasses } from '../services/classService';

export default function Exams() {
  const [exams, setExams] = useState([]);
  const [classes, setClasses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [editingId, setEditingId] = useState(null);
  const [formData, setFormData] = useState({ exam_name: '', class_id: '', exam_date: '', start_time: '' });

  const loadData = async () => {
    try {
      const [exList, clsList] = await Promise.all([getExams(), getClasses()]);
      const fetchedExams = Array.isArray(exList) ? exList : (exList?.exams || []);
      const fetchedClasses = Array.isArray(clsList) ? clsList : (clsList?.classes || []);
      setExams(fetchedExams);
      setClasses(fetchedClasses);
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
      const payload = { ...formData, class_id: Number(formData.class_id) };
      if (editingId) {
        await updateExam(editingId, payload);
      } else {
        await createExam(payload);
      }
      setFormData({ exam_name: '', class_id: '', exam_date: '', start_time: '' });
      setEditingId(null);
      loadData();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleEdit = (ex) => {
    const id = ex.exam_id || ex.id;
    setEditingId(id);
    setFormData({
      exam_name: ex.exam_name || '',
      class_id: ex.class_id || '',
      exam_date: ex.exam_date || '',
      start_time: ex.start_time || '',
    });
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Delete exam?')) return;
    try {
      await deleteExam(id);
      loadData();
    } catch (err) {
      setError(err.message);
    }
  };

  if (loading) return <Loading />;

  return (
    <div style={{ maxWidth: '1100px', margin: '0 auto', width: '100%' }}>
      <h1 style={{ marginBottom: '0.5rem', fontSize: '1.4rem', fontWeight: 800 }}>Manage Exams</h1>
      <p style={{ color: 'var(--text-secondary)', marginBottom: '1.25rem', fontSize: '0.85rem' }}>
        Schedule examinations, assign classes, and set exam timings
      </p>

      <ErrorMessage message={error} />

      <form onSubmit={handleSubmit} className="card" style={{ maxWidth: '520px', marginBottom: '1.75rem', padding: '1.25rem' }}>
        <h3 style={{ fontSize: '1.05rem', fontWeight: 700, marginBottom: '0.85rem' }}>{editingId ? 'Edit Exam' : 'Add Exam'}</h3>
        <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>Exam Name</label>
        <input
          type="text"
          value={formData.exam_name}
          placeholder="e.g. Mid-Sem Examination"
          onChange={(e) => setFormData({ ...formData, exam_name: e.target.value })}
          required
          style={{ width: '100%', marginBottom: '0.75rem' }}
        />
        <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>Class / Section</label>
        <select
          value={formData.class_id}
          onChange={(e) => setFormData({ ...formData, class_id: e.target.value })}
          required
          style={{ width: '100%', marginBottom: '0.75rem' }}
        >
          <option value="">Select Class</option>
          {classes.map((c) => (
            <option key={c.class_id || c.id} value={c.class_id || c.id}>
              {c.class_name} {c.department ? `(${c.department})` : ''}
            </option>
          ))}
        </select>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', marginBottom: '1rem' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>Exam Date</label>
            <input
              type="date"
              value={formData.exam_date}
              onChange={(e) => setFormData({ ...formData, exam_date: e.target.value })}
              required
              style={{ width: '100%' }}
            />
          </div>
          <div>
            <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>Start Time (Optional)</label>
            <input
              type="time"
              value={formData.start_time}
              onChange={(e) => setFormData({ ...formData, start_time: e.target.value })}
              style={{ width: '100%' }}
            />
          </div>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button type="submit" className="btn" style={{ flex: 1 }}>
            {editingId ? 'Update Exam' : 'Add Exam'}
          </button>
          {editingId && (
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => {
                setEditingId(null);
                setFormData({ exam_name: '', class_id: '', exam_date: '', start_time: '' });
              }}
            >
              Cancel
            </button>
          )}
        </div>
      </form>

      <div className="card" style={{ padding: '1rem', width: '100%', overflow: 'hidden' }}>
        <div className="responsive-table-wrapper" style={{ overflowX: 'auto', WebkitOverflowScrolling: 'touch', width: '100%' }}>
          <table style={{ minWidth: '600px', borderCollapse: 'collapse', margin: 0 }}>
            <thead>
              <tr style={{ backgroundColor: 'var(--hover-bg)' }}>
                <th style={{ width: '50px' }}>ID</th>
                <th>Exam Name</th>
                <th>Semester / Class</th>
                <th>Exam Date</th>
                <th>Start Time</th>
                <th style={{ textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {exams.length === 0 ? (
                <tr>
                  <td colSpan={6} style={{ textAlign: 'center', padding: '2rem 1rem', color: 'var(--text-secondary)' }}>
                    No exams scheduled yet.
                  </td>
                </tr>
              ) : (
                exams.map((ex) => {
                  const id = ex.exam_id || ex.id;
                  const cls = classes.find((c) => (c.class_id || c.id) === ex.class_id);
                  const semDisplay = cls ? (cls.semester ? `Semester ${cls.semester} (${cls.class_name})` : cls.class_name) : `Class #${ex.class_id}`;
                  return (
                    <tr key={id}>
                      <td style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>{id}</td>
                      <td><strong>{ex.exam_name}</strong></td>
                      <td>{semDisplay}</td>
                      <td>{ex.exam_date}</td>
                      <td>{ex.start_time || '-'}</td>
                      <td style={{ textAlign: 'right' }}>
                        <div style={{ display: 'inline-flex', gap: '0.4rem' }}>
                          <button className="btn" onClick={() => handleEdit(ex)} style={{ fontSize: '0.75rem', padding: '0.3rem 0.65rem' }}>
                            Edit
                          </button>
                          <button className="btn text-red" onClick={() => handleDelete(id)} style={{ fontSize: '0.75rem', padding: '0.3rem 0.65rem' }}>
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
    </div>
  );
}
