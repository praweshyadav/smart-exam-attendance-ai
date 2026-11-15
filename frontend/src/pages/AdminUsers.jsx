// src/pages/AdminUsers.jsx
import React, { useEffect, useState } from 'react';
import { Shield, ShieldCheck, UserPlus, Trash2, Users, Settings, ChevronDown, ChevronUp, KeyRound, AtSign } from 'lucide-react';
import Loading from '../components/Loading';
import ErrorMessage from '../components/ErrorMessage';
import { useAuth } from '../context/AuthContext';
import {
  deleteUserAccount,
  getAllUsers,
  registerAdmin,
  updateMyPassword,
  updateMyUsername,
} from '../services/authService';

export default function AdminUsers() {
  const { user: currentUser, logout } = useAuth();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  // Account settings panel state
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [settingsTab, setSettingsTab] = useState('password'); // 'password' | 'username'
  const [pwForm, setPwForm] = useState({ current_password: '', new_password: '', confirm: '' });
  const [unForm, setUnForm] = useState({ new_username: '', password: '' });
  const [settingsMsg, setSettingsMsg] = useState('');
  const [settingsErr, setSettingsErr] = useState('');
  const [settingsSubmitting, setSettingsSubmitting] = useState(false);

  const [formData, setFormData] = useState({ username: '', full_name: '', password: '' });

  const loadUsers = async () => {
    try {
      const res = await getAllUsers();
      setUsers(Array.isArray(res?.users) ? res.users : []);
    } catch (err) {
      setError(err.message || 'Failed to load users.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadUsers(); }, []);

  const handleRegisterAdmin = async (e) => {
    e.preventDefault();
    setError(''); setSuccessMsg(''); setSubmitting(true);
    try {
      const res = await registerAdmin({
        username: formData.username.trim(),
        full_name: formData.full_name.trim(),
        password: formData.password,
      });
      setSuccessMsg(res?.message || 'Admin account registered successfully.');
      setFormData({ username: '', full_name: '', password: '' });
      await loadUsers();
    } catch (err) {
      setError(err.message || 'Failed to register admin.');
    } finally { setSubmitting(false); }
  };

  const handleDeleteUser = async (target) => {
    if (!window.confirm(`Delete user '${target.username}' (${target.role})?`)) return;
    setError(''); setSuccessMsg('');
    try {
      await deleteUserAccount(target.id);
      setSuccessMsg(`Deleted user '${target.username}'.`);
      await loadUsers();
    } catch (err) {
      setError(err.message || 'Failed to delete user.');
    }
  };

  const handleChangePassword = async (e) => {
    e.preventDefault();
    setSettingsErr(''); setSettingsMsg('');
    if (pwForm.new_password !== pwForm.confirm) {
      setSettingsErr('New passwords do not match.'); return;
    }
    if (pwForm.new_password.length < 6) {
      setSettingsErr('New password must be at least 6 characters.'); return;
    }
    setSettingsSubmitting(true);
    try {
      await updateMyPassword({ current_password: pwForm.current_password, new_password: pwForm.new_password });
      setSettingsMsg('Password updated successfully.');
      setPwForm({ current_password: '', new_password: '', confirm: '' });
    } catch (err) {
      setSettingsErr(err.message || 'Failed to update password.');
    } finally { setSettingsSubmitting(false); }
  };

  const handleChangeUsername = async (e) => {
    e.preventDefault();
    setSettingsErr(''); setSettingsMsg('');
    setSettingsSubmitting(true);
    try {
      await updateMyUsername({ new_username: unForm.new_username.trim(), password: unForm.password });
      setSettingsMsg('Username updated. You will be logged out now.');
      setUnForm({ new_username: '', password: '' });
      setTimeout(() => logout(), 1800);
    } catch (err) {
      setSettingsErr(err.message || 'Failed to update username.');
    } finally { setSettingsSubmitting(false); }
  };

  if (loading) return <Loading />;

  return (
    <div style={{ maxWidth: '1100px', margin: '0 auto', width: '100%' }}>
      <div style={{ marginBottom: '1.25rem', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '0.75rem' }}>
        <div>
          <h1 style={{ fontSize: '1.45rem', fontWeight: 800, margin: 0, color: 'var(--text-color)' }}>
            Admin & User Access Management
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginTop: '0.2rem' }}>
            Register administrators and manage accounts
          </p>
        </div>
        <button
          type="button"
          onClick={() => { setSettingsOpen(v => !v); setSettingsErr(''); setSettingsMsg(''); }}
          style={{
            display: 'inline-flex', alignItems: 'center', gap: '0.4rem',
            padding: '0.45rem 0.9rem', borderRadius: '8px', fontSize: '0.82rem', fontWeight: 600,
            border: '1px solid var(--border-color)', background: 'var(--hover-bg)',
            color: 'var(--text-secondary)', cursor: 'pointer',
          }}
        >
          <Settings size={14} /> Account Settings {settingsOpen ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
        </button>
      </div>

      {/* Account Settings Collapsible */}
      {settingsOpen && (
        <div className="card" style={{ marginBottom: '1.5rem', padding: '1.15rem 1.35rem' }}>
          <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
            {['password', 'username'].map(tab => (
              <button key={tab} type="button"
                onClick={() => { setSettingsTab(tab); setSettingsErr(''); setSettingsMsg(''); }}
                style={{
                  padding: '0.35rem 0.85rem', borderRadius: '6px', fontSize: '0.8rem', fontWeight: 600, cursor: 'pointer',
                  border: 'none',
                  background: settingsTab === tab ? 'var(--primary-purple)' : 'var(--hover-bg)',
                  color: settingsTab === tab ? '#fff' : 'var(--text-secondary)',
                  display: 'inline-flex', alignItems: 'center', gap: '0.3rem',
                }}
              >
                {tab === 'password' ? <><KeyRound size={12} /> Change Password</> : <><AtSign size={12} /> Change Username</>}
              </button>
            ))}
          </div>

          {settingsErr && <div style={{ padding: '0.5rem 0.75rem', borderRadius: '6px', backgroundColor: 'var(--badge-absent-bg)', color: 'var(--badge-absent-text)', fontSize: '0.82rem', marginBottom: '0.75rem', border: '1px solid var(--status-red)' }}>{settingsErr}</div>}
          {settingsMsg && <div style={{ padding: '0.5rem 0.75rem', borderRadius: '6px', backgroundColor: 'var(--badge-present-bg)', color: 'var(--badge-present-text)', fontSize: '0.82rem', marginBottom: '0.75rem', border: '1px solid var(--status-green)' }}>{settingsMsg}</div>}

          {settingsTab === 'password' ? (
            <form onSubmit={handleChangePassword} style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '0.75rem', alignItems: 'end' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.74rem', fontWeight: 700, color: 'var(--text-secondary)', marginBottom: '0.2rem' }}>Current Password</label>
                <input type="password" value={pwForm.current_password} onChange={e => setPwForm(p => ({ ...p, current_password: e.target.value }))} required style={{ margin: 0, height: '36px', fontSize: '0.85rem' }} placeholder="Current password" />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '0.74rem', fontWeight: 700, color: 'var(--text-secondary)', marginBottom: '0.2rem' }}>New Password</label>
                <input type="password" value={pwForm.new_password} onChange={e => setPwForm(p => ({ ...p, new_password: e.target.value }))} required minLength={6} style={{ margin: 0, height: '36px', fontSize: '0.85rem' }} placeholder="Min 6 characters" />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '0.74rem', fontWeight: 700, color: 'var(--text-secondary)', marginBottom: '0.2rem' }}>Confirm New Password</label>
                <input type="password" value={pwForm.confirm} onChange={e => setPwForm(p => ({ ...p, confirm: e.target.value }))} required style={{ margin: 0, height: '36px', fontSize: '0.85rem' }} placeholder="Repeat new password" />
              </div>
              <div>
                <button type="submit" className="btn" disabled={settingsSubmitting} style={{ height: '36px', padding: '0 1rem', fontSize: '0.82rem', width: '100%' }}>
                  {settingsSubmitting ? 'Updating...' : 'Update Password'}
                </button>
              </div>
            </form>
          ) : (
            <form onSubmit={handleChangeUsername} style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '0.75rem', alignItems: 'end' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.74rem', fontWeight: 700, color: 'var(--text-secondary)', marginBottom: '0.2rem' }}>New Username</label>
                <input type="text" value={unForm.new_username} onChange={e => setUnForm(p => ({ ...p, new_username: e.target.value }))} required style={{ margin: 0, height: '36px', fontSize: '0.85rem' }} placeholder="Unique username" />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '0.74rem', fontWeight: 700, color: 'var(--text-secondary)', marginBottom: '0.2rem' }}>Confirm with Password</label>
                <input type="password" value={unForm.password} onChange={e => setUnForm(p => ({ ...p, password: e.target.value }))} required style={{ margin: 0, height: '36px', fontSize: '0.85rem' }} placeholder="Your password" />
              </div>
              <div>
                <button type="submit" className="btn" disabled={settingsSubmitting} style={{ height: '36px', padding: '0 1rem', fontSize: '0.82rem', width: '100%' }}>
                  {settingsSubmitting ? 'Updating...' : 'Update Username'}
                </button>
              </div>
            </form>
          )}
        </div>
      )}

      <ErrorMessage message={error} />
      {successMsg && (
        <div style={{ padding: '0.75rem 1rem', borderRadius: '8px', backgroundColor: 'var(--badge-present-bg)', color: 'var(--badge-present-text)', border: '1px solid var(--status-green)', marginBottom: '1rem', fontWeight: 600, fontSize: '0.88rem' }}>
          {successMsg}
        </div>
      )}

      {/* Register New Admin Card */}
      <form onSubmit={handleRegisterAdmin} className="card" style={{ maxWidth: '540px', marginBottom: '1.75rem', padding: '1.35rem 1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
          <UserPlus size={18} style={{ color: 'var(--primary-purple)' }} />
          <h3 style={{ fontSize: '1.05rem', fontWeight: 700, margin: 0 }}>Register New Administrator</h3>
        </div>
        <div style={{ marginBottom: '0.85rem' }}>
          <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>Admin Username</label>
          <input type="text" placeholder="e.g. exam_admin1" value={formData.username} onChange={e => setFormData({ ...formData, username: e.target.value })} required style={{ width: '100%', margin: 0 }} />
        </div>
        <div style={{ marginBottom: '0.85rem' }}>
          <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>Full Name</label>
          <input type="text" placeholder="e.g. Prof. Sharma" value={formData.full_name} onChange={e => setFormData({ ...formData, full_name: e.target.value })} required style={{ width: '100%', margin: 0 }} />
        </div>
        <div style={{ marginBottom: '1.1rem' }}>
          <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>Password (min 6 characters)</label>
          <input type="password" placeholder="Enter strong password" value={formData.password} onChange={e => setFormData({ ...formData, password: e.target.value })} required minLength={6} style={{ width: '100%', margin: 0 }} />
        </div>
        <button type="submit" className="btn" disabled={submitting} style={{ width: '100%' }}>
          {submitting ? 'Registering Admin...' : 'Register Admin Account'}
        </button>
      </form>

      {/* Users Table */}
      <div className="card" style={{ padding: '1.25rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.9rem' }}>
          <Users size={18} style={{ color: 'var(--primary-purple)' }} />
          <h3 style={{ fontSize: '1.05rem', fontWeight: 700, margin: 0 }}>Registered Accounts ({users.length})</h3>
        </div>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', minWidth: '640px', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ backgroundColor: 'var(--hover-bg)' }}>
                <th>Username / Roll No.</th>
                <th>Full Name</th>
                <th>Role</th>
                <th>Created By</th>
                <th style={{ textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map(u => {
                const isSelf = currentUser && u.id === currentUser.id;
                const isSysAdmin = Boolean(u.is_system_admin);
                return (
                  <tr key={u.id}>
                    <td>
                      <strong>{u.username}</strong>
                      {isSelf && <span style={{ marginLeft: '0.4rem', fontSize: '0.7rem', padding: '0.1rem 0.4rem', borderRadius: '6px', backgroundColor: 'var(--badge-info-bg)', color: 'var(--badge-info-text)', fontWeight: 700 }}>You</span>}
                    </td>
                    <td>{u.full_name}</td>
                    <td>
                      {isSysAdmin ? (
                        <span className="badge badge-info" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}><ShieldCheck size={12} /> System Admin</span>
                      ) : u.role === 'admin' ? (
                        <span className="badge badge-present" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}><Shield size={12} /> Admin</span>
                      ) : (
                        <span className="badge" style={{ backgroundColor: 'var(--hover-bg)', color: 'var(--text-secondary)' }}>Student</span>
                      )}
                    </td>
                    <td style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>{u.created_by || 'self'}</td>
                    <td style={{ textAlign: 'right' }}>
                      {isSysAdmin || isSelf ? (
                        <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>{isSysAdmin ? 'Protected' : 'Active'}</span>
                      ) : (
                        <button type="button" className="btn btn-secondary text-red" onClick={() => handleDeleteUser(u)} style={{ padding: '0.3rem 0.65rem', fontSize: '0.78rem', display: 'inline-flex', alignItems: 'center', gap: '0.3rem' }}>
                          <Trash2 size={13} /> Delete
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
