// src/components/Sidebar.jsx
import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  UserPlus,
  Camera,
  CalendarCheck,
  FileSpreadsheet,
  Calendar,
  Users,
  GraduationCap,
  Sparkles,
  ShieldCheck,
  LogOut,
  X,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function Sidebar({ mobileOpen, onCloseMobile }) {
  const { user, isAdmin, logout } = useAuth();
  const navigate = useNavigate();

  const handleNavClick = () => {
    if (onCloseMobile) onCloseMobile();
  };

  const handleLogout = async () => {
    if (onCloseMobile) onCloseMobile();
    await logout();
    navigate('/login', { replace: true });
  };

  return (
    <>
      {mobileOpen && (
        <div className="sidebar-backdrop" onClick={onCloseMobile} />
      )}

      <aside className={`navy-sidebar ${mobileOpen ? 'mobile-open' : ''}`}>
        <div>
          <div className="sidebar-header">
            <div className="brand-badge-container">
              <div className="brand-icon-box">
                <Sparkles size={18} className="brand-sparkle-icon" />
              </div>
              <div className="brand-info">
                <h1 className="brand-title">Smart Attendance</h1>
                <p className="brand-subtitle">
                  {isAdmin ? 'Admin Console' : 'Student Portal'}
                </p>
              </div>
            </div>
            {mobileOpen && (
              <button
                className="mobile-close-btn"
                onClick={onCloseMobile}
                aria-label="Close sidebar"
              >
                <X size={18} />
              </button>
            )}
          </div>

          <div className="sidebar-nav-container">
            {isAdmin ? (
              <>
                <nav className="nav-list">
                  <NavLink
                    to="/"
                    end
                    className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}
                    onClick={handleNavClick}
                  >
                    <LayoutDashboard size={17} className="nav-icon" />
                    <span className="nav-text">Dashboard</span>
                  </NavLink>

                  <NavLink
                    to="/register"
                    className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}
                    onClick={handleNavClick}
                  >
                    <UserPlus size={17} className="nav-icon" />
                    <span className="nav-text">Register Student</span>
                  </NavLink>

                  <NavLink
                    to="/take-attendance"
                    className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}
                    onClick={handleNavClick}
                  >
                    <Camera size={17} className="nav-icon" />
                    <span className="nav-text">Take Attendance</span>
                  </NavLink>

                  <NavLink
                    to="/view-attendance"
                    className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}
                    onClick={handleNavClick}
                  >
                    <CalendarCheck size={17} className="nav-icon" />
                    <span className="nav-text">View Attendance</span>
                  </NavLink>

                  <NavLink
                    to="/attendance-report"
                    className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}
                    onClick={handleNavClick}
                  >
                    <FileSpreadsheet size={17} className="nav-icon" />
                    <span className="nav-text">Attendance Report</span>
                  </NavLink>

                  <NavLink
                    to="/calendar"
                    className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}
                    onClick={handleNavClick}
                  >
                    <Calendar size={17} className="nav-icon" />
                    <span className="nav-text">Calendar View</span>
                  </NavLink>
                </nav>

                <div className="sidebar-divider" />

                <nav className="nav-list">
                  <NavLink
                    to="/students"
                    className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}
                    onClick={handleNavClick}
                  >
                    <Users size={17} className="nav-icon" />
                    <span className="nav-text">Students</span>
                  </NavLink>

                  <NavLink
                    to="/classes"
                    className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}
                    onClick={handleNavClick}
                  >
                    <GraduationCap size={17} className="nav-icon" />
                    <span className="nav-text">Classes</span>
                  </NavLink>

                  <NavLink
                    to="/exams"
                    className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}
                    onClick={handleNavClick}
                  >
                    <FileSpreadsheet size={17} className="nav-icon" />
                    <span className="nav-text">Exams</span>
                  </NavLink>

                  <NavLink
                    to="/admin-users"
                    className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}
                    onClick={handleNavClick}
                  >
                    <ShieldCheck size={17} className="nav-icon" />
                    <span className="nav-text">Admin &amp; Users</span>
                  </NavLink>
                </nav>
              </>
            ) : (
              <nav className="nav-list">
                <NavLink
                  to="/view-attendance"
                  className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}
                  onClick={handleNavClick}
                >
                  <CalendarCheck size={17} className="nav-icon" />
                  <span className="nav-text">My Attendance</span>
                </NavLink>
              </nav>
            )}
          </div>
        </div>

        {/* Sidebar Footer: Active Identity & Logout */}
        <div
          style={{
            paddingTop: '0.85rem',
            borderTop: '1px solid var(--sidebar-border)',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.5rem',
          }}
        >
          {user && (
            <div style={{ padding: '0 0.4rem', fontSize: '0.78rem', color: 'var(--sidebar-muted)' }}>
              <div style={{ fontWeight: 700, color: 'var(--sidebar-text)' }}>
                {user.full_name}
              </div>
              <div>
                {isAdmin ? `@${user.username}` : `Roll No: ${user.username}`}
              </div>
            </div>
          )}

          <button
            type="button"
            onClick={handleLogout}
            className="sidebar-link"
            style={{
              width: '100%',
              border: 'none',
              background: 'transparent',
              color: 'var(--status-red)',
              cursor: 'pointer',
              textAlign: 'left',
            }}
          >
            <LogOut size={17} className="nav-icon" />
            <span className="nav-text">Logout</span>
          </button>
        </div>
      </aside>
    </>
  );
}
