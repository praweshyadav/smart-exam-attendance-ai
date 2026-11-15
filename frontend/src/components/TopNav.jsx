// src/components/TopNav.jsx
import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Search,
  Moon,
  Sun,
  Bell,
  CheckCircle2,
  AlertCircle,
  Info,
  AlertTriangle,
  Menu,
  User,
  Shield,
  Settings,
  LogOut,
} from 'lucide-react';
import {
  getNotifications,
  markNotificationRead,
  markAllNotificationsRead,
  searchRecords,
} from '../services/dashboardService';
import { useAuth } from '../context/AuthContext';

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

export default function TopNav({ theme, toggleTheme, onToggleMobileSidebar }) {
  const navigate = useNavigate();
  const { user, isAdmin, logout } = useAuth();

  // Search state (admin only)
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState(null);
  const [isSearching, setIsSearching] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const searchInputRef = useRef(null);
  const searchDropdownRef = useRef(null);

  // Notifications state (admin only)
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [notifOpen, setNotifOpen] = useState(false);
  const notifDropdownRef = useRef(null);

  // Profile menu state
  const [profileOpen, setProfileOpen] = useState(false);
  const profileDropdownRef = useRef(null);

  const displayName = user?.full_name || user?.username || 'User';
  const displayRole = isAdmin
    ? user?.is_system_admin
      ? 'System Administrator'
      : 'Administrator'
    : `Student • Roll: ${user?.username || ''}`;

  // Load notifications only for Admins
  useEffect(() => {
    if (!isAdmin) return;
    async function loadNotifications() {
      try {
        const notifRes = await getNotifications();
        if (notifRes?.notifications) {
          setNotifications(notifRes.notifications);
          setUnreadCount(notifRes.unread_count || 0);
        }
      } catch {
        // Safe fallback
      }
    }
    loadNotifications();
  }, [isAdmin]);

  // Global Ctrl + K listener (Admin only)
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (isAdmin && (e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        searchInputRef.current?.focus();
        setSearchOpen(true);
      } else if (e.key === 'Escape') {
        setSearchOpen(false);
        setNotifOpen(false);
        setProfileOpen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isAdmin]);

  // Debounced search (Admin only)
  useEffect(() => {
    if (!isAdmin || !searchQuery.trim() || searchQuery.trim().length < 2) {
      setSearchResults(null);
      setIsSearching(false);
      return;
    }

    setIsSearching(true);
    const timer = setTimeout(async () => {
      try {
        const res = await searchRecords(searchQuery);
        setSearchResults(res);
      } catch {
        setSearchResults(null);
      } finally {
        setIsSearching(false);
      }
    }, 250);

    return () => clearTimeout(timer);
  }, [searchQuery, isAdmin]);

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (
        searchDropdownRef.current &&
        !searchDropdownRef.current.contains(e.target) &&
        !searchInputRef.current?.contains(e.target)
      ) {
        setSearchOpen(false);
      }
      if (notifDropdownRef.current && !notifDropdownRef.current.contains(e.target)) {
        setNotifOpen(false);
      }
      if (profileDropdownRef.current && !profileDropdownRef.current.contains(e.target)) {
        setProfileOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleMarkAllRead = async () => {
    try {
      await markAllNotificationsRead();
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: 1 })));
      setUnreadCount(0);
    } catch {
      // Safe ignore
    }
  };

  const handleNotificationClick = async (notif) => {
    if (!notif.is_read) {
      try {
        await markNotificationRead(notif.id);
        setNotifications((prev) =>
          prev.map((n) => (n.id === notif.id ? { ...n, is_read: 1 } : n))
        );
        setUnreadCount((c) => Math.max(0, c - 1));
      } catch {
        // Safe ignore
      }
    }
  };

  const handleSearchResultClick = (type) => {
    setSearchOpen(false);
    setSearchQuery('');
    if (type === 'student') navigate('/students');
    else if (type === 'class') navigate('/classes');
    else if (type === 'exam') navigate('/exams');
  };

  const handleLogout = async () => {
    setProfileOpen(false);
    await logout();
    navigate('/login', { replace: true });
  };

  const getNotifIcon = (type) => {
    switch (type) {
      case 'success':
        return <CheckCircle2 size={16} className="text-emerald-500" />;
      case 'warning':
        return <AlertTriangle size={16} className="text-amber-500" />;
      case 'error':
        return <AlertCircle size={16} className="text-rose-500" />;
      default:
        return <Info size={16} className="text-purple-500" />;
    }
  };

  const hasResults =
    searchResults &&
    (searchResults.students?.length > 0 ||
      searchResults.classes?.length > 0 ||
      searchResults.exams?.length > 0);

  return (
    <header className="top-navbar">
      <div className="top-navbar-left">
        <button
          className="mobile-sidebar-toggle"
          onClick={onToggleMobileSidebar}
          aria-label="Toggle navigation"
        >
          <Menu size={20} />
        </button>

        {isAdmin ? (
          <div className="global-search-container">
            <div className="search-input-wrapper">
              <Search size={17} className="search-icon" />
              <input
                ref={searchInputRef}
                type="text"
                placeholder="Search students, classes, exams..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onFocus={() => setSearchOpen(true)}
                className="global-search-input"
              />
              <div className="shortcut-badge">
                <kbd>Ctrl</kbd> <kbd>K</kbd>
              </div>
            </div>

            {searchOpen && searchQuery.trim().length >= 2 && (
              <div ref={searchDropdownRef} className="search-results-dropdown">
                {isSearching ? (
                  <div className="search-dropdown-loading">Searching records...</div>
                ) : hasResults ? (
                  <div className="search-dropdown-sections">
                    {searchResults.students?.length > 0 && (
                      <div className="search-group">
                        <div className="search-group-title">Students</div>
                        {searchResults.students.map((st) => (
                          <div
                            key={st.student_id}
                            className="search-item"
                            onClick={() => handleSearchResultClick('student')}
                          >
                            <div className="search-item-info">
                              <span className="search-item-primary">{st.student_name}</span>
                              <span className="search-item-secondary">
                                ID: {st.student_id} {st.class_name ? `• ${st.class_name}` : ''}
                              </span>
                            </div>
                            <span className="search-item-badge">Student</span>
                          </div>
                        ))}
                      </div>
                    )}

                    {searchResults.classes?.length > 0 && (
                      <div className="search-group">
                        <div className="search-group-title">Classes</div>
                        {searchResults.classes.map((c) => (
                          <div
                            key={c.class_id}
                            className="search-item"
                            onClick={() => handleSearchResultClick('class')}
                          >
                            <div className="search-item-info">
                              <span className="search-item-primary">{c.class_name}</span>
                              <span className="search-item-secondary">
                                {c.department ? `${c.department} • ` : ''}Sem {c.semester || 'N/A'}
                              </span>
                            </div>
                            <span className="search-item-badge">Class</span>
                          </div>
                        ))}
                      </div>
                    )}

                    {searchResults.exams?.length > 0 && (
                      <div className="search-group">
                        <div className="search-group-title">Exams &amp; Sessions</div>
                        {searchResults.exams.map((ex) => (
                          <div
                            key={ex.exam_id}
                            className="search-item"
                            onClick={() => handleSearchResultClick('exam')}
                          >
                            <div className="search-item-info">
                              <span className="search-item-primary">{ex.exam_name}</span>
                              <span className="search-item-secondary">Date: {ex.exam_date}</span>
                            </div>
                            <span className="search-item-badge">Exam</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="search-dropdown-empty">
                    No records matching &quot;{searchQuery}&quot;
                  </div>
                )}
              </div>
            )}
          </div>
        ) : (
          <div style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--text-color)' }}>
            Student Self-Service Portal
          </div>
        )}
      </div>

      <div className="top-navbar-right">
        <button
          className="top-icon-btn theme-toggle"
          onClick={toggleTheme}
          aria-label="Toggle color theme"
          title={`Switch to ${theme === 'light' ? 'Dark' : 'Light'} Mode`}
        >
          {theme === 'light' ? <Moon size={19} /> : <Sun size={19} />}
        </button>

        {isAdmin && (
          <div className="notif-wrapper" ref={notifDropdownRef}>
            <button
              className={`top-icon-btn notif-btn ${notifOpen ? 'active' : ''}`}
              onClick={() => setNotifOpen(!notifOpen)}
              aria-label="View notifications"
            >
              <Bell size={19} />
              {unreadCount > 0 && (
                <span className="notif-badge">{unreadCount > 9 ? '9+' : unreadCount}</span>
              )}
            </button>

            {notifOpen && (
              <div className="notif-dropdown">
                <div className="notif-dropdown-header">
                  <div className="notif-header-title">
                    <h4>Notifications</h4>
                    {unreadCount > 0 && (
                      <span className="notif-count-tag">{unreadCount} new</span>
                    )}
                  </div>
                  {unreadCount > 0 && (
                    <button className="notif-mark-all" onClick={handleMarkAllRead}>
                      Mark all as read
                    </button>
                  )}
                </div>

                <div className="notif-list">
                  {notifications.length === 0 ? (
                    <div className="notif-empty">No notifications</div>
                  ) : (
                    notifications.map((n) => (
                      <div
                        key={n.id}
                        className={`notif-card ${!n.is_read ? 'unread' : ''}`}
                        onClick={() => handleNotificationClick(n)}
                      >
                        <div className="notif-card-icon">{getNotifIcon(n.type)}</div>
                        <div className="notif-card-content">
                          <div className="notif-card-title">{n.title}</div>
                          <div className="notif-card-desc">{n.message}</div>
                          <div className="notif-card-time">{timeAgo(n.created_at)}</div>
                        </div>
                        {!n.is_read && <div className="notif-unread-dot" />}
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {/* User Profile Area */}
        <div className="admin-profile-wrapper" ref={profileDropdownRef}>
          <div
            className="admin-profile-trigger"
            onClick={() => setProfileOpen(!profileOpen)}
          >
            <div className="admin-avatar">
              <span>{displayName ? displayName[0].toUpperCase() : 'U'}</span>
            </div>
            <div className="admin-meta">
              <span className="admin-name">{displayName}</span>
              <span className="admin-role">{displayRole}</span>
            </div>
          </div>

          {profileOpen && (
            <div className="profile-dropdown">
              <div className="profile-dropdown-header">
                <div className="profile-dropdown-name">{displayName}</div>
                <div className="profile-dropdown-email">
                  {isAdmin ? `Username: ${user?.username}` : `Roll No: ${user?.username}`}
                </div>
                <div className="profile-dropdown-role">
                  <Shield size={12} /> {displayRole}
                </div>
              </div>
              <div className="profile-dropdown-divider" />
              {isAdmin ? (
                <>
                  <button
                    className="profile-dropdown-item"
                    onClick={() => {
                      setProfileOpen(false);
                      navigate('/view-attendance');
                    }}
                  >
                    <User size={15} /> Student Records
                  </button>
                  <button
                    className="profile-dropdown-item"
                    onClick={() => {
                      setProfileOpen(false);
                      navigate('/admin-users');
                    }}
                  >
                    <Settings size={15} /> Admin &amp; Users
                  </button>
                </>
              ) : (
                <button
                  className="profile-dropdown-item"
                  onClick={() => {
                    setProfileOpen(false);
                    navigate('/view-attendance');
                  }}
                >
                  <User size={15} /> My Attendance
                </button>
              )}
              <div className="profile-dropdown-divider" />
              <button
                className="profile-dropdown-item"
                style={{ color: 'var(--status-red)', fontWeight: 700 }}
                onClick={handleLogout}
              >
                <LogOut size={15} /> Logout
              </button>
            </div>
          )}
        </div>

        {/* Direct Logout Button */}
        <button
          type="button"
          onClick={handleLogout}
          className="btn btn-secondary"
          title="Logout"
          style={{
            padding: '0.4rem 0.75rem',
            fontSize: '0.8rem',
            fontWeight: 600,
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.35rem',
            color: 'var(--status-red)',
          }}
        >
          <LogOut size={15} /> Logout
        </button>
      </div>
    </header>
  );
}
