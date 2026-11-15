// src/components/RecentActivityFeed.jsx
import React, { useState, useEffect } from 'react';
import {
  Activity,
  UserPlus,
  CheckCircle2,
  FileSpreadsheet,
  GraduationCap,
  Camera,
  ChevronRight,
  X,
  Clock,
} from 'lucide-react';
import { getRecentActivities } from '../services/dashboardService';

function timeAgo(dateString) {
  if (!dateString) return 'recently';
  const now = new Date();
  const past = new Date(dateString.replace(' ', 'T'));
  const diffSec = Math.floor((now - past) / 1000);
  if (isNaN(diffSec) || diffSec < 0) return 'just now';
  if (diffSec < 60) return `${diffSec}s ago`;
  const diffMin = Math.floor(diffSec / 60);
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffHours = Math.floor(diffMin / 60);
  if (diffHours < 24) return `${diffHours}h ago`;
  const diffDays = Math.floor(diffHours / 24);
  return `${diffDays}d ago`;
}

export default function RecentActivityFeed() {
  const [activities, setActivities] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [viewAllOpen, setViewAllOpen] = useState(false);
  const [modalActivities, setModalActivities] = useState([]);
  const [modalPage, setModalPage] = useState(1);
  const [modalLoading, setModalLoading] = useState(false);

  useEffect(() => {
    let isMounted = true;
    async function loadActivities() {
      try {
        const res = await getRecentActivities(3, 1);
        if (isMounted) {
          setActivities(res.activities || []);
          setTotalCount(res.total || 0);
        }
      } catch (err) {
        // Safe fallback
      } finally {
        if (isMounted) setLoading(false);
      }
    }
    loadActivities();
    return () => {
      isMounted = false;
    };
  }, []);

  const openViewAllModal = async () => {
    setViewAllOpen(true);
    setModalLoading(true);
    try {
      const res = await getRecentActivities(15, 1);
      setModalActivities(res.activities || []);
      setModalPage(1);
    } catch (e) {
      // Safe fallback
    } finally {
      setModalLoading(false);
    }
  };

  const loadMoreModal = async () => {
    setModalLoading(true);
    const nextPage = modalPage + 1;
    try {
      const res = await getRecentActivities(15, nextPage);
      setModalActivities((prev) => [...prev, ...(res.activities || [])]);
      setModalPage(nextPage);
    } catch (e) {
      // Safe fallback
    } finally {
      setModalLoading(false);
    }
  };

  const getActivityIcon = (type) => {
    switch (type) {
      case 'STUDENT_REGISTERED':
      case 'student':
        return <UserPlus size={14} className="text-purple" />;
      case 'ATTENDANCE_MARKED':
      case 'attendance':
        return <CheckCircle2 size={14} className="text-green" />;
      case 'EXAM_CREATED':
      case 'exam':
        return <FileSpreadsheet size={14} className="text-blue" />;
      case 'CLASS_CREATED':
      case 'class':
        return <GraduationCap size={14} className="text-amber" />;
      case 'SESSION_STARTED':
      case 'session':
        return <Camera size={14} className="text-cyan" />;
      default:
        return <Activity size={14} className="text-slate-500" />;
    }
  };

  return (
    <div className="card recent-activity-card compact-activity-card">
      <div className="card-header-with-action">
        <h4 className="compact-card-title">Recent Activity</h4>
        {totalCount > 0 && (
          <button className="view-all-btn" onClick={openViewAllModal}>
            View All ({totalCount}) <ChevronRight size={12} />
          </button>
        )}
      </div>

      <div className="activity-feed-body">
        {loading ? (
          <div className="activity-skeleton-list compact-skeleton-list" />
        ) : activities.length === 0 ? (
          <div className="activity-empty-state compact-empty">
            <p>No recent activity recorded.</p>
          </div>
        ) : (
          <div className="activity-timeline-list compact-timeline">
            {activities.map((act) => (
              <div key={act.id} className="activity-timeline-item compact-item">
                <div className="activity-icon-container compact-icon-box">
                  {getActivityIcon(act.activity_type)}
                </div>
                <div className="activity-item-details">
                  <p className="activity-item-description compact-desc">
                    {act.description}
                  </p>
                  <span className="activity-item-time compact-time">
                    <Clock size={11} /> {timeAgo(act.created_at)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* View All Modal */}
      {viewAllOpen && (
        <div className="modal-backdrop" onClick={() => setViewAllOpen(false)}>
          <div
            className="modal-content activity-modal"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="modal-header">
              <div className="modal-title-box">
                <Activity size={18} className="text-purple" />
                <h3>System Activity Audit Logs ({totalCount})</h3>
              </div>
              <button
                className="modal-close-btn"
                onClick={() => setViewAllOpen(false)}
                aria-label="Close modal"
              >
                <X size={18} />
              </button>
            </div>

            <div className="modal-body activity-modal-body">
              <div className="activity-timeline-list modal-list">
                {modalActivities.map((act) => (
                  <div key={act.id} className="activity-timeline-item">
                    <div className="activity-icon-container">
                      {getActivityIcon(act.activity_type)}
                    </div>
                    <div className="activity-item-details">
                      <p className="activity-item-description">
                        {act.description}
                      </p>
                      <div className="activity-meta-row">
                        <span className="activity-item-time">
                          <Clock size={12} /> {timeAgo(act.created_at)}
                        </span>
                        <span className="activity-exact-time">
                          {act.created_at}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {modalActivities.length < totalCount && (
                <div className="modal-load-more-wrapper">
                  <button
                    className="btn btn-secondary"
                    onClick={loadMoreModal}
                    disabled={modalLoading}
                  >
                    {modalLoading ? 'Loading more...' : 'Load More Logs'}
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
