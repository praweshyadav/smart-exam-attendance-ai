// src/components/QuickActions.jsx
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { UserPlus, Camera, FileSpreadsheet } from 'lucide-react';

export default function QuickActions() {
  const navigate = useNavigate();

  const actions = [
    {
      title: 'Register Student',
      subtitle: 'Add student & face capture',
      path: '/register',
      icon: UserPlus,
      accent: '#0066cc',
      gradient: 'linear-gradient(135deg, rgba(0, 102, 204, 0.12) 0%, rgba(0, 75, 181, 0.04) 100%)',
    },
    {
      title: 'Take Attendance',
      subtitle: 'Open camera & mark attendance',
      path: '/take-attendance',
      icon: Camera,
      accent: '#2563EB',
      gradient: 'linear-gradient(135deg, rgba(37, 99, 235, 0.12) 0%, rgba(29, 78, 216, 0.04) 100%)',
    },
    {
      title: 'Attendance Report',
      subtitle: 'View date-wise attendance sheet',
      path: '/attendance-report',
      icon: FileSpreadsheet,
      accent: '#16C784',
      gradient: 'linear-gradient(135deg, rgba(22, 199, 132, 0.12) 0%, rgba(5, 150, 105, 0.04) 100%)',
    },
  ];

  return (
    <div className="card compact-actions-card">
      <div className="compact-section-header">
        <h4 className="compact-card-title">Quick Actions</h4>
      </div>

      <div className="compact-actions-grid">
        {actions.map((act) => {
          const Icon = act.icon;
          return (
            <div
              key={act.title}
              className="compact-action-btn"
              onClick={() => navigate(act.path)}
              style={{
                '--action-accent': act.accent,
                '--action-gradient': act.gradient,
              }}
            >
              <div
                className="compact-action-icon-box"
                style={{
                  color: act.accent,
                  backgroundColor: 'var(--hover-bg)',
                }}
              >
                <Icon size={16} />
              </div>
              <div className="compact-action-info">
                <div className="compact-action-title">{act.title}</div>
                <div className="compact-action-sub">{act.subtitle}</div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
