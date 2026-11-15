// src/pages/Dashboard.jsx
import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Users, GraduationCap, FileSpreadsheet, CheckCircle2 } from 'lucide-react';
import DashboardHeader from '../components/DashboardHeader';
import StatCard from '../components/StatCard';
import AttendanceTrendChart from '../components/AttendanceTrendChart';
import TodayAttendanceCard from '../components/TodayAttendanceCard';
import QuickActions from '../components/QuickActions';
import RecentActivityFeed from '../components/RecentActivityFeed';
import ErrorMessage from '../components/ErrorMessage';
import { getDashboardSummary } from '../services/dashboardService';

export default function Dashboard() {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    let isMounted = true;
    async function loadDashboard() {
      try {
        const res = await getDashboardSummary();
        if (isMounted) setSummary(res);
      } catch (err) {
        if (isMounted) setError(err.message || 'Failed to load dashboard summary.');
      } finally {
        if (isMounted) setLoading(false);
      }
    }
    loadDashboard();
    return () => { isMounted = false; };
  }, []);

  return (
    <div className="dashboard-page-container single-screen-layout">
      <DashboardHeader adminName={summary?.admin?.name || 'Admin'} />
      <ErrorMessage message={error} />

      <div className="stat-cards-row compact-stat-row">
        <StatCard
          title="TOTAL STUDENTS"
          value={summary?.totalStudents}
          subtitle="Registered in system"
          icon={Users}
          accentColor="#0066cc"
          loading={loading}
          onClick={() => navigate('/students')}
        />
        <StatCard
          title="TOTAL CLASSES"
          value={summary?.totalClasses}
          subtitle="Across departments"
          icon={GraduationCap}
          accentColor="#2563EB"
          loading={loading}
          onClick={() => navigate('/classes')}
        />
        <StatCard
          title="TOTAL EXAMS"
          value={summary?.totalExams}
          subtitle="Scheduled & conducted"
          icon={FileSpreadsheet}
          accentColor="#F59E0B"
          loading={loading}
          onClick={() => navigate('/exams')}
        />
        <StatCard
          title="ATTENDANCE RATE"
          value={summary ? `${summary.attendanceRate}%` : '0%'}
          subtitle="Overall attendance"
          icon={CheckCircle2}
          accentColor="#16C784"
          loading={loading}
          onClick={() => navigate('/view-attendance')}
        />
      </div>

      <div className="dashboard-grid-middle compact-middle-grid">
        <div className="grid-col-chart"><AttendanceTrendChart /></div>
        <div className="grid-col-today"><TodayAttendanceCard /></div>
      </div>

      <div className="dashboard-grid-bottom-compact">
        <div className="grid-col-actions"><QuickActions /></div>
        <div className="grid-col-activity"><RecentActivityFeed /></div>
      </div>
    </div>
  );
}
