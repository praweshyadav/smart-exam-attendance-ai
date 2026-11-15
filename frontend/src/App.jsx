// src/App.jsx
import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Sidebar from './components/Sidebar';
import TopNav from './components/TopNav';
import Loading from './components/Loading';
import Login from './pages/Login';
import Signup from './pages/Signup';
import Dashboard from './pages/Dashboard';
import RegisterStudent from './pages/RegisterStudent';
import TakeAttendance from './pages/TakeAttendance';
import ViewAttendance from './pages/ViewAttendance';
import AttendanceReport from './pages/AttendanceReport';
import CalendarPage from './pages/CalendarPage';
import Students from './pages/Students';
import Classes from './pages/Classes';
import Exams from './pages/Exams';
import AdminUsers from './pages/AdminUsers';

function AppRoutes({ theme, toggleTheme }) {
  const { isAuthenticated, isAdmin, authLoading } = useAuth();
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);

  useEffect(() => {
    if (mobileSidebarOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [mobileSidebarOpen]);

  if (authLoading) {
    return (
      <div
        style={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: 'var(--bg-color)',
        }}
      >
        <Loading />
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <Routes>
        <Route path="/login" element={<Login theme={theme} toggleTheme={toggleTheme} />} />
        <Route path="/signup" element={<Signup theme={theme} toggleTheme={toggleTheme} />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    );
  }

  const defaultHome = isAdmin ? '/' : '/view-attendance';

  return (
    <div className="app-layout">
      <Sidebar
        mobileOpen={mobileSidebarOpen}
        onCloseMobile={() => setMobileSidebarOpen(false)}
      />

      <div className="app-main-wrapper">
        <TopNav
          theme={theme}
          toggleTheme={toggleTheme}
          onToggleMobileSidebar={() => setMobileSidebarOpen((v) => !v)}
        />

        <main className="main-content-scroll">
          <Routes>
            {/* Public auth paths redirect home if already signed in */}
            <Route path="/login" element={<Navigate to={defaultHome} replace />} />
            <Route path="/signup" element={<Navigate to={defaultHome} replace />} />

            {/* Student & Admin View: Student has access to My Attendance only */}
            <Route path="/view-attendance" element={<ViewAttendance />} />
            <Route path="/my-attendance" element={<ViewAttendance />} />

            {/* Admin-only Routes */}
            <Route
              path="/"
              element={isAdmin ? <Dashboard /> : <Navigate to="/view-attendance" replace />}
            />
            <Route
              path="/register"
              element={isAdmin ? <RegisterStudent /> : <Navigate to="/view-attendance" replace />}
            />
            <Route
              path="/take-attendance"
              element={isAdmin ? <TakeAttendance /> : <Navigate to="/view-attendance" replace />}
            />
            <Route
              path="/attendance-report"
              element={isAdmin ? <AttendanceReport /> : <Navigate to="/view-attendance" replace />}
            />
            <Route
              path="/attendance-register"
              element={isAdmin ? <AttendanceReport /> : <Navigate to="/view-attendance" replace />}
            />
            <Route
              path="/reports"
              element={isAdmin ? <AttendanceReport /> : <Navigate to="/view-attendance" replace />}
            />
            <Route
              path="/calendar"
              element={isAdmin ? <CalendarPage /> : <Navigate to="/view-attendance" replace />}
            />
            <Route
              path="/students"
              element={isAdmin ? <Students /> : <Navigate to="/view-attendance" replace />}
            />
            <Route
              path="/classes"
              element={isAdmin ? <Classes /> : <Navigate to="/view-attendance" replace />}
            />
            <Route
              path="/exams"
              element={isAdmin ? <Exams /> : <Navigate to="/view-attendance" replace />}
            />
            <Route
              path="/admin-users"
              element={isAdmin ? <AdminUsers /> : <Navigate to="/view-attendance" replace />}
            />

            <Route path="*" element={<Navigate to={defaultHome} replace />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}

export default function App() {
  const [theme, setTheme] = useState(() => {
    const saved = localStorage.getItem('app_theme');
    return saved === 'dark' ? 'dark' : 'light';
  });

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('app_theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'light' ? 'dark' : 'light'));
  };

  return (
    <AuthProvider>
      <Router>
        <AppRoutes theme={theme} toggleTheme={toggleTheme} />
      </Router>
    </AuthProvider>
  );
}
